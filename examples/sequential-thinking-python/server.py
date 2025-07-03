from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json

# Import the router from your mcp_server module
from app.mcp_server import router as mcp_router
# Import the main prompt processing logic
from app.prompt import prompt as process_prompt_logic, PromptPayload
from app.constants import CLIENT_NAME, CLIENT_VERSION


# Initialize FastAPI app
app = FastAPI(
    title=CLIENT_NAME,
    version=CLIENT_VERSION,
    description="Python implementation of the Sequential Thinking Agent."
)

# Add CORS middleware if you plan to call this from a browser-based client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include the MCP tool router at the root level
# This makes POST /call_tool/sequentialthinking available
app.include_router(mcp_router)

@app.get("/", response_class=HTMLResponse, tags=["General"])
async def root():
    """
    Root endpoint providing basic information about the agent.
    """
    return f"""
    <html>
        <head>
            <title>{CLIENT_NAME}</title>
        </head>
        <body>
            <h1>Welcome to {CLIENT_NAME} (v{CLIENT_VERSION})</h1>
            <p>This is a Python implementation of the Sequential Thinking Agent.</p>
            <p>Key Endpoints:</p>
            <ul>
                <li><code>POST /prompt</code>: Main endpoint to interact with the agent (expects JSON payload).</li>
                <li><code>POST /call_tool/sequentialthinking</code>: Endpoint for the 'sequentialthinking' tool.</li>
                <li><code>GET /docs</code>: API documentation (Swagger UI).</li>
                <li><code>GET /redoc</code>: Alternative API documentation (ReDoc).</li>
            </ul>
        </body>
    </html>
    """

# Define the main prompt endpoint
class PromptRequest(PromptPayload): # Inherits from PromptPayload for structure
    pass

@app.post("/prompt", tags=["Agent Interaction"])
async def handle_prompt(request_payload: PromptRequest) -> StreamingResponse:
    """
    Handles user prompts and streams back the agent's responses.
    Input payload should be: `{"messages": [{"role": "user", "content": "Your message"}]}`
    """
    # The process_prompt_logic is an async generator yielding bytes (SSE formatted)
    return StreamingResponse(process_prompt_logic(request_payload.model_dump()), media_type="text/event-stream")


if __name__ == "__main__":
    # This allows running the server directly using `python server.py`
    # However, for development, `uvicorn server:app --reload` is often preferred.
    print(f"Starting {CLIENT_NAME} v{CLIENT_VERSION} server...")
    print(f"Access API docs at http://localhost:8000/docs or http://localhost:8000/redoc")
    print(f"Main prompt endpoint: POST http://localhost:8000/prompt")
    print(f"Sequential Thinking tool endpoint: POST http://localhost:8000/call_tool/sequentialthinking")

    uvicorn.run(app, host="0.0.0.0", port=8000)

# To run from command line:
# uvicorn examples.sequential-thinking-python.server:app --reload --port 8000
#
# Example curl for /prompt endpoint:
# curl -X POST "http://localhost:8000/prompt" \
# -H "Content-Type: application/json" \
# -d '{"messages": [{"role": "user", "content": "Tell me a joke about philosophers and tools."}]}' \
# --no-buffer
#
# Example curl for /call_tool/sequentialthinking (simulating OpenAI calling the tool):
# curl -X POST "http://localhost:8000/call_tool/sequentialthinking" \
# -H "Content-Type: application/json" \
# -d '{"arguments": {"thought": "Initial thought for joke.", "nextThoughtNeeded": true, "thoughtNumber": 1, "totalThoughts": 3}}'

# Path confirmation:
# - GET / (HTML info)
# - POST /prompt (Main interaction)
# - POST /call_tool/sequentialthinking (Tool endpoint from mcp_router, now at root)
# - GET /docs, GET /redoc (FastAPI docs)
# This structure is consistent with utils.py's process_tool_calls expecting MCP_SERVER_BASE_URL/call_tool/tool_name.
# (e.g. http://localhost:8000/call_tool/sequentialthinking if MCP_SERVER_BASE_URL is http://localhost:8000)
