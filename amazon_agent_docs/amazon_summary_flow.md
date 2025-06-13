## How it Works - Summary Flow

The `amazon-agent` operates through a sequence of steps involving server initialization, user interaction, LLM processing, browser automation, and streaming responses. Here's a summary of a typical request lifecycle:

1.  **Server Initialization & VNC Setup:**
    *   When the agent starts (e.g., via `docker run` which executes the `ENTRYPOINT` in the `Dockerfile`), the `server.py` script is launched.
    *   The `lifespan` asynchronous context manager in `server.py` performs crucial setup:
        *   It initializes the Xvfb virtual display, Openbox window manager, x11vnc server, and the noVNC proxy for web-based VNC access.
        *   It starts and configures a Playwright browser instance (via the `browser_use` library).
        *   The browser automatically navigates to the `AMAZON_URL` specified in `app/config.py`.
    *   Users can obtain the URL to view this live browser session by querying the `/processing-url` endpoint.

2.  **User Sends Prompt:**
    *   A user or client application sends an HTTP `POST` request to the `/prompt` endpoint of the agent.
    *   The request body is a JSON payload containing the conversation history, for example:
        ```json
        {
          "messages": [
            {"role": "user", "content": "Find me a coffee maker under $50"}
          ]
        }
        ```

3.  **Request Received by FastAPI (`server.py`):**
    *   The FastAPI application defined in `server.py` receives the request at the `/prompt` endpoint.

4.  **Agent Processing Initiated (`app/agent.py` - `prompt` function):**
    *   The request handler in `server.py` calls the `prompt` asynchronous generator function located in `app/agent.py`.
    *   The `messages` from the request and the active `browser_context` are passed to this function.
    *   The chat history is refined (e.g., by `refine_chat_history` from `app/utils.py`), and the system prompt (from `system_prompt.txt`) is prepended to provide context to the LLM.
    *   An initial API request is made to the configured LLM, sending the processed messages and the list of available tools (defined in `app/tools.py`).

5.  **LLM Responds (Text or Tool Call):**
    *   **If the LLM provides a direct textual response:** This text is yielded by the `app/agent.py`'s `prompt` function. The `stream_reader` in `server.py` then formats it as a Server-Sent Event (SSE) and streams it back to the client.
    *   **If the LLM requests a tool call:** The LLM's response will include a `tool_calls` object specifying the tool's `name` and `arguments`. The `app/agent.py` logic parses this request.

6.  **Agent Handoff (if applicable):**
    *   The agent logic in `app/agent.py` (using `get_agent_for_tool`) determines if the requested tool requires a specific "agent persona" (e.g., "shopping_browsing" or "purchase_management").
    *   If a handoff between personas is detected (e.g., switching from searching products to managing an existing order), a system message is added to the conversation history to re-orient the LLM for the new context.

7.  **Tool Execution:**
    *   A "tool call request" message, indicating which tool is about to be run with which arguments, is formatted (using `wrap_toolcall_request`) and streamed to the client.
    *   The `execute_openai_compatible_toolcall` function in `app/agent.py` is invoked. It uses internal mappings to find the Python implementation of the requested tool in `app/tool_impl.py`.
    *   The corresponding tool function from `app/tool_impl.py` is executed. This function uses the `BrowserContext` (Playwright) to perform actions on the live web page (e.g., typing text into a search bar, clicking buttons, extracting product details).
    *   Many tool implementations are asynchronous generators and can `yield` intermediate results or log messages. These are wrapped (using `wrap_toolcall_response`) and streamed to the client, providing visibility into the tool's progress.
    *   The final result of the tool's execution is captured.

8.  **Result Sent to LLM:**
    *   The captured result from the tool is formatted as a "tool" role message and appended to the conversation history in `app/agent.py`.
    *   The agent then sends this updated conversation history (including the tool's outcome) back to the LLM.

9.  **Loop or Final Response:**
    *   The process loops back to step 5. The LLM, now aware of the tool's result, will decide the next action:
        *   Provide more textual response.
        *   Request another tool call.
        *   Conclude the interaction if the task is complete.
    *   This iterative process of LLM reasoning, tool execution, and observation continues until the user's initial request is fulfilled or a predefined limit (e.g., maximum number of tool calls) is reached.

10. **Stream Termination:**
    *   Once the entire interaction is complete and the `app/agent.py`'s `prompt` generator finishes, the `stream_reader` function in `server.py` executes its `finally` block.
    *   It sends a special SSE message, `data: [DONE]\n\n`, to the client, signaling that the stream has ended and no more data will be sent.
    *   The HTTP connection is then closed. The client application will have received the complete sequence of interactions, including the LLM's text responses and detailed information about any tool calls made.

This flow enables the `amazon-agent` to handle complex, multi-step tasks by breaking them down into LLM reasoning steps and concrete browser actions, all while providing continuous feedback to the user.
