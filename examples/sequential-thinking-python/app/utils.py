import json
import re
import httpx # Using httpx for async requests
from typing import List, Dict, Any, Tuple, AsyncGenerator, Optional

# Assuming mcp_server.py is in the same directory or accessible in PYTHONPATH
# For the tool definition, if needed by the client side preparing the OpenAI call.
# However, the OpenAI call itself will use the `tools` parameter with the definition.
# from .mcp_server import SEQUENTIAL_THINKING_TOOL_DEF


def convert_mcp_tools_to_openai_format(mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts a list of MCP-style tool definitions to the format expected by OpenAI API.
    Note: In this refactor, we are defining SEQUENTIAL_THINKING_TOOL_DEF directly in
    the OpenAI format, so this function might be less critical if we only have one tool
    defined this way. It's kept for conceptual similarity or future expansion.
    """
    openai_tools = []
    for tool in mcp_tools:
        if tool.get("type") == "function" and tool.get("function"):
            openai_tools.append(tool) # Already in desired format
        else: # Attempt a basic conversion if structure is different
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("inputSchema") # MCP uses inputSchema
                }
            })
    return openai_tools


async def process_tool_calls(
    tool_calls: List[Dict[str, Any]], # Expects OpenAI tool_call objects
    mcp_server_url: str # e.g., "http://localhost:8000"
) -> List[Dict[str, Any]]:
    """
    Processes tool calls by making HTTP requests to the MCP-like server (FastAPI app).
    Returns a list of OpenAI-compatible tool message objects.
    """
    tool_messages = []
    async with httpx.AsyncClient() as client:
        for tool_call in tool_calls:
            tool_name = tool_call.get("function", {}).get("name")
            tool_id = tool_call.get("id")
            try:
                # Arguments are expected to be a JSON string by OpenAI, parse them
                arguments_str = tool_call.get("function", {}).get("arguments", "{}")
                arguments = json.loads(arguments_str)
            except json.JSONDecodeError:
                print(f"Error decoding arguments for tool {tool_name}: {arguments_str}")
                tool_result_content = json.dumps({
                    "error": "Invalid JSON arguments",
                    "status": "failed"
                })
            else:
                request_payload = {"arguments": arguments}
                api_url = f"{mcp_server_url}/call_tool/{tool_name}"

                try:
                    response = await client.post(api_url, json=request_payload)
                    response.raise_for_status() # Raise an exception for HTTP errors

                    # Assuming the server returns JSON compatible with ToolOutput Pydantic model
                    # Specifically, we need the 'text' field from the first 'content' item.
                    response_data = response.json() # This is a dict like ToolOutput

                    # The actual content from the tool is nested
                    if response_data.get("content") and isinstance(response_data["content"], list) and len(response_data["content"]) > 0:
                         # The text field itself is a JSON string representing the tool's structured output
                        tool_result_content = response_data["content"][0].get("text", "{}")
                    else:
                        tool_result_content = json.dumps({"error": "Tool response format unexpected", "details": response_data})

                except httpx.HTTPStatusError as e:
                    print(f"HTTP error calling tool {tool_name}: {e.response.status_code} - {e.response.text}")
                    tool_result_content = json.dumps({
                        "error": f"HTTP error {e.response.status_code}",
                        "details": e.response.text,
                        "status": "failed"
                    })
                except httpx.RequestError as e:
                    print(f"Request error calling tool {tool_name}: {e}")
                    tool_result_content = json.dumps({
                        "error": "Request error",
                        "details": str(e),
                        "status": "failed"
                    })
                except json.JSONDecodeError: # If response from tool server is not JSON
                    print(f"Failed to decode JSON response from tool {tool_name}")
                    tool_result_content = json.dumps({
                        "error": "Invalid JSON response from tool",
                        "status": "failed"
                    })


            tool_messages.append({
                "tool_call_id": tool_id,
                "role": "tool",
                "name": tool_name,
                "content": tool_result_content, # This should be a string
            })
    return tool_messages


def enqueue_message(finished: bool, content: str, is_tool_call_ui: bool = False, tool_name: Optional[str] = None, tool_args: Optional[str] = None, tool_response: Optional[str] = None) -> Dict[str, Any]:
    """
    Formats a message for streaming (similar to the TypeScript version).
    The `is_tool_call_ui` and related params are new additions for richer UI if needed.
    """
    message: Dict[str, Any] = {"finished": finished}
    if content:
        message["content"] = content
    if is_tool_call_ui:
        message["type"] = "tool_activity"
        if tool_name:
            message["tool_name"] = tool_name
        if tool_args: # Should be JSON string
            message["tool_args"] = tool_args
        if tool_response: # Should be JSON string
            message["tool_response"] = tool_response

    return message


THINK_TAG_START = "<think>"
THINK_TAG_END = "</think>"
OPEN_THINK_TAG_REGEX = re.compile(r"<think>", re.IGNORECASE)
CLOSE_THINK_TAG_REGEX = re.compile(r"</think>", re.IGNORECASE)

def remove_think(text: Optional[str]) -> str:
    """
    Removes <think>...</think> tags from a string.
    Handles nested tags by removing the outermost pair.
    Also handles incomplete tags if the LLM streams them.
    """
    if text is None:
        return ""

    # More robust removal of all occurrences, not just one pair
    text = OPEN_THINK_TAG_REGEX.sub("", text)
    text = CLOSE_THINK_TAG_REGEX.sub("", text)
    return text.strip()


async def stream_string_to_bytes(content_stream: AsyncGenerator[str, None]) -> AsyncGenerator[bytes, None]:
    """
    Converts an async generator of strings to an async generator of bytes (UTF-8 encoded).
    """
    async for chunk in content_stream:
        yield chunk.encode('utf-8')

if __name__ == "__main__":
    # Test remove_think
    test_strings = [
        "This is a <think>thought process</think> sentence.",
        "<think>Another thought</think> and some more text.",
        "No tags here.",
        "<think> Mismatched tag",
        "Another <think>thought</think> and <think>one more</think>.",
        "<think>Outer <think>Inner thought</think> thought</think>",
        None,
        ""
    ]
    print("Testing remove_think:")
    for s in test_strings:
        print(f"Original: '{s}' -> Cleaned: '{remove_think(s)}'")

    # Example of how convert_mcp_tools_to_openai_format might be used (though less relevant now)
    print("\nTesting convert_mcp_tools_to_openai_format:")
    from .mcp_server import SEQUENTIAL_THINKING_TOOL_DEF # Relative import for example
    converted = convert_mcp_tools_to_openai_format([SEQUENTIAL_THINKING_TOOL_DEF])
    # print(json.dumps(converted, indent=2)) # This will just print the same def back

    # process_tool_calls would need a running server to test properly.
    # You could mock httpx.AsyncClient for unit testing.
    print("\n`process_tool_calls` needs a running server or mocks to test.")
    print("`enqueue_message` is straightforward data packaging.")

    # To run this test: python -m examples.sequential-thinking-python.app.utils
    # (assuming your project root is in PYTHONPATH)
    # Or, navigate to examples/sequential-thinking-python and run: python -m app.utils
    print(f"\nTo run these tests, navigate to 'examples/sequential-thinking-python' and run: python -m app.utils")
