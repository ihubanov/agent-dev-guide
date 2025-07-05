# Sequential Thinking Agent (Python)

This agent demonstrates how to implement an agent that uses sequential thinking, refactored into Python from a TypeScript example. It uses FastAPI for its server component, interacts with the OpenAI API, and features a mechanism for multi-step reasoning using a dedicated "sequentialthinking" tool.

## Features
- **Sequential Reasoning**: Utilizes a tool to break down problems into a sequence of thoughts.
- **OpenAI Integration**: Leverages OpenAI models for language understanding and generation.
- **FastAPI Backend**: Provides a robust and fast server for handling prompts and tool calls.
- **Streaming Responses**: Streams responses back to the client for a more interactive experience.
- **Environment Variable Configuration**: Easily configurable via a `.env` file.
- **Docker Support**: Includes a `Dockerfile` for containerization.
- **Unit & Integration Tests**: Comes with a suite of tests using `pytest`.

## Project Structure
- `app/`: Contains the core application logic.
  - `__init__.py`: Makes `app` a Python package.
  - `constants.py`: Defines application constants and loads environment variables (e.g., API keys, model names).
  - `mcp_server.py`: Implements the `SequentialThinkingServer` class (which processes "thoughts") and the FastAPI endpoint (`/call_tool/sequentialthinking`) for the tool.
  - `prompt.py`: Contains the main `prompt` async generator function that orchestrates interactions with the OpenAI API and the tool server.
  - `utils.py`: Provides utility functions (e.g., for processing tool calls, formatting messages).
- `tests/`: Contains all tests.
  - `app/`: Tests for modules within the `app` directory (`test_mcp_server.py`, `test_prompt.py`, `test_utils.py`).
  - `test_server.py`: Integration tests for the main FastAPI server endpoints (`server.py`).
- `server.py`: The main FastAPI application file that sets up routes and runs the Uvicorn server.
- `requirements.txt`: Lists Python dependencies for the project.
- `Dockerfile`: For building a Docker image of the application.
- `system-prompt.txt`: The base system prompt used for instructing the OpenAI model.
- `.env.example`: Example environment file. Create a `.env` from this.
- `README.md`: This file.

## Running Tests
The project uses `pytest` for testing. To run the tests:
1. Ensure you have installed dependencies, including `pytest` and `pytest-asyncio` (they are in `requirements.txt`).
2. Activate your virtual environment.
3. Navigate to the `examples/sequential-thinking-python` directory.
4. Run pytest:
   ```bash
   pytest
   ```
   Or, to run specific tests:
   ```bash
   pytest tests/app/test_prompt.py
   ```

## Docker Deployment
To build and run the agent using Docker:

1.  **Build the Docker image:**
    Navigate to the `examples/sequential-thinking-python` directory and run:
    ```bash
    docker build -t sequential-thinking-python-agent .
    ```

2.  **Run the Docker container:**
    ```bash
    docker run -d -p 8000:8000 \
    -e OPENAI_API_KEY="your_openai_api_key_here" \
    sequential-thinking-python-agent
    ```
    Replace `"your_openai_api_key_here"` with your actual OpenAI API key. The agent will then be accessible at `http://localhost:8000`.

## How it Works
1.  A client sends a list of messages to the `/prompt` endpoint.
2.  The `prompt` function in `app/prompt.py` receives the request.
3.  It constructs a system prompt (from `system-prompt.txt`, augmented with the current time) and combines it with the user's messages.
4.  This package is sent to the OpenAI API (e.g., GPT-4o), configured to use the `sequentialthinking` tool.
5.  **Tool Invocation**: If the OpenAI model decides to use the `sequentialthinking` tool, it returns a tool call request.
    -   The `prompt` function then makes an HTTP POST request to its own local FastAPI server endpoint (`/call_tool/sequentialthinking`).
    -   The `app/mcp_server.py` module handles this request via its `SequentialThinkingServer` class. This class processes the "thought" (which could be an initial thought, a revision, a branch, etc.) and logs it. It returns a JSON response indicating the outcome of the thought processing.
6.  The `prompt` function receives the tool's JSON response and sends it back to the OpenAI API.
7.  OpenAI processes the tool's output and generates the next part of the response, which might be more text or another tool call.
8.  This loop (steps 4-7) continues until the OpenAI API provides a final message without requesting further tool calls.
9.  All assistant messages, UI updates for tool calls (like "Executing tool X", arguments, and responses), and the final "finished" signal are streamed back to the original client as Server-Sent Events (SSE).

## Customization
-   **Agent Behavior**: Modify the system prompt in `system-prompt.txt` or the core logic in `app/prompt.py`.
-   **Tool Logic**: Enhance the `SequentialThinkingServer` class in `app/mcp_server.py` or add new tools by defining their schemas and handling logic.
-   **Model**: Change the OpenAI model used by updating the `MODEL_NAME` environment variable in your `.env` file (or directly in `app/constants.py`).

## Quick Start

### 1. Prerequisites
- Python 3.9 or higher.
- An OpenAI API Key.
- Docker (optional, for containerized deployment).

### 2. Setup Environment Variables
Copy the `.env.example` file to `.env` in the `examples/sequential-thinking-python` directory:
```bash
cp .env.example .env
```
Then, edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY="your_openai_api_key_here"
# Optional:
# MODEL_NAME="gpt-4o"
# MCP_SERVER_BASE_URL="http://localhost:8000" # Base URL where this server itself runs
# DISABLE_THOUGHT_LOGGING="false" # Set to "true" to disable console logging of thoughts
```

### 3. Install Dependencies
Navigate to the `examples/sequential-thinking-python` directory and install the required Python packages:
```bash
python -m venv venv      # Create a virtual environment (recommended)
source venv/bin/activate # Activate the virtual environment (on Linux/macOS)
# For Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Agent Server
Start the FastAPI server using Uvicorn:
```bash
uvicorn server:app --reload --port 8000
```
The server will be available at `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

### 5. Interacting with the Agent
The primary way to interact with the agent is by sending a POST request to the `/prompt` endpoint.

**Example using cURL:**
```bash
curl -X POST "http://localhost:8000/prompt" \
-H "Content-Type: application/json" \
-d '{"messages": [{"role": "user", "content": "Explain quantum entanglement in simple terms, thinking step by step."}]}' \
--no-buffer
```
This will stream Server-Sent Events (SSE) back to your terminal. Each event is a JSON object.

The `sequentialthinking` tool, used internally by the agent, is exposed at `POST /call_tool/sequentialthinking`. This is typically called by the OpenAI model, not directly by end-users.

## Project Structure
- `app/`: Contains the core application logic.
  - `__init__.py`: Makes `app` a Python package.
  - `constants.py`: Defines application constants and loads environment variables.
  - `mcp_server.py`: Implements the `SequentialThinkingServer` logic and the FastAPI endpoint for tool calls.
  - `prompt.py`: Contains the main `prompt` function for interacting with OpenAI and the tool server.
  - `utils.py`: Provides utility functions.
- `server.py`: The main FastAPI application file.
- `requirements.txt`: Lists Python dependencies.
- `Dockerfile`: For containerizing the application.
- `system-prompt.txt`: The system prompt used for the OpenAI API.
- `README.md`: This file.

## How it Works
1. The `prompt` function in `app/prompt.py` takes a user's message list.
2. It constructs a system prompt (including the current time) and sends it along with the user messages to the OpenAI API, configured to use the `sequentialthinking` tool.
3. If the OpenAI API decides to use the `sequentialthinking` tool, the `prompt` function makes an HTTP POST request to the local FastAPI server endpoint (`/call_tool/sequentialthinking`).
4. The `app/mcp_server.py` handles this request, processes the "thought" using the `SequentialThinkingServer` class, and returns a result.
5. The `prompt` function then sends this tool result back to the OpenAI API to get the next response.
6. This process continues in a loop until the OpenAI API provides a final message without a tool call.
7. Responses are streamed back to the caller of the `prompt` function.

## Development
- To add or modify tool calls, edit `app/mcp_server.py`.
- To change the agent's behavior, modify the system prompt in `system-prompt.txt` or the logic in `app/prompt.py`.

## Packaging for Publishing (Example with Docker)
To package your agent using Docker:
1. Build the Docker image:
   ```bash
   docker build -t sequential-thinking-python .
   ```
2. Run the Docker container:
   ```bash
   docker run -d -p 8000:8000 -e OPENAI_API_KEY="your_openai_api_key_here" sequential-thinking-python
   ```
This will create a distributable package of your agent.
