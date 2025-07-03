import pytest
import json
from unittest.mock import AsyncMock, patch

from app.utils import (
    remove_think,
    enqueue_message,
    process_tool_calls,
    convert_mcp_tools_to_openai_format # Added for completeness
)
from app.mcp_server import SEQUENTIAL_THINKING_TOOL_DEF # For testing conversion

# Test remove_think
@pytest.mark.parametrize("input_text, expected_output", [
    ("This is a <think>thought process</think> sentence.", "This is a thought process sentence."),
    ("<think>Another thought</think> and some more text.", "Another thought and some more text."),
    ("No tags here.", "No tags here."),
    ("<think> Mismatched tag", "Mismatched tag"),
    ("Another <think>thought</think> and <think>one more</think>.", "Another thought and one more."),
    ("<think>Outer <think>Inner thought</think> thought</think>", "Outer Inner thought thought"),
    ("Text with <think>  leading/trailing spaces in tag  </think> end.", "Text with   leading/trailing spaces in tag   end."),
    ("", ""),
    (None, "")
])
def test_remove_think(input_text, expected_output):
    assert remove_think(input_text) == expected_output

# Test enqueue_message
def test_enqueue_message_finished_no_content():
    msg = enqueue_message(finished=True, content="")
    assert msg == {"finished": True, "content": ""} # content key is added even if empty, as per current code

def test_enqueue_message_not_finished_with_content():
    msg = enqueue_message(finished=False, content="Hello")
    assert msg == {"finished": False, "content": "Hello"}

def test_enqueue_message_tool_activity():
    msg = enqueue_message(
        finished=False,
        content="<action>Tool action</action>",
        is_tool_call_ui=True,
        tool_name="test_tool",
        tool_args='{"arg": "val"}',
        tool_response='{"res": "ok"}'
    )
    assert msg == {
        "finished": False,
        "content": "<action>Tool action</action>",
        "type": "tool_activity",
        "tool_name": "test_tool",
        "tool_args": '{"arg": "val"}',
        "tool_response": '{"res": "ok"}'
    }

# Test convert_mcp_tools_to_openai_format
def test_convert_mcp_tools_to_openai_format_already_correct():
    # Using the existing SEQUENTIAL_THINKING_TOOL_DEF which is already in OpenAI format
    openai_tools = convert_mcp_tools_to_openai_format([SEQUENTIAL_THINKING_TOOL_DEF])
    assert len(openai_tools) == 1
    assert openai_tools[0] == SEQUENTIAL_THINKING_TOOL_DEF

def test_convert_mcp_tools_to_openai_format_basic_conversion():
    mcp_style_tool = {
        "name": "custom_tool",
        "description": "A custom tool.",
        "inputSchema": {
            "type": "object",
            "properties": {"param1": {"type": "string"}}
        }
    }
    expected_openai_tool = {
        "type": "function",
        "function": {
            "name": "custom_tool",
            "description": "A custom tool.",
            "parameters": {
                "type": "object",
                "properties": {"param1": {"type": "string"}}
            }
        }
    }
    openai_tools = convert_mcp_tools_to_openai_format([mcp_style_tool])
    assert len(openai_tools) == 1
    assert openai_tools[0] == expected_openai_tool


# Tests for process_tool_calls (requires mocking httpx.AsyncClient)
@pytest.mark.asyncio
async def test_process_tool_calls_successful():
    mock_tool_calls = [
        {
            "id": "call_123",
            "type": "function",
            "function": {
                "name": "sequentialthinking",
                "arguments": '{"thought": "Test thought", "thoughtNumber": 1, "totalThoughts": 1, "nextThoughtNeeded": false}'
            }
        }
    ]
    mcp_server_url = "http://fake-server.com"

    # Mock httpx.AsyncClient response
    mock_response = AsyncMock()
    mock_response.status_code = 200
    # The tool server's response has content -> type, text. The text is a JSON string.
    tool_server_output_text = json.dumps({
        "thoughtNumber": 1, "totalThoughts": 1, "nextThoughtNeeded": False, "processed_thought": "Test thought"
    })
    mock_response.json.return_value = { # This is the ToolOutput model from mcp_server
        "content": [{"type": "text", "text": tool_server_output_text}],
        "is_error": False
    }

    with patch("app.utils.httpx.AsyncClient") as MockAsyncClient:
        mock_async_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        mock_async_client_instance.post.return_value = mock_response

        results = await process_tool_calls(mock_tool_calls, mcp_server_url)

        assert len(results) == 1
        assert results[0]["tool_call_id"] == "call_123"
        assert results[0]["role"] == "tool"
        assert results[0]["name"] == "sequentialthinking"
        # The content here should be the JSON string that was in `text` field
        assert results[0]["content"] == tool_server_output_text

        mock_async_client_instance.post.assert_called_once()
        call_args = mock_async_client_instance.post.call_args
        assert call_args[0][0] == f"{mcp_server_url}/call_tool/sequentialthinking"
        assert call_args[1]["json"]["arguments"]["thought"] == "Test thought"

@pytest.mark.asyncio
async def test_process_tool_calls_http_error():
    mock_tool_calls = [{"id": "call_err", "type": "function", "function": {"name": "error_tool", "arguments": "{}"}}]
    mcp_server_url = "http://fake-server.com"

    mock_response = AsyncMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    # Configure raise_for_status to raise an exception
    mock_response.raise_for_status = AsyncMock(side_effect=Exception(f"HTTP error 500: {mock_response.text}"))


    with patch("app.utils.httpx.AsyncClient") as MockAsyncClient:
        mock_async_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        # Make the post call raise an httpx.HTTPStatusError
        # We need to mock the actual exception type that httpx would raise
        import httpx
        http_error = httpx.HTTPStatusError("Server Error", request=AsyncMock(), response=mock_response)
        mock_async_client_instance.post.side_effect = http_error


        results = await process_tool_calls(mock_tool_calls, mcp_server_url)

        assert len(results) == 1
        assert results[0]["tool_call_id"] == "call_err"
        tool_content = json.loads(results[0]["content"])
        assert tool_content["error"] == "HTTP error 500" # Error code from mock_response
        assert tool_content["status"] == "failed"
        assert "Internal Server Error" in tool_content["details"]


@pytest.mark.asyncio
async def test_process_tool_calls_request_error():
    mock_tool_calls = [{"id": "call_req_err", "type": "function", "function": {"name": "req_error_tool", "arguments": "{}"}}]
    mcp_server_url = "http://fake-server.com"

    with patch("app.utils.httpx.AsyncClient") as MockAsyncClient:
        mock_async_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        import httpx
        mock_async_client_instance.post.side_effect = httpx.RequestError("Connection failed", request=AsyncMock())

        results = await process_tool_calls(mock_tool_calls, mcp_server_url)

        assert len(results) == 1
        tool_content = json.loads(results[0]["content"])
        assert tool_content["error"] == "Request error"
        assert tool_content["status"] == "failed"
        assert "Connection failed" in tool_content["details"]

@pytest.mark.asyncio
async def test_process_tool_calls_invalid_json_arguments():
    mock_tool_calls = [
        {
            "id": "call_json_err",
            "type": "function",
            "function": {
                "name": "some_tool",
                "arguments": '{"thought": "Test thought", "broken_json": }' # Invalid JSON
            }
        }
    ]
    mcp_server_url = "http://fake-server.com"

    # No need to mock httpx client here as it fails before the call
    results = await process_tool_calls(mock_tool_calls, mcp_server_url)

    assert len(results) == 1
    tool_content = json.loads(results[0]["content"])
    assert tool_content["error"] == "Invalid JSON arguments"
    assert tool_content["status"] == "failed"

@pytest.mark.asyncio
async def test_process_tool_calls_tool_server_returns_malformed_json_response():
    mock_tool_calls = [
        {
            "id": "call_malformed_resp",
            "type": "function",
            "function": {"name": "malformed_resp_tool", "arguments": "{}"}
        }
    ]
    mcp_server_url = "http://fake-server.com"

    mock_response = AsyncMock()
    mock_response.status_code = 200
    # Simulate the server returning a non-JSON string or malformed JSON
    mock_response.json.side_effect = json.JSONDecodeError("msg", "doc", 0)


    with patch("app.utils.httpx.AsyncClient") as MockAsyncClient:
        mock_async_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        mock_async_client_instance.post.return_value = mock_response

        results = await process_tool_calls(mock_tool_calls, mcp_server_url)

        assert len(results) == 1
        tool_content = json.loads(results[0]["content"]) # This is the error JSON created by process_tool_calls
        assert tool_content["error"] == "Invalid JSON response from tool"
        assert tool_content["status"] == "failed"


@pytest.mark.asyncio
async def test_process_tool_calls_tool_server_unexpected_content_structure():
    mock_tool_calls = [
        {
            "id": "call_bad_struct",
            "type": "function",
            "function": {"name": "bad_struct_tool", "arguments": "{}"}
        }
    ]
    mcp_server_url = "http://fake-server.com"

    mock_response = AsyncMock()
    mock_response.status_code = 200
    # Tool server returns valid JSON, but not the expected ToolOutput structure
    mock_response.json.return_value = {"unexpected_key": "unexpected_value"}

    with patch("app.utils.httpx.AsyncClient") as MockAsyncClient:
        mock_async_client_instance = MockAsyncClient.return_value.__aenter__.return_value
        mock_async_client_instance.post.return_value = mock_response

        results = await process_tool_calls(mock_tool_calls, mcp_server_url)

        assert len(results) == 1
        tool_content = json.loads(results[0]["content"])
        assert tool_content["error"] == "Tool response format unexpected"
        assert tool_content["details"] == {"unexpected_key": "unexpected_value"}

# To run: pytest examples/sequential-thinking-python/tests/app/test_utils.py
