## Core Functionality - Agent Logic and LLM Interaction (`app/agent.py`)

The `app/agent.py` file is the brain of the `amazon-agent`, orchestrating the interaction with the Large Language Model (LLM), managing the conversation flow, and coordinating the execution of browser-based tools.

### OpenAI Client Initialization

At the beginning of its operation, specifically within the main `prompt` function, an asynchronous OpenAI client is initialized:

```python
llm = openai.AsyncClient(
    base_url=os.getenv("LLM_BASE_URL", "http://localmodel:65534/v1"),
    api_key=os.getenv("LLM_API_KEY", "no-need"),
    max_retries=3
)
```
This client is configured using environment variables for the `LLM_BASE_URL` and `LLM_API_KEY`, allowing flexibility in connecting to different OpenAI-compatible LLM providers. `max_retries=3` enables resilience against transient network issues.

### System Prompt

The agent's behavior is guided by a system prompt. This prompt is fetched using the `get_system_prompt()` utility function (from `app/utils.py`), which typically reads the content of `system_prompt.txt`. The system prompt provides the LLM with its persona, instructions on how to behave, what tools it has access to, and how to interpret user requests in the context of e-commerce tasks on Amazon.

### Main `prompt` Function

The asynchronous generator function `prompt(messages: list[dict[str, str]], browser_context: BrowserContext, **_)` is the primary entry point for handling user interactions.

1.  **Inputs**: It takes the current `messages` (chat history) and the active `browser_context` (the Playwright browser instance) as key inputs.

2.  **Initial Page Check**: Before any LLM interaction, it checks if the current browser page is on the `AMAZON_URL` (defined in `app/config.py`). If not, it navigates the browser to this URL.
    ```python
    page = await browser_context.get_current_page()
    current_url = page.url
    if not current_url.startswith(AMAZON_URL):
        await page.goto(AMAZON_URL)
        # ...
    ```

3.  **Chat History Refinement**: The incoming `messages` are processed by `refine_chat_history` (from `app/utils.py`). This utility likely ensures the chat history is in the correct format, and crucially, it prepends the system prompt to the message list to set the context for the LLM.

4.  **LLM Interaction and Tool Calling Loop**:
    *   **Initial LLM Call**: The agent makes its first call to the LLM using `llm.chat.completions.create`. This request includes the refined `messages` and a list of available `functions` (tools, obtained from `app/tools.py` via `get_functions()`) that the LLM can request to use. `tool_choice="auto"` allows the LLM to decide whether to respond directly or request a tool call.
        ```python
        completion = await llm.chat.completions.create(
            model=os.getenv("LLM_MODEL_ID", 'local-llm'),
            messages=messages,
            tools=functions,
            tool_choice="auto",
            # ... other parameters like seed, temperature
        )
        ```
    *   **Direct Response**: If the LLM provides a direct textual response (`completion.choices[0].message.content`), this content is yielded, effectively streaming it back to the client. The assistant's message is then appended to the `messages` history.

    *   **Tool Call Handling Loop**: If the LLM's response includes `tool_calls`, the agent enters a loop to process them:
        *   **Iterate Tool Calls**: It iterates through each tool call requested by the LLM.
        *   **Agent Type Determination**: `get_agent_for_tool(tool_name)` determines if the requested tool belongs to the "shopping_browsing" agent or the "purchase_management" agent. This allows for context-specific behavior or instructions.
        *   **Agent Handoff Logic**: If the agent type determined for the current tool differs from the `previous_agent` type, a new system message is appended to the `messages` list. This message explicitly re-orients the LLM to its new role (e.g., "You are a purchase management agent..."). This helps the LLM maintain context when switching between different sets of tasks.
        *   **Skip Duplicate/Failed Execution**: The agent checks if a tool call with the exact same name and arguments has already been executed in the current turn (`identity in executed`) or if a prior tool call in the current sequence of calls resulted in an exception (`has_exception`). If so, it skips re-executing to prevent loops or repeated errors.
        *   **Tool Execution**:
            1.  A "request" message for the tool call is yielded to the stream (using `wrap_toolcall_request` for formatting).
            2.  `execute_openai_compatible_toolcall` is called. This function acts as a dispatcher, taking the tool name, arguments, browser context, and agent type. It maps the tool name to its actual Python implementation found in `app/tool_impl.py` (e.g., `search_products`, `add_to_cart`) and executes it.
            3.  The tool implementations in `tool_impl.py` perform the browser automation actions using the provided `browser_context`. These functions can also be asynchronous generators, yielding intermediate results or observations.
            4.  These intermediate results (and the final result) from the tool execution are wrapped (using `wrap_toolcall_response`) and yielded to the client stream, providing real-time feedback on the tool's progress.
            5.  The consolidated result from the tool is captured.
        *   **Append Tool Result**: The result of the tool execution is then formatted as a "tool" role message and appended to the `messages` list.
        *   **Next LLM Call**: After processing all tool calls in a given LLM response, the agent makes another call to `llm.chat.completions.create` with the updated `messages` history. This allows the LLM to process the tool results and decide on the next step (another tool call or a final textual response). The `tools` and `tool_choice` parameters are conditionally included; they are omitted if a maximum number of tool calls (e.g., 10) has been reached or if an exception occurred during tool execution, to prevent runaway loops.
        *   The loop continues until the LLM responds with content instead of more tool calls, or a limiting condition is met.

5.  **Error Handling**: The entire LLM interaction and tool calling process is wrapped in `try...except...finally` blocks. This allows the agent to catch various errors (e.g., `openai.APIConnectionError`, `httpx.HTTPStatusError`, generic `Exception`) that might occur during communication with the LLM or during tool execution. Error messages are logged and also yielded back to the client stream in a structured format.

### Helper Functions for Formatting

Throughout `app/agent.py`, several utility functions (likely imported from `app/utils.py`) are used to format messages for consistency and for the streaming protocol:
*   `refine_assistant_message`: Ensures the assistant's messages are correctly structured.
*   `to_chunk_data`: Encodes streamable data into the SSE format.
*   `wrap_toolcall_request` and `wrap_toolcall_response`: Format the information about tool calls and their results into a human-readable (often HTML-like for rich display) and machine-parseable format for the client.
*   `refine_mcp_response`: Likely standardizes the structure of tool call results before they are added to the message history.

This robust loop, combined with careful state management (message history, agent type), allows the `amazon-agent` to engage in multi-step reasoning and action sequences to fulfill complex e-commerce tasks.
