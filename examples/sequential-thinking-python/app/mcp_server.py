import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError
from typing import List, Dict, Any, Optional, Union
from termcolor import colored
import os

# Environment variable to disable thought logging
DISABLE_THOUGHT_LOGGING = os.getenv("DISABLE_THOUGHT_LOGGING", "false").lower() == "true"

class ThoughtDataInput(BaseModel):
    thought: str
    thought_number: int = Field(..., alias="thoughtNumber")
    total_thoughts: int = Field(..., alias="totalThoughts")
    next_thought_needed: bool = Field(..., alias="nextThoughtNeeded")
    is_revision: Optional[bool] = Field(None, alias="isRevision")
    revises_thought: Optional[int] = Field(None, alias="revisesThought")
    branch_from_thought: Optional[int] = Field(None, alias="branchFromThought")
    branch_id: Optional[str] = Field(None, alias="branchId")
    needs_more_thoughts: Optional[bool] = Field(None, alias="needsMoreThoughts")

    class Config:
        populate_by_name = True


class ToolOutputContent(BaseModel):
    type: str
    text: str

class ToolOutput(BaseModel):
    content: List[ToolOutputContent]
    is_error: Optional[bool] = False


class SequentialThinkingServer:
    def __init__(self):
        self.thought_history: List[Dict[str, Any]] = []
        self.branches: Dict[str, List[Dict[str, Any]]] = {}
        self.disable_thought_logging = DISABLE_THOUGHT_LOGGING

    def _validate_thought_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Pydantic model handles validation
            validated_model = ThoughtDataInput(**input_data)
            return validated_model.model_dump(by_alias=True)
        except ValidationError as e:
            raise ValueError(f"Invalid input: {e.errors()}")

    def _format_thought(self, thought_data: Dict[str, Any]) -> str:
        thought_number = thought_data.get("thoughtNumber", 0)
        total_thoughts = thought_data.get("totalThoughts", 0)
        thought_text = thought_data.get("thought", "")
        is_revision = thought_data.get("isRevision", False)
        revises_thought = thought_data.get("revisesThought")
        branch_from_thought = thought_data.get("branchFromThought")
        branch_id = thought_data.get("branchId")

        prefix = ""
        context = ""

        if is_revision:
            prefix = colored("🔄 Revision", "yellow")
            context = f" (revising thought {revises_thought})"
        elif branch_from_thought:
            prefix = colored("🌿 Branch", "green")
            context = f" (from thought {branch_from_thought}, ID: {branch_id})"
        else:
            prefix = colored("💭 Thought", "blue")

        header = f"{prefix} {thought_number}/{total_thoughts}{context}"
        # Ensure thought_text is a string before calling len() or pad_end()
        thought_text_str = str(thought_text)
        border_len = max(len(header) - (len(prefix) - len(prefix.encode('utf-8'))), len(thought_text_str)) + 4 # Adjust for escape codes

        # Crude way to get visible length of colored string
        # For more accuracy, a library that handles ANSI escape codes might be needed
        try:
            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            header_visible_len = len(ansi_escape.sub('', header))
            border_len = max(header_visible_len, len(thought_text_str)) + 4
        except ImportError:
            pass # Fallback to previous border_len if regex not available or fails

        border = "─" * border_len

        # Pad header to align with border, considering color codes
        # This is tricky with ANSI codes, this is a simplification
        header_padding = border_len - header_visible_len -2
        padded_header = f"{header}{' ' * header_padding if header_padding > 0 else ''}"


        return f"\n┌{border}┐\n│ {padded_header} │\n├{border}┤\n│ {thought_text_str.ljust(border_len -2)} │\n└{border}┘"

    def process_thought(self, input_data: Dict[str, Any]) -> ToolOutput:
        try:
            validated_input = self._validate_thought_data(input_data)

            if validated_input["thoughtNumber"] > validated_input["totalThoughts"]:
                validated_input["totalThoughts"] = validated_input["thoughtNumber"]

            self.thought_history.append(validated_input)

            if validated_input.get("branchFromThought") and validated_input.get("branchId"):
                branch_id = validated_input["branchId"]
                if branch_id not in self.branches:
                    self.branches[branch_id] = []
                self.branches[branch_id].append(validated_input)

            if not self.disable_thought_logging:
                formatted_thought = self._format_thought(validated_input)
                print(formatted_thought, flush=True) # Use print for stderr-like behavior in servers

            return ToolOutput(content=[
                ToolOutputContent(type="text", text=json.dumps(
                    {
                        "thoughtNumber": validated_input["thoughtNumber"],
                        "totalThoughts": validated_input["totalThoughts"],
                        "nextThoughtNeeded": validated_input["nextThoughtNeeded"],
                        "branches": list(self.branches.keys()),
                        "thoughtHistoryLength": len(self.thought_history),
                    },
                    indent=2
                ))
            ])
        except Exception as error:
            return ToolOutput(content=[
                ToolOutputContent(type="text", text=json.dumps(
                    {
                        "error": str(error),
                        "status": "failed",
                    },
                    indent=2
                ))
            ], is_error=True)

# Tool Definition (as it was in TypeScript, for reference and use in OpenAI API call)
SEQUENTIAL_THINKING_TOOL_DEF = {
    "type": "function",
    "function": {
        "name": "sequentialthinking",
        "description": """A detailed tool for dynamic and reflective problem-solving through thoughts.
This tool helps analyze problems through a flexible thinking process that can adapt and evolve.
Each thought can build on, question, or revise previous insights as understanding deepens.

When to use this tool:
- Breaking down complex problems into steps
- Planning and design with room for revision
- Analysis that might need course correction
- Problems where the full scope might not be clear initially
- Problems that require a multi-step solution
- Tasks that need to maintain context over multiple steps
- Situations where irrelevant information needs to be filtered out

Key features:
- You can adjust total_thoughts up or down as you progress
- You can question or revise previous thoughts
- You can add more thoughts even after reaching what seemed like the end
- You can express uncertainty and explore alternative approaches
- Not every thought needs to build linearly - you can branch or backtrack
- Generates a solution hypothesis
- Verifies the hypothesis based on the Chain of Thought steps
- Repeats the process until satisfied
- Provides a correct answer

Parameters explained:
- thought: Your current thinking step, which can include:
* Regular analytical steps
* Revisions of previous thoughts
* Questions about previous decisions
* Realizations about needing more analysis
* Changes in approach
* Hypothesis generation
* Hypothesis verification
- next_thought_needed: True if you need more thinking, even if at what seemed like the end
- thought_number: Current number in sequence (can go beyond initial total if needed)
- total_thoughts: Current estimate of thoughts needed (can be adjusted up/down)
- is_revision: A boolean indicating if this thought revises previous thinking
- revises_thought: If is_revision is true, which thought number is being reconsidered
- branch_from_thought: If branching, which thought number is the branching point
- branch_id: Identifier for the current branch (if any)
- needs_more_thoughts: If reaching end but realizing more thoughts needed

You should:
1. Start with an initial estimate of needed thoughts, but be ready to adjust
2. Feel free to question or revise previous thoughts
3. Don't hesitate to add more thoughts if needed, even at the "end"
4. Express uncertainty when present
5. Mark thoughts that revise previous thinking or branch into new paths
6. Ignore information that is irrelevant to the current step
7. Generate a solution hypothesis when appropriate
8. Verify the hypothesis based on the Chain of Thought steps
9. Repeat the process until satisfied with the solution
10. Provide a single, ideally correct answer as the final output
11. Only set next_thought_needed to false when truly done and a satisfactory answer is reached""",
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "Your current thinking step"},
                "nextThoughtNeeded": {"type": "boolean", "description": "Whether another thought step is needed"},
                "thoughtNumber": {"type": "integer", "description": "Current thought number", "minimum": 1},
                "totalThoughts": {"type": "integer", "description": "Estimated total thoughts needed", "minimum": 1},
                "isRevision": {"type": "boolean", "description": "Whether this revises previous thinking"},
                "revisesThought": {"type": "integer", "description": "Which thought is being reconsidered", "minimum": 1},
                "branchFromThought": {"type": "integer", "description": "Branching point thought number", "minimum": 1},
                "branchId": {"type": "string", "description": "Branch identifier"},
                "needsMoreThoughts": {"type": "boolean", "description": "If more thoughts are needed"},
            },
            "required": ["thought", "nextThoughtNeeded", "thoughtNumber", "totalThoughts"],
        },
    }
}


# FastAPI Router
router = APIRouter()
thinking_server_instance = SequentialThinkingServer()

class CallToolRequest(BaseModel):
    # Mimicking structure from CallToolRequestSchema in TS
    # name: str # This will be part of the path
    arguments: Dict[str, Any]


@router.post("/call_tool/{tool_name}")
async def call_tool(tool_name: str, request: CallToolRequest) -> ToolOutput:
    if tool_name == "sequentialthinking":
        return thinking_server_instance.process_thought(request.arguments)
    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

# This function is for providing the tool definition to the OpenAI client part
def list_tools() -> List[Dict[str, Any]]:
    return [SEQUENTIAL_THINKING_TOOL_DEF]

if __name__ == "__main__":
    # Example usage for testing the server logic directly
    server = SequentialThinkingServer()
    test_thought_1 = {
        "thought": "This is my first thought.",
        "thoughtNumber": 1,
        "totalThoughts": 3,
        "nextThoughtNeeded": True
    }
    print("Processing test_thought_1:")
    output1 = server.process_thought(test_thought_1)
    print(output1.model_dump_json(indent=2))

    test_thought_2_revises = {
        "thought": "Actually, let me revise my first thought.",
        "thoughtNumber": 2,
        "totalThoughts": 3,
        "nextThoughtNeeded": True,
        "isRevision": True,
        "revisesThought": 1
    }
    print("\nProcessing test_thought_2_revises:")
    output2 = server.process_thought(test_thought_2_revises)
    print(output2.model_dump_json(indent=2))

    test_thought_3_branch = {
        "thought": "Let's explore a different path from thought 1.",
        "thoughtNumber": 3, # This might be thought 1 on a new branch logically
        "totalThoughts": 3, # Or total thoughts for this branch
        "nextThoughtNeeded": True,
        "branchFromThought": 1,
        "branchId": "branch_A"
    }
    print("\nProcessing test_thought_3_branch:")
    output3 = server.process_thought(test_thought_3_branch)
    print(output3.model_dump_json(indent=2))

    print("\nFinal thought history:")
    for item in server.thought_history:
        print(item)
    print("\nFinal branches:")
    for branch_id, thoughts in server.branches.items():
        print(f"Branch {branch_id}: {thoughts}")

    # Test validation error
    test_invalid_thought = {
        "thought": "This is invalid.",
        # "thoughtNumber": 1, # Missing required field
        "totalThoughts": 1,
        "nextThoughtNeeded": True
    }
    print("\nProcessing invalid thought:")
    output_invalid = server.process_thought(test_invalid_thought)
    print(output_invalid.model_dump_json(indent=2))

    # To run this file directly for testing: python examples/sequential-thinking-python/app/mcp_server.py
    # To run with Uvicorn (once server.py is created): uvicorn server:app --reload --port 8000
    print(colored("\nTo run the FastAPI server, create server.py and run: uvicorn server:app --reload --port 8000", "cyan"))
