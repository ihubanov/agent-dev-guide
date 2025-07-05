import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
# Useful for local development. In production, variables are typically set in the environment.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env') # .env in parent dir of app/
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# OpenAI API Configuration
LLM_API_KEY = os.getenv("OPENAI_API_KEY")
LLM_BASE_URL = os.getenv("OPENAI_BASE_URL") # Optional, for proxies or other OpenAI-compatible APIs

# Default Model
MODEL = os.getenv("MODEL_NAME", "gpt-4o") # Default to gpt-4o if not set

# Application Details (similar to TypeScript version)
CLIENT_NAME = "sequential-thinking-agent-python"
CLIENT_VERSION = "0.1.0"

# MCP Server URL (for the FastAPI app hosting the tool)
# This will typically be a local URL if the prompt client and tool server run in the same environment.
MCP_SERVER_BASE_URL = os.getenv("MCP_SERVER_BASE_URL", "http://localhost:8000")

# System Prompt File
# Assuming system-prompt.txt is in the parent directory of this 'app' directory
SYSTEM_PROMPT_FILE = os.path.join(os.path.dirname(__file__), "..", "system-prompt.txt")


# Validate that essential configurations are present
if not LLM_API_KEY:
    print("Warning: OPENAI_API_KEY is not set. The application may not function correctly.")
    # Depending on strictness, you might want to raise an error here:
    # raise ValueError("Missing critical environment variable: OPENAI_API_KEY")


if __name__ == "__main__":
    print("Loaded Constants:")
    print(f"  LLM_API_KEY: {'Set' if LLM_API_KEY else 'Not Set'}")
    print(f"  LLM_BASE_URL: {LLM_BASE_URL}")
    print(f"  MODEL: {MODEL}")
    print(f"  CLIENT_NAME: {CLIENT_NAME}")
    print(f"  CLIENT_VERSION: {CLIENT_VERSION}")
    print(f"  MCP_SERVER_BASE_URL: {MCP_SERVER_BASE_URL}")
    print(f"  SYSTEM_PROMPT_FILE: {SYSTEM_PROMPT_FILE}")

    # Test reading the system prompt
    try:
        with open(SYSTEM_PROMPT_FILE, "r", encoding="utf-8") as f:
            prompt_content = f.read()
        print(f"  System Prompt Content (first 50 chars): {prompt_content[:50]}...")
        print(f"  System prompt file exists: {os.path.exists(SYSTEM_PROMPT_FILE)}")
    except FileNotFoundError:
        print(f"  Error: System prompt file not found at {SYSTEM_PROMPT_FILE}")

    # To run this test: python -m examples.sequential-thinking-python.app.constants
    # (assuming your project root is in PYTHONPATH)
    # Or, navigate to examples/sequential-thinking-python and run: python -m app.constants
    print(f"\nTo run these tests, navigate to 'examples/sequential-thinking-python' and run: python -m app.constants")
