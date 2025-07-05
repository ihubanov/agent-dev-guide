import asyncio
import json
import os
import datetime
from typing import List, Dict, Any, Union, AsyncGenerator, Optional # Added Optional
from openai import OpenAI, AsyncOpenAI # AsyncOpenAI for async streaming
import httpx

from .constants import (
    LLM_API_KEY,
    LLM_BASE_URL,
    MODEL,
    MCP_SERVER_BASE_URL,
    SYSTEM_PROMPT_FILE,
    CLIENT_NAME,
    CLIENT_VERSION
)
from .utils import (
    process_tool_calls,
    enqueue_message,
    remove_think,
    stream_string_to_bytes, # For converting string stream to byte stream if needed by FastAPI response
    convert_mcp_tools_to_openai_format # Though we might use the direct definition
)
# Import the tool definition from mcp_server to pass to OpenAI
from .mcp_server import SEQUENTIAL_THINKING_TOOL_DEF, list_tools


# Initialize OpenAI client
# Use AsyncOpenAI for asynchronous operations, especially streaming
if LLM_BASE_URL:
    async_openai_client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, max_retries=3)
    # Sync client also, if needed for any non-async operations (though try to keep async)
    openai_client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL, max_retries=3)
else:
    async_openai_client = AsyncOpenAI(api_key=LLM_API_KEY, max_retries=3)
    openai_client = OpenAI(api_key=LLM_API_KEY, max_retries=3)


# Load System Prompt
try:
    with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
        BASE_SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print(f"Error: System prompt file not found at {SYSTEM_PROMPT_FILE}. Using a default prompt.")
    BASE_SYSTEM_PROMPT = "You are a helpful AI assistant."


class PromptPayload(Dict[str, Any]): # Using Dict for simplicity, can be Pydantic model
    messages: List[Dict[str, str]]


async def prompt(payload: PromptPayload) -> AsyncGenerator[bytes, None]:
    """
    Main prompt function that interacts with OpenAI and the tool server.
    Streams responses back as server-sent events (SSE-like JSON strings).
    """
    print(f"Starting prompt with payload: {payload}")

    if not LLM_API_KEY:
        error_msg = enqueue_message(True, "Error: OPENAI_API_KEY is not configured.")
        yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
        return

    if not payload.get("messages"):
        error_msg = enqueue_message(True, "Error: No messages provided in payload.")
        yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
        return

    # Get available tools (in our case, just the sequentialthinking tool)
    # The list_tools() from mcp_server.py returns it in the correct OpenAI format
    available_tools_openai_format = list_tools()

    # Add current time to the system prompt
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    system_prompt_with_time = f"{BASE_SYSTEM_PROMPT}\nThe current time is {current_time} (only use this information for time-aware responses, actions)."

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_prompt_with_time},
        *payload["messages"] # Make sure payload messages are in {"role": "user/assistant", "content": "..."} format
    ]

    finished_normally = False
    try:
        while not finished_normally:
            params = {
                "model": MODEL,
                "messages": messages,
                "temperature": 0, # As in original TS
                "stream": True,
                "seed": 42, # As in original TS
                "tools": available_tools_openai_format,
                "tool_choice": "auto" # Explicitly set or "required" if a tool must be called
            }

            stream_content_parts = []
            full_tool_calls = [] # To store complete tool call objects from stream

            # print(f"OpenAI Request Params: {json.dumps(params, indent=2)}")

            try:
                stream = await async_openai_client.chat.completions.create(**params) # type: ignore

                current_tool_calls_delta = [] # For assembling streamed tool calls

                async for chunk in stream:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    if delta and delta.content:
                        stream_content_parts.append(delta.content)
                        yield f"data: {json.dumps(enqueue_message(False, delta.content))}\n\n".encode('utf-8')

                    if delta and delta.tool_calls:
                        for tool_call_chunk in delta.tool_calls:
                            # Append or update tool call info from chunks
                            if tool_call_chunk.index >= len(current_tool_calls_delta):
                                current_tool_calls_delta.append({
                                    "id": tool_call_chunk.id or f"call_{tool_call_chunk.index}_{datetime.datetime.now().timestamp()}",
                                    "type": "function", # Assuming type is function
                                    "function": {"name": "", "arguments": ""}
                                })

                            tc_delta_ref = current_tool_calls_delta[tool_call_chunk.index]
                            if tool_call_chunk.id:
                                tc_delta_ref["id"] = tool_call_chunk.id
                            if tool_call_chunk.function and tool_call_chunk.function.name:
                                tc_delta_ref["function"]["name"] = tool_call_chunk.function.name
                            if tool_call_chunk.function and tool_call_chunk.function.arguments:
                                tc_delta_ref["function"]["arguments"] += tool_call_chunk.function.arguments

                    if choice.finish_reason:
                        # print(f"Finish reason: {choice.finish_reason}")
                        if choice.finish_reason == "stop":
                            finished_normally = True
                            break
                        elif choice.finish_reason == "tool_calls":
                            # Consolidate tool calls accumulated from deltas
                            full_tool_calls = current_tool_calls_delta
                            break # Break from inner chunk loop to process tool calls

                if not full_tool_calls and choice.finish_reason != "stop": # Handle cases where stream ends before finish_reason
                    if current_tool_calls_delta and any(tc.get("function", {}).get("name") for tc in current_tool_calls_delta):
                         full_tool_calls = current_tool_calls_delta
                    elif not stream_content_parts: # No content and no tool calls, unusual
                         finished_normally = True # Assume finished if nothing else to do

            except Exception as e:
                print(f"Error during OpenAI API call: {e}")
                error_msg = enqueue_message(True, f"Error communicating with OpenAI: {str(e)}")
                yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
                return # Stop processing

            # If there's text content from assistant, add it to messages
            assistant_response_content = "".join(stream_content_parts)
            if assistant_response_content or full_tool_calls: # Add assistant message if there's content OR tool calls
                msg_to_append = {"role": "assistant", "content": remove_think(assistant_response_content)}
                if full_tool_calls:
                    msg_to_append["tool_calls"] = full_tool_calls
                messages.append(msg_to_append)


            if full_tool_calls:
                finished_normally = False # Not finished, need to process tools

                for tool_call_obj in full_tool_calls: # tool_call_obj is now assembled
                    tool_name = tool_call_obj.get("function", {}).get("name", "unknown_tool")
                    tool_args_str = tool_call_obj.get("function", {}).get("arguments", "{}")

                    # UI message for executing tool
                    action_msg = f"<action>Executing {tool_name}</action>\n\n"
                    yield f"data: {json.dumps(enqueue_message(False, action_msg, is_tool_call_ui=True, tool_name=tool_name))}\n\n".encode('utf-8')

                    # UI message for arguments
                    args_details_md = f"<details>\n<summary>Arguments</summary>\n\n```json\n{tool_args_str}\n```\n\n</details>\n\n"
                    yield f"data: {json.dumps(enqueue_message(False, args_details_md, is_tool_call_ui=True, tool_name=tool_name, tool_args=tool_args_str))}\n\n".encode('utf-8')

                # process_tool_calls expects a list of OpenAI tool_call objects
                # and returns a list of OpenAI tool message objects
                tool_messages_from_server = await process_tool_calls(full_tool_calls, MCP_SERVER_BASE_URL)

                for i, tool_msg_content in enumerate(tool_messages_from_server):
                    # tool_msg_content is like {"tool_call_id": ..., "role": "tool", "name": ..., "content": "{...}"}
                    # The "content" is the JSON string from the tool server.
                    tool_response_str = tool_msg_content.get("content", "{}")

                    # UI message for response
                    # Ensure tool_name is correctly sourced if not in tool_msg_content (it should be)
                    current_tool_name_for_ui = tool_msg_content.get("name", full_tool_calls[i]["function"]["name"] if i < len(full_tool_calls) else "unknown_tool" )
                    response_details_md = f"<details>\n<summary>Response from {current_tool_name_for_ui}</summary>\n\n```json\n{tool_response_str}\n```\n\n</details>\n\n"
                    yield f"data: {json.dumps(enqueue_message(False, response_details_md, is_tool_call_ui=True, tool_name=current_tool_name_for_ui, tool_response=tool_response_str))}\n\n".encode('utf-8')

                    messages.append(tool_msg_content) # Add tool result to conversation history

            elif not assistant_response_content and not finished_normally:
                # If no content and no tool calls, and not explicitly stopped, it might be an issue or end of chain.
                # This can happen if the model streams nothing then a finish_reason.
                # If finish_reason was 'stop', finished_normally would be true.
                # If it was 'tool_calls' but full_tool_calls is empty, that's odd.
                # print("Warning: Loop iteration with no new content, tool calls, or explicit stop.")
                # To prevent potential infinite loops if API behaves unexpectedly:
                if not choice or not choice.finish_reason : # if stream ended abruptly without finish reason
                    finished_normally = True # assume finished


        # Final "finished" message
        yield f"data: {json.dumps(enqueue_message(True, ''))}\n\n".encode('utf-8')

    except httpx.HTTPStatusError as e:
        print(f"HTTP error during tool call processing: {e.response.status_code} - {e.response.text}")
        error_msg = enqueue_message(True, f"Error during tool call: {e.response.status_code} - {e.response.text}")
        yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')
    except Exception as e:
        print(f"Error in prompt execution: {e}")
        import traceback
        traceback.print_exc()
        error_msg = enqueue_message(True, f"An unexpected error occurred: {str(e)}")
        yield f"data: {json.dumps(error_msg)}\n\n".encode('utf-8')


async def main_test():
    """ Test function to simulate calling the prompt """
    print("Testing prompt function...")

    # Create a dummy .env file if it doesn't exist for testing
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', '.env')):
        print("Creating dummy .env for testing (OPENAI_API_KEY='testkey')")
        with open(os.path.join(os.path.dirname(__file__), '..', '.env'), "w") as f:
            f.write("OPENAI_API_KEY=\"test_not_a_real_key_for_testing_prompt_module\"\n")
            f.write("MCP_SERVER_BASE_URL=\"http://localhost:8001\"\n") # Use a different port for dummy server

    # This test requires a running MCP server (FastAPI app) and potentially an OpenAI-compatible API
    # For now, it will just print the SSE events it would send.

    test_payload: PromptPayload = {
        "messages": [
            {"role": "user", "content": "What is the capital of France? And can you use a tool to think about it first?"}
        ]
    }

    print(f"\nCalling prompt with payload: {test_payload}")
    print("Expected SSE output (will be JSON strings):")

    # Mock the OpenAI client and MCP server for this local test if you don't want to make real calls
    # For now, this will attempt real calls if API key is set and server is running.

    # A simple dummy server for testing process_tool_calls if MCP_SERVER_BASE_URL is http://localhost:8001
    # You would run this in a separate terminal:
    # uvicorn examples.sequential-thinking-python.app.prompt:dummy_tool_server_app --port 8001 --log-level debug

    async for data_bytes in prompt(test_payload):
        print(data_bytes.decode('utf-8').strip())

# Dummy FastAPI app for testing tool calls locally without the full mcp_server
from fastapi import FastAPI, Request
dummy_tool_server_app = FastAPI()

@dummy_tool_server_app.post("/call_tool/{tool_name}")
async def dummy_call_tool(tool_name: str, request: Request):
    args = await request.json()
    print(f"[DummyToolServer] Called tool: {tool_name} with args: {args}")
    if tool_name == "sequentialthinking":
        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "thoughtNumber": args.get("arguments",{}).get("thoughtNumber",0) + 1,
                    "totalThoughts": args.get("arguments",{}).get("totalThoughts",1),
                    "nextThoughtNeeded": False, # End the thinking for dummy
                    "processed_thought": args.get("arguments",{}).get("thought","Dummy thought processed")
                })
            }],
            "is_error": False
        }
    return {"content": [{"type": "text", "text": json.dumps({"error": "Unknown tool in dummy server"})}]}


if __name__ == "__main__":
    print("To test the prompt function, ensure your OPENAI_API_KEY is set in .env")
    print("And ensure the MCP server (FastAPI app from server.py) is running on port 8000 (or as configured).")
    print("Or, run the dummy tool server: uvicorn examples.sequential-thinking-python.app.prompt:dummy_tool_server_app --port 8001")
    print("Then run this script: python -m examples.sequential-thinking-python.app.prompt")

    # Check if OPENAI_API_KEY is available, otherwise skip live test
    if not LLM_API_KEY or LLM_API_KEY == "test_not_a_real_key_for_testing_prompt_module":
        print("\nOPENAI_API_KEY not found or is a test key. Skipping live prompt test.")
        print("You can manually run `asyncio.run(main_test())` if you have a mock server or want to see init errors.")
    else:
        asyncio.run(main_test())
