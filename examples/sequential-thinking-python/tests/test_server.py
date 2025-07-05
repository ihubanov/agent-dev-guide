import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock # For mocking the prompt logic

from server import app # Your main FastAPI app
from app.constants import CLIENT_NAME, CLIENT_VERSION, MODEL # For checking values
from app.prompt import PromptPayload # For type hinting if needed

# Test client fixture
@pytest.fixture
def client():
    return TestClient(app)

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html; charset=utf-8"
    content = response.text
    assert f"Welcome to {CLIENT_NAME} (v{CLIENT_VERSION})" in content
    assert "POST /prompt" in content
    assert "POST /call_tool/sequentialthinking" in content # Check if tool endpoint is mentioned

# Test the /prompt endpoint (integration style, but mocking the core prompt logic)
@pytest.mark.asyncio
@patch("server.process_prompt_logic") # Mock the imported prompt function in server.py
async def test_prompt_endpoint_success(mock_process_prompt, client: TestClient):

    # Define what the mocked process_prompt_logic async generator should yield
    async def mock_stream_generator(*args, **kwargs):
        yield b"data: " + json.dumps({"finished": False, "content": "Processing..."}).encode('utf-8') + b"\n\n"
        yield b"data: " + json.dumps({"finished": True, "content": "Done."}).encode('utf-8') + b"\n\n"

    mock_process_prompt.return_value = mock_stream_generator()

    payload = {"messages": [{"role": "user", "content": "Hello agent"}]}

    response = client.post("/prompt", json=payload) # TestClient handles async calls appropriately

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    # Collect streamed content
    # TestClient's response.text will contain the concatenated chunks for SSE
    # A more robust way to test SSE might involve reading the stream directly,
    # but for many cases, checking response.text is sufficient.

    # print(f"Raw response text: {response.text}") # For debugging

    expected_sse_data = [
        {"finished": False, "content": "Processing..."},
        {"finished": True, "content": "Done."}
    ]

    received_data = []
    for line in response.text.split("\n\n"):
        if line.startswith("data: "):
            try:
                data_json = json.loads(line[len("data: "):])
                received_data.append(data_json)
            except json.JSONDecodeError:
                if line.strip(): # Avoid erroring on empty lines if any
                    print(f"Failed to decode JSON from SSE line: {line}")

    assert received_data == expected_sse_data

    # Check that our mock was called with the correct payload
    mock_process_prompt.assert_called_once()
    call_args = mock_process_prompt.call_args[0][0] # First positional argument
    assert call_args["messages"] == payload["messages"]


@pytest.mark.asyncio
@patch("server.process_prompt_logic")
async def test_prompt_endpoint_empty_payload(mock_process_prompt, client: TestClient):
    # FastAPI should catch this based on Pydantic model PromptRequest
    # which inherits from PromptPayload (which is a Dict, so less strict here)
    # If PromptRequest was a Pydantic model with actual fields, it would be stricter.
    # Let's assume PromptRequest is `class PromptRequest(BaseModel): messages: List[Dict[str,str]]`
    # For now, PromptPayload is a Dict, so FastAPI might not validate upfront as much.
    # The validation happens inside process_prompt_logic.

    async def mock_error_stream_generator(*args, **kwargs):
        # Simulate error from within process_prompt_logic if payload is bad
        if not args[0].get("messages"):
             yield b"data: " + json.dumps({"finished": True, "content": "Error: No messages provided"}).encode('utf-8') + b"\n\n"
        else:
             yield b"data: " + json.dumps({"finished": False, "content": "Unexpected"}).encode('utf-8') + b"\n\n"


    mock_process_prompt.return_value = mock_error_stream_generator(PromptPayload(messages=[])) # Call with empty messages

    response = client.post("/prompt", json={"messages": []}) # Empty messages list

    assert response.status_code == 200 # Endpoint itself is fine

    received_data = []
    for line in response.text.split("\n\n"):
        if line.startswith("data: "):
            received_data.append(json.loads(line[len("data: "):]))

    assert len(received_data) == 1
    assert received_data[0]["finished"] == True
    assert "Error: No messages provided" in received_data[0]["content"] # Matching the mocked error

    mock_process_prompt.assert_called_once_with( {"messages": []})


def test_prompt_endpoint_invalid_json_body(client: TestClient):
    response = client.post("/prompt", data="this is not json")
    assert response.status_code == 422 # Unprocessable Entity for invalid JSON
    assert "application/json" in response.headers["content-type"]
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["type"] == "json_invalid"


# Test for the /api/call_tool/sequentialthinking endpoint (already covered in test_mcp_server.py integration part)
# but a simple check here confirms it's routed correctly by the main app.
def test_call_tool_endpoint_basic_check(client: TestClient):
    # This just checks if the endpoint exists and fails as expected with bad input
    # More detailed logic tests are in test_mcp_server.py
    from app.mcp_server import thinking_server_instance
    thinking_server_instance.__init__() # Reset state for predictability

    payload = {
        "arguments": {
            "thought": "Server integration test thought",
            "thoughtNumber": 1,
            "totalThoughts": 1,
            "nextThoughtNeeded": True
        }
    }
    response = client.post("/call_tool/sequentialthinking", json=payload)
    assert response.status_code == 200 # Successful call to the tool processing logic
    data = response.json()
    assert not data.get("is_error")
    content_text = json.loads(data["content"][0]["text"])
    assert content_text["thoughtNumber"] == 1


def test_docs_endpoints(client: TestClient):
    response_docs = client.get("/docs")
    assert response_docs.status_code == 200
    assert "text/html" in response_docs.headers["content-type"]

    response_redoc = client.get("/redoc")
    assert response_redoc.status_code == 200
    assert "text/html" in response_redoc.headers["content-type"]

# To run: pytest examples/sequential-thinking-python/tests/test_server.py
