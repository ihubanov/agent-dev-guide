import pytest
import json
from fastapi.testclient import TestClient

# Assuming your FastAPI app and SequentialThinkingServer class are structured as previously defined
# Adjust imports based on your actual project structure
from app.mcp_server import SequentialThinkingServer, ToolOutput, ThoughtDataInput, router as mcp_router
from server import app # Main FastAPI app for integration style testing of router

# Unit tests for SequentialThinkingServer class
class TestSequentialThinkingServerLogic:

    @pytest.fixture
    def server_instance(self):
        return SequentialThinkingServer()

    def test_initialization(self, server_instance: SequentialThinkingServer):
        assert isinstance(server_instance, SequentialThinkingServer)
        assert server_instance.thought_history == []
        assert server_instance.branches == {}

    def test_process_valid_thought(self, server_instance: SequentialThinkingServer):
        thought_data = {
            "thought": "This is a test thought.",
            "thoughtNumber": 1,
            "totalThoughts": 3,
            "nextThoughtNeeded": True
        }
        output = server_instance.process_thought(thought_data)

        assert not output.is_error
        assert len(output.content) == 1
        assert output.content[0].type == "text"

        response_data = json.loads(output.content[0].text)
        assert response_data["thoughtNumber"] == 1
        assert response_data["totalThoughts"] == 3
        assert response_data["nextThoughtNeeded"] == True
        assert len(server_instance.thought_history) == 1
        assert server_instance.thought_history[0]["thought"] == "This is a test thought."

    def test_process_thought_updates_total_thoughts(self, server_instance: SequentialThinkingServer):
        thought_data = {
            "thought": "Test thought high number.",
            "thoughtNumber": 5, # Higher than initial totalThoughts
            "totalThoughts": 3,
            "nextThoughtNeeded": True
        }
        output = server_instance.process_thought(thought_data)
        response_data = json.loads(output.content[0].text)
        assert response_data["totalThoughts"] == 5 # Should be updated
        assert server_instance.thought_history[0]["totalThoughts"] == 5

    def test_process_revision_thought(self, server_instance: SequentialThinkingServer):
        thought1 = {
            "thought": "Initial thought.",
            "thoughtNumber": 1, "totalThoughts": 2, "nextThoughtNeeded": True
        }
        server_instance.process_thought(thought1)

        revision_thought = {
            "thought": "Revised thought.",
            "thoughtNumber": 2, "totalThoughts": 2, "nextThoughtNeeded": False,
            "isRevision": True, "revisesThought": 1
        }
        output = server_instance.process_thought(revision_thought)
        assert not output.is_error
        response_data = json.loads(output.content[0].text)
        assert response_data["thoughtNumber"] == 2
        assert len(server_instance.thought_history) == 2
        assert server_instance.thought_history[1]["isRevision"] == True
        assert server_instance.thought_history[1]["revisesThought"] == 1

    def test_process_branch_thought(self, server_instance: SequentialThinkingServer):
        thought1 = {
            "thought": "Main branch thought.",
            "thoughtNumber": 1, "totalThoughts": 1, "nextThoughtNeeded": True
        }
        server_instance.process_thought(thought1)

        branch_thought = {
            "thought": "Branch A thought.",
            "thoughtNumber": 1, # Could be 1 for the branch
            "totalThoughts": 1, # For this branch
            "nextThoughtNeeded": False,
            "branchFromThought": 1,
            "branchId": "branchA"
        }
        output = server_instance.process_thought(branch_thought)
        assert not output.is_error
        response_data = json.loads(output.content[0].text)
        assert "branchA" in response_data["branches"]
        assert "branchA" in server_instance.branches
        assert len(server_instance.branches["branchA"]) == 1
        assert server_instance.branches["branchA"][0]["thought"] == "Branch A thought."

    def test_process_invalid_input_missing_required_field(self, server_instance: SequentialThinkingServer):
        invalid_data = {
            "thought": "Missing fields."
            # "thoughtNumber", "totalThoughts", "nextThoughtNeeded" are missing
        }
        output = server_instance.process_thought(invalid_data)
        assert output.is_error
        response_data = json.loads(output.content[0].text)
        assert "error" in response_data
        assert "validation error" in response_data["error"].lower() # Pydantic validation

    def test_process_invalid_input_wrong_type(self, server_instance: SequentialThinkingServer):
        invalid_data = {
            "thought": "Wrong type.",
            "thoughtNumber": "not-an-integer", # Wrong type
            "totalThoughts": 3,
            "nextThoughtNeeded": True
        }
        output = server_instance.process_thought(invalid_data)
        assert output.is_error
        response_data = json.loads(output.content[0].text)
        assert "error" in response_data
        assert "validation error" in response_data["error"].lower()

    def test_format_thought_regular(self, server_instance: SequentialThinkingServer):
        # Basic check, doesn't verify colors but structure
        thought_data = ThoughtDataInput(
            thought="Test", thoughtNumber=1, totalThoughts=1, nextThoughtNeeded=False
        ).model_dump(by_alias=True)
        formatted_str = server_instance._format_thought(thought_data)
        assert "Thought 1/1" in formatted_str
        assert "Test" in formatted_str

    def test_format_thought_revision(self, server_instance: SequentialThinkingServer):
        thought_data = ThoughtDataInput(
            thought="Revise", thoughtNumber=2, totalThoughts=2, nextThoughtNeeded=False,
            isRevision=True, revisesThought=1
        ).model_dump(by_alias=True)
        formatted_str = server_instance._format_thought(thought_data)
        assert "Revision 2/2" in formatted_str
        assert "(revising thought 1)" in formatted_str
        assert "Revise" in formatted_str

    def test_format_thought_branch(self, server_instance: SequentialThinkingServer):
        thought_data = ThoughtDataInput(
            thought="Branch", thoughtNumber=1, totalThoughts=1, nextThoughtNeeded=False,
            branchFromThought=1, branchId="B1"
        ).model_dump(by_alias=True)
        formatted_str = server_instance._format_thought(thought_data)
        assert "Branch 1/1" in formatted_str
        assert "(from thought 1, ID: B1)" in formatted_str
        assert "Branch" in formatted_str


# Integration tests for the FastAPI router /call_tool endpoint
# These use the TestClient for the main app
class TestMCPRouterIntegration:

    @pytest.fixture
    def client(self):
        # Reset server instance state for each test if necessary,
        # or ensure thinking_server_instance is fresh.
        # For simplicity, TestClient(app) will use the app's existing thinking_server_instance.
        # If state needs to be clean, you might need to re-initialize thinking_server_instance
        # or create a new app instance for each test.
        # from app.mcp_server import thinking_server_instance # to reset if needed
        # thinking_server_instance.__init__() # Example reset
        return TestClient(app)

    def test_call_tool_sequentialthinking_valid(self, client: TestClient):
        # Need to reset the global thinking_server_instance for clean test
        from app.mcp_server import thinking_server_instance
        thinking_server_instance.__init__() # Reset state

        payload = {
            "arguments": {
                "thought": "API test thought",
                "thoughtNumber": 1,
                "totalThoughts": 1,
                "nextThoughtNeeded": True
            }
        }
        response = client.post("/call_tool/sequentialthinking", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert not data.get("is_error")
        content_text = json.loads(data["content"][0]["text"])
        assert content_text["thoughtNumber"] == 1
        assert content_text["nextThoughtNeeded"] == True
        assert thinking_server_instance.thought_history[0]["thought"] == "API test thought"


    def test_call_tool_sequentialthinking_invalid_payload_structure(self, client: TestClient):
        # Payload missing "arguments" field
        payload = {
            "args": { # incorrect field name
                "thought": "API test thought",
                "thoughtNumber": 1,
                "totalThoughts": 1,
                "nextThoughtNeeded": True
            }
        }
        response = client.post("/call_tool/sequentialthinking", json=payload)
        assert response.status_code == 422 # FastAPI validation error for CallToolRequest model
        data = response.json()
        assert "detail" in data
        # Example: {'detail': [{'type': 'missing', 'loc': ['body', 'arguments'], 'msg': 'Field required', ...}]}

    def test_call_tool_sequentialthinking_invalid_thought_data(self, client: TestClient):
         # Payload with "arguments" but arguments themselves are invalid for ThoughtDataInput
        payload = {
            "arguments": {
                "thought": "API test thought",
                # "thoughtNumber": 1, # Missing required field within arguments
                "totalThoughts": 1,
                "nextThoughtNeeded": True
            }
        }
        response = client.post("/call_tool/sequentialthinking", json=payload)
        # This will be processed by SequentialThinkingServer.process_thought, which returns a 200 OK
        # but with an error flag in its own JSON response.
        assert response.status_code == 200
        data = response.json()
        assert data.get("is_error") == True
        content_text = json.loads(data["content"][0]["text"])
        assert "error" in content_text
        assert "validation error" in content_text["error"].lower()


    def test_call_tool_unknown_tool(self, client: TestClient):
        payload = {"arguments": {}} # Dummy args
        response = client.post("/call_tool/unknown_tool_name", json=payload)
        assert response.status_code == 404 # As defined in mcp_server.py router
        data = response.json()
        assert data["detail"] == "Unknown tool: unknown_tool_name"

# To run these tests:
# Ensure you are in the `examples/sequential-thinking-python` directory.
# Run `pytest` or `python -m pytest`.
# You might need to set PYTHONPATH=. or ensure your project structure is recognized.
# Example: PYTHONPATH=. pytest tests/app/test_mcp_server.py
# Or from project root: pytest examples/sequential-thinking-python/tests/app/test_mcp_server.py
