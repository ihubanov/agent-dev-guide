## Core Functionality - Streaming Responses (`server.py`, `app/agent.py`)

A key feature of the `amazon-agent` is its ability to stream responses back to the client in real-time. This ensures that the user is not kept waiting for the entire operation to complete but receives continuous feedback. This includes direct text from the LLM, notifications about tool calls being made, and intermediate results or logs from those tools as they execute. This streaming mechanism is a coordinated effort primarily between `app/agent.py` and `server.py`.

### Streaming from `app/agent.py`'s `prompt` Function

The core agent logic in `app/agent.py`, encapsulated within the `prompt` asynchronous generator function, is designed from the ground up for streaming:

1.  **Asynchronous Generator (`AsyncGenerator`)**: The `prompt` function is defined as an `async def ... -> AsyncGenerator[str, None]`. This allows it to `yield` multiple pieces of information sequentially as they become available.

2.  **Yielding Various Message Types**: Throughout its execution, the `prompt` function yields different types of messages:
    *   **Direct LLM Content**: When the LLM provides a direct textual answer, this content is yielded immediately.
        ```python
        # In app/agent.py
        if completion.choices[0].message.content:
            yield completion.choices[0].message.content
        ```
    *   **Tool Call Requests**: Before executing a tool, a formatted message indicating the tool call is about to happen is yielded. This uses helper functions from `app/utils.py` like `wrap_toolcall_request` (to structure the message, often as HTML-like content for rich display) and `to_chunk_data` (to format it as a byte string suitable for SSE).
        ```python
        # In app/agent.py, before executing a tool
        yield await to_chunk_data(wrap_toolcall_request(
            uuid=response_uuid,
            fn_name=_name,
            args=_args
        ))
        ```
    *   **Intermediate Tool Results/Logs**: The tool implementation functions in `app/tool_impl.py` are often asynchronous generators themselves. As they perform browser actions, they can `yield` intermediate status updates or logs. These are caught in `app/agent.py` and then wrapped (using `wrap_toolcall_response` and `to_chunk_data`) and yielded to the client stream.
        ```python
        # In app/agent.py, during tool execution
        async for msg in execute_openai_compatible_toolcall(...):
            yield await to_chunk_data(
                wrap_toolcall_response(...) # Containing msg from tool_impl
            )
        ```
    *   **Error Messages**: If exceptions occur during LLM communication or tool execution, formatted error messages are yielded.

### FastAPI's `StreamingResponse` in `server.py`

The `server.py` file is responsible for taking the stream produced by `app/agent.py` and delivering it to the client over HTTP using Server-Sent Events (SSE).

1.  **Endpoint Definition**: The `/prompt` endpoint in `server.py` is designed to return a `StreamingResponse` from FastAPI:
    ```python
    # In server.py
    from fastapi.responses import StreamingResponse

    @api_app.post("/prompt", response_model=None)
    async def post_prompt(body: dict) -> Union[StreamingResponse, PlainTextResponse, JSONResponse]:
        # ...
        stream = app.prompt(...) # from app/agent.py
        return StreamingResponse(
            stream_reader(stream), # stream_reader processes the generator
            media_type="text/event-stream"
        )
    ```
2.  **Content Source**: The content for this `StreamingResponse` is the asynchronous generator returned by `app.prompt`, but it's first processed by a utility function called `stream_reader`.
3.  **Media Type**: The `media_type` is explicitly set to `"text/event-stream"`, which is the standard MIME type for Server-Sent Events.

### The `stream_reader` Utility in `server.py`

The `stream_reader` asynchronous generator function in `server.py` acts as an intermediary, further processing and formatting the chunks received from `app/agent.py`'s `prompt` function to ensure they are valid SSE messages.

1.  **Iterating Chunks**: It iterates through the chunks yielded by the `app.prompt` generator.

2.  **SSE Formatting**:
    *   **String Chunks**: If a chunk yielded by `app.prompt` is a plain string (e.g., direct LLM text), `stream_reader` wraps it in a `ChatCompletionStreamResponse` Pydantic model (from `app/models/oai_compatible_models.py`). This model structures the content similarly to how OpenAI's API streams chat completions (with fields like `id`, `object`, `created`, `model`, `choices`, `delta`). This Pydantic object is then serialized to JSON, and the resulting string is formatted as an SSE message: `data: {json_payload}\n\n`.
        ```python
        # In server.py stream_reader
        if isinstance(chunk, str):
            chunk_model = ChatCompletionStreamResponse(...)
            yield (f'data: {chunk_model.model_dump_json()}\n\n').encode('utf-8')
        ```
    *   **Byte Chunks**: If a chunk is already bytes (this is the case for messages formatted by `to_chunk_data` in `app/utils.py`, such as tool call requests/responses, which are already in the `data: ...\n\n` format), `stream_reader` yields it directly.
        ```python
        # In server.py stream_reader
        else: # Assumes it's bytes
            yield chunk
        ```

3.  **Error Handling**: `stream_reader` includes `try...except` blocks to catch various `openai` API errors (`APIConnectionError`, `RateLimitError`, `APIError`) and other general exceptions that might not have been caught deeper in `app/agent.py`. If an error occurs, it creates a `PromptErrorResponse` model, serializes it to JSON, and yields it as an SSE-formatted error message.

4.  **`[DONE]` Signal**: Crucially, in its `finally` block, `stream_reader` always yields the byte string `b'data: [DONE]\n\n'`. This is the standard way to signal to an SSE client that the stream has ended and no more messages will be sent.

This layered approach to streaming—generation of diverse event types in `app/agent.py`, and standardized SSE formatting and error handling in `server.py`'s `stream_reader`—provides a robust and informative real-time experience for the client interacting with the `amazon-agent`.
