import pytest
import json
import os
from unittest.mock import AsyncMock, patch, MagicMock
from app.prompt import prompt, PromptPayload
from app.constants import LLM_API_KEY, MCP_SERVER_BASE_URL, SYSTEM_PROMPT_FILE, MODEL
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk, Choice, ChoiceDelta, ChoiceDeltaToolCall, ChoiceDeltaToolCallFunction
from openai.types.chat.chat_completion_message_tool_call import ChatCompletionMessageToolCall, Function

# Helper to collect streamed data from the prompt function
async def collect_streamed_data(generator):
    data = []
    raw_bytes = b""
    async for chunk_bytes in generator:
        raw_bytes += chunk_bytes
        # Assuming SSE format: "data: {...}\n\n"
        parts = raw_bytes.split(b'\n\n')
        for part in parts[:-1]: # Process all complete messages
            if part.startswith(b"data: "):
                try:
                    json_data = json.loads(part[len(b"data: "):].decode('utf-8'))
                    data.append(json_data)
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e} on data: {part[len(b'data: '):].decode('utf-8')}")
            raw_bytes = parts[-1] # Keep the incomplete part for next iteration

        # If the last part is a complete message (e.g. final message)
        if raw_bytes.startswith(b"data: ") and raw_bytes.endswith(b"\n\n"):
            if raw_bytes.startswith(b"data: "):
                try:
                    json_data = json.loads(raw_bytes[len(b"data: "):-2].decode('utf-8')) # remove \n\n too
                    data.append(json_data)
                    raw_bytes = b""
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error on final part: {e} on data: {raw_bytes[len(b'data: '):-2].decode('utf-8')}")


    # Process any remaining data that might not end with \n\n but is a full data message
    if raw_bytes.startswith(b"data: "):
        try:
            # Attempt to decode if it looks like a complete JSON object without the final \n\n
            # This might happen if the stream ends abruptly or the last message is not followed by \n\n
            # For robust parsing, one might need a more sophisticated SSE client logic.
            # Here, we assume that if it starts with "data: ", it's intended to be a JSON message.
            json_str = raw_bytes[len(b"data: "):].decode('utf-8').strip()
            if json_str: # Ensure it's not empty after stripping
                json_data = json.loads(json_str)
                data.append(json_data)
        except json.JSONDecodeError:
            print(f"Could not decode trailing data: {raw_bytes.decode('utf-8', errors='ignore')}")
            pass # Ignore if it's not valid JSON

    return data


@pytest.fixture(autouse=True)
def setup_env_vars(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")
    monkeypatch.setenv("MCP_SERVER_BASE_URL", "http://localhost:8000") # Default, can be overridden
    # Ensure system prompt file exists for tests or mock its reading
    if not os.path.exists(SYSTEM_PROMPT_FILE):
        with open(SYSTEM_PROMPT_FILE, "w") as f:
            f.write("Test system prompt.")
    # Reload constants and prompt module to pick up mocked env vars if they are loaded at import time
    import importlib
    from app import constants, prompt as prompt_module
    importlib.reload(constants)
    importlib.reload(prompt_module) # Ensures prompt module uses mocked constants
    return prompt_module.prompt # Return the reloaded prompt function


@pytest.mark.asyncio
async def test_prompt_no_api_key(setup_env_vars, monkeypatch):
    prompt_func = setup_env_vars
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Crucial: reload constants and prompt module so they see the missing API key
    import importlib
    from app import constants, prompt as prompt_module
    importlib.reload(constants) # constants will now have LLM_API_KEY = None
    importlib.reload(prompt_module) # prompt module re-initializes its OpenAI client etc.
    prompt_func = prompt_module.prompt


    payload: PromptPayload = {"messages": [{"role": "user", "content": "Hello"}]}
    results = await collect_streamed_data(prompt_func(payload))

    assert len(results) == 1
    assert results[0]["finished"] == True
    assert "OPENAI_API_KEY is not configured" in results[0]["content"]

@pytest.mark.asyncio
async def test_prompt_no_messages(setup_env_vars):
    prompt_func = setup_env_vars
    payload: PromptPayload = {"messages": []} # No messages
    results = await collect_streamed_data(prompt_func(payload))

    assert len(results) == 1
    assert results[0]["finished"] == True
    assert "No messages provided in payload" in results[0]["content"]


@pytest.mark.asyncio
@patch('app.prompt.async_openai_client.chat.completions.create')
async def test_prompt_simple_text_response(mock_openai_create, setup_env_vars):
    prompt_func = setup_env_vars
    # Mock OpenAI stream response for a simple text message
    async def mock_stream():
        yield ChatCompletionChunk(
            id='chatcmpl-test', choices=[Choice(delta=ChoiceDelta(content='Hello,'), finish_reason=None, index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )
        yield ChatCompletionChunk(
            id='chatcmpl-test', choices=[Choice(delta=ChoiceDelta(content=' world!'), finish_reason=None, index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )
        yield ChatCompletionChunk(
            id='chatcmpl-test', choices=[Choice(delta=ChoiceDelta(), finish_reason='stop', index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )
    mock_openai_create.return_value = mock_stream()

    payload: PromptPayload = {"messages": [{"role": "user", "content": "Say hi"}]}
    results = await collect_streamed_data(prompt_func(payload))

    mock_openai_create.assert_called_once()
    # print(f"OpenAI call args: {mock_openai_create.call_args}")
    # print(f"Results: {results}")


    assert len(results) == 3 # Two content messages, one finish message
    assert results[0] == {"finished": False, "content": "Hello,"}
    assert results[1] == {"finished": False, "content": " world!"}
    assert results[2] == {"finished": True, "content": ""}


@pytest.mark.asyncio
@patch('app.prompt.async_openai_client.chat.completions.create')
@patch('app.prompt.process_tool_calls') # Mock the function that calls the tool server
async def test_prompt_with_tool_call(mock_process_tool_calls, mock_openai_create, setup_env_vars):
    prompt_func = setup_env_vars

    # --- First OpenAI call: Assistant requests a tool call ---
    async def mock_openai_stream_tool_request():
        # Streamed tool call parts
        yield ChatCompletionChunk(
            id='chatcmpl-tool', choices=[Choice(delta=ChoiceDelta(tool_calls=[
                ChoiceDeltaToolCall(index=0, id="call_abc123", function=ChoiceDeltaToolCallFunction(name="sequentialthinking", arguments='{"thought":'))
            ]), finish_reason=None, index=0)], model=MODEL, object='chat.completion.chunk', created=123
        )
        yield ChatCompletionChunk(
            id='chatcmpl-tool', choices=[Choice(delta=ChoiceDelta(tool_calls=[
                ChoiceDeltaToolCall(index=0, function=ChoiceDeltaToolCallFunction(arguments='"First thought"}'))
            ]), finish_reason=None, index=0)], model=MODEL, object='chat.completion.chunk', created=123
        )
        # Finish reason indicates tool_calls are complete
        yield ChatCompletionChunk(
            id='chatcmpl-tool', choices=[Choice(delta=ChoiceDelta(), finish_reason='tool_calls', index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )

    # --- Mock process_tool_calls response ---
    # This is what our FastAPI server would return, wrapped by process_tool_calls
    mock_process_tool_calls.return_value = [
        {
            "tool_call_id": "call_abc123", # Must match the ID from OpenAI
            "role": "tool",
            "name": "sequentialthinking",
            "content": json.dumps({"status": "success", "thought_processed": "First thought"}) # JSON string
        }
    ]

    # --- Second OpenAI call: Assistant responds after tool execution ---
    async def mock_openai_stream_final_response():
        yield ChatCompletionChunk(
            id='chatcmpl-final', choices=[Choice(delta=ChoiceDelta(content='Tool finished. Final answer.'), finish_reason=None, index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )
        yield ChatCompletionChunk(
            id='chatcmpl-final', choices=[Choice(delta=ChoiceDelta(), finish_reason='stop', index=0)],
            model=MODEL, object='chat.completion.chunk', created=123
        )

    # Configure the mock_openai_create to return different streams for sequential calls
    mock_openai_create.side_effect = [
        mock_openai_stream_tool_request(),
        mock_openai_stream_final_response()
    ]

    payload: PromptPayload = {"messages": [{"role": "user", "content": "Think about something."}]}
    results = await collect_streamed_data(prompt_func(payload))

    # print(f"Results from tool call test: {json.dumps(results, indent=2)}")

    assert mock_openai_create.call_count == 2
    mock_process_tool_calls.assert_called_once()

    # Check arguments passed to process_tool_calls
    # process_tool_calls is called with:
    # tool_calls: List[Dict[str, Any]] (OpenAI tool_call objects)
    # mcp_server_url: str
    args, _ = mock_process_tool_calls.call_args
    assert len(args[0]) == 1 # One tool call object
    assert args[0][0]["id"] == "call_abc123"
    assert args[0][0]["function"]["name"] == "sequentialthinking"
    assert json.loads(args[0][0]["function"]["arguments"]) == {"thought": "First thought"}
    assert args[1] == MCP_SERVER_BASE_URL


    # Expected sequence of messages:
    # 1. (Optional) Assistant content before tool call (not in this mock)
    # 2. UI message: Executing tool (content: "<action>...</action>")
    # 3. UI message: Tool arguments (content: "<details>...</details>")
    # 4. UI message: Tool response (content: "<details>...</details>")
    # 5. Assistant final content chunk
    # 6. Finished message

    # Let's find these messages in the results
    action_msg = next(r for r in results if r.get("content", "").startswith("<action>"))
    args_msg = next(r for r in results if r.get("content", "").startswith("<details><summary>Arguments"))
    resp_msg = next(r for r in results if r.get("content", "").startswith("<details><summary>Response"))
    final_content_msg = next(r for r in results if r.get("content") == "Tool finished. Final answer.")
    finish_msg = next(r for r in results if r.get("finished") == True and r.get("content") == "")

    assert action_msg and action_msg["tool_name"] == "sequentialthinking"
    assert args_msg and json.loads(args_msg["tool_args"]) == {"thought": "First thought"}
    assert resp_msg and json.loads(resp_msg["tool_response"]) == {"status": "success", "thought_processed": "First thought"}
    assert final_content_msg
    assert finish_msg

    # Verify the messages passed to the second OpenAI call included the tool responses
    second_openai_call_args = mock_openai_create.call_args_list[1]
    messages_to_second_call = second_openai_call_args[1]['messages'] # or .kwargs if using kwargs

    # Expected messages: system, user, assistant (with tool_call), tool (result)
    assert len(messages_to_second_call) == 4
    assert messages_to_second_call[0]["role"] == "system"
    assert messages_to_second_call[1]["role"] == "user"
    assert messages_to_second_call[2]["role"] == "assistant"
    assert messages_to_second_call[2]["tool_calls"][0]["id"] == "call_abc123"
    assert messages_to_second_call[3]["role"] == "tool"
    assert messages_to_second_call[3]["tool_call_id"] == "call_abc123"
    assert messages_to_second_call[3]["content"] == json.dumps({"status": "success", "thought_processed": "First thought"})


@pytest.mark.asyncio
@patch('app.prompt.async_openai_client.chat.completions.create')
async def test_prompt_openai_api_error(mock_openai_create, setup_env_vars):
    prompt_func = setup_env_vars
    # Mock OpenAI client to raise an APIError
    import openai
    mock_openai_create.side_effect = openai.APIError("Test API Error", request=MagicMock(), body=None)

    payload: PromptPayload = {"messages": [{"role": "user", "content": "This will fail"}]}
    results = await collect_streamed_data(prompt_func(payload))

    # print(f"API Error test results: {results}")
    assert len(results) == 1
    assert results[0]["finished"] == True
    assert "Error communicating with OpenAI: Test API Error" in results[0]["content"]


@pytest.mark.asyncio
@patch('app.prompt.async_openai_client.chat.completions.create')
@patch('app.prompt.process_tool_calls')
async def test_prompt_tool_call_processing_error(mock_process_tool_calls, mock_openai_create, setup_env_vars):
    prompt_func = setup_env_vars
    # Similar to test_prompt_with_tool_call for the first part
    async def mock_openai_stream_tool_request():
        yield ChatCompletionChunk(id='chatcmpl-tool', choices=[Choice(delta=ChoiceDelta(tool_calls=[ChoiceDeltaToolCall(index=0,id="call_fail123", function=ChoiceDeltaToolCallFunction(name="sequentialthinking", arguments='{"problem": "true"}'))]), finish_reason=None, index=0)], model=MODEL, object='chat.completion.chunk', created=123)
        yield ChatCompletionChunk(id='chatcmpl-tool', choices=[Choice(delta=ChoiceDelta(), finish_reason='tool_calls', index=0)], model=MODEL, object='chat.completion.chunk', created=123)

    mock_openai_create.return_value = mock_openai_stream_tool_request()

    # Mock process_tool_calls to simulate an error during tool execution
    # For example, the tool server returns an HTTP error, or httpx itself fails
    import httpx
    # This mock needs to be an async function if process_tool_calls is async
    mock_process_tool_calls.side_effect = httpx.HTTPStatusError(
        "Tool Server Error",
        request=MagicMock(),
        response=MagicMock(status_code=500, text="Internal Server Error on Tool")
    )

    payload: PromptPayload = {"messages": [{"role": "user", "content": "Call a failing tool"}]}
    results = await collect_streamed_data(prompt_func(payload))

    # print(f"Tool processing error results: {json.dumps(results, indent=2)}")

    # Expected:
    # 1. UI message: Executing tool
    # 2. UI message: Tool arguments
    # 3. Error message propagated from the exception in prompt()
    #    The error message should be the one from the httpx.HTTPStatusError

    action_msg = next((r for r in results if r.get("content", "").startswith("<action>")), None)
    args_msg = next((r for r in results if r.get("content", "").startswith("<details><summary>Arguments")), None)
    error_msg = next((r for r in results if r.get("finished") == True and "Error during tool call" in r.get("content","")), None)

    assert action_msg is not None
    assert args_msg is not None
    assert error_msg is not None
    assert "500 - Internal Server Error on Tool" in error_msg["content"]

    # Ensure OpenAI was called once (for the tool request)
    mock_openai_create.assert_called_once()
    # Ensure process_tool_calls was called
    mock_process_tool_calls.assert_called_once()

# To run: pytest examples/sequential-thinking-python/tests/app/test_prompt.py
