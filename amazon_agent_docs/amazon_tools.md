## Core Functionality - Tools (`app/tools.py`, `app/tool_impl.py`)

The `amazon-agent`'s ability to perform concrete actions on an e-commerce website is realized through a system of "tools." These tools are functions that the Large Language Model (LLM) can request to be executed. The definition, implementation, and execution of these tools are primarily handled in `app/tools.py`, `app/tool_impl.py`, and `app/agent.py`.

### Tool Definitions/Schemas (`app/tools.py`)

The `app/tools.py` file is responsible for defining the schemas of all tools that the agent can make available to the LLM. This allows the LLM to understand what each tool does, what arguments it expects, and in what format.

1.  **Providing Tool Definitions**:
    *   A function, typically named `get_functions()` or similar, returns a list of dictionaries. Each dictionary represents the schema for a single tool, conforming to the OpenAI function calling/tool specification.
        ```python
        # Example structure in app/tools.py
        functions = [
            {
                "type": "function",
                "function": {
                    "name": "search_products",
                    "description": "Search products with the specified criteria.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The query to search for. For example, 'laptop'"
                            }
                        },
                        "required": ["query"],
                    }
                }
            },
            # ... other tool definitions
        ]

        def get_functions():
            return functions
        ```

2.  **Tool Schema Structure**: Each tool definition includes:
    *   `type`: Typically "function".
    *   `function`: An object containing:
        *   `name`: The unique name of the tool (e.g., `search_products`). This is what the LLM will use to refer to the tool.
        *   `description`: A clear, natural language description of what the tool does. This is crucial for the LLM to determine when to use the tool.
        *   `parameters`: An OpenAPI-compatible JSON schema object that describes the arguments the tool accepts. This includes the `type` of each parameter (e.g., "string", "number", "boolean"), a `description` for each, and which parameters are `required`.

3.  **Defined E-commerce Tools**: The `amazon-agent` defines a suite of tools tailored for e-commerce operations, such as:
    *   `search_products`: To find products based on a query.
    *   `get_product_detail`: To fetch details for a specific product (likely using its URL).
    *   `add_to_cart`: To add the currently viewed or a specified product to the shopping cart.
    *   `go_to_cart`: To navigate to the shopping cart page.
    *   `adjust_cart`: To change quantities or remove items from the cart.
    *   `check_out`: To initiate or complete the checkout process.
    *   `get_order_history`: To retrieve the user's past orders.
    *   `cancel_order`: To cancel a specific order by its ID.
    *   `request_refund`: To request a refund for a specific order.

### Tool Implementations (`app/tool_impl.py`)

For each tool defined in `app/tools.py`, there is a corresponding Python function in `app/tool_impl.py` that contains the actual logic to perform the action.

1.  **Function Signature**: These implementation functions typically accept `BrowserContext` (aliased as `ctx`) as their first argument, followed by other arguments as specified in their respective schemas in `tools.py`.
    ```python
    # Example structure in app/tool_impl.py
    async def search_products(ctx: BrowserContext, query: str) -> AsyncGenerator[str, None]:
        # ... implementation using Playwright via ctx ...
        yield "Searching for products related to: " + query
        # ... more actions and yields ...
        yield "Found X products." # Final or summary message
    ```

2.  **Browser Interaction**: Inside these functions, the `ctx` object (which is a Playwright `BrowserContext` instance) is used to interact with the web browser. This includes actions like:
    *   Navigating to URLs (`await page.goto(...)`).
    *   Finding elements (`await page.query_selector(...)`, `await page.locator(...).click()`).
    *   Typing text (`await locator.fill(...)`).
    *   Clicking buttons (`await locator.click()`).
    *   Extracting data from the page (`await locator.inner_text()`, `await locator.get_attribute(...)`).

3.  **Asynchronous and Streaming Results**:
    *   The tool implementation functions are asynchronous (`async def`).
    *   Many of them are asynchronous generators (`-> AsyncGenerator[str, None]`), using `async for ... yield` to stream intermediate results, logs, or observations back to the `app/agent.py`'s main loop. This allows the client to receive real-time updates about the progress of a tool's execution (e.g., "Navigated to product page," "Clicked 'Add to Cart' button").

### Tool Execution Mapping (`app/agent.py`)

The `app/agent.py` file bridges the gap between the LLM's request for a tool call and the execution of its Python implementation. This is primarily handled by the `execute_openai_compatible_toolcall` function.

1.  **Receiving Tool Request**: This function is called when the LLM returns a `tool_calls` object. It receives the `name` of the tool to be executed and the `args` (arguments) for it, as decided by the LLM.

2.  **Mapping Tool Name to Function**:
    *   `app/agent.py` defines dictionaries like `shopping_browsing_tool_function_map` and `purchase_management_tool_function_map`. These dictionaries map tool names (strings) to the actual callable Python functions in `app/tool_impl.py`.
        ```python
        # In app/agent.py
        shopping_browsing_tool_function_map = {
            "search_products": search_products, # search_products imported from .tool_impl
            "get_product_detail": get_product_detail,
            # ...
        }
        ```
    *   The `execute_openai_compatible_toolcall` function uses these maps (based on the determined `agent_type`) to find the correct implementation function corresponding to the requested `name`.

3.  **Calling the Implementation**:
    *   Once the function is found, it's called with the `browser_context` (`ctx`) and the arguments (`**args`) provided by the LLM.
        ```python
        # In execute_openai_compatible_toolcall within app/agent.py
        if agent_type == "shopping_browsing":
            tool_func = shopping_browsing_tool_function_map.get(name)
        # ...
        if tool_func is not None:
            async for msg in tool_func(ctx, **args): # Calls the function from tool_impl.py
                yield msg
        ```

4.  **Handling Unknown Tools**: If the requested tool `name` is not found in the maps, an error message is yielded, indicating that the tool is not available.

This clear separation of tool definition (schema for LLM), implementation (Python code for browser actions), and execution mapping allows for a modular and extensible system for adding new capabilities to the `amazon-agent`.
