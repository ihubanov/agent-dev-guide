# 🧠 Modular Sequential Thinking Implementation

This document explains how to use the modular sequential thinking implementation that can be called by functions. This is an exact implementation of the sequential thinking functionality from the Python example, but made modular and reusable.

## 📁 Files

- `app/sequential_thinking_module.py` - The main modular implementation
- `test_sequential_thinking.py` - Test script demonstrating usage
- `examples/sequential_thinking_examples.py` - Various usage examples

## 🚀 Quick Start

### Basic Usage

```python
from app.sequential_thinking_module import process_sequential_thought, create_thinking_session

# Create a thinking session
thinking = create_thinking_session()

# Process a thought
result = process_sequential_thought(
    thought="I need to analyze this problem step by step.",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=3,
    thinking_module=thinking
)

print(result)
```

### Function Interface (No Module Instance)

```python
from app.sequential_thinking_module import process_sequential_thought

# Use the function directly (creates its own module instance)
result = process_sequential_thought(
    thought="This is a standalone thought.",
    next_thought_needed=False,
    thought_number=1,
    total_thoughts=1
)

print(result)
```

## 🔧 API Reference

### `SequentialThinkingModule`

The main class for managing sequential thinking sessions.

#### Constructor
```python
SequentialThinkingModule(disable_logging: bool = None)
```

#### Methods

- `process_thought(input_data: Dict[str, Any]) -> Dict[str, Any]` - Process a single thought
- `get_thought_history() -> List[ThoughtData]` - Get complete thought history
- `get_branches() -> Dict[str, List[ThoughtData]]` - Get all branches
- `clear_history() -> None` - Clear all thought history and branches
- `get_summary() -> Dict[str, Any]` - Get summary of current thinking state

### `process_sequential_thought()`

Function interface for processing thoughts.

```python
def process_sequential_thought(
    thought: str,
    next_thought_needed: bool,
    thought_number: int,
    total_thoughts: int,
    is_revision: Optional[bool] = None,
    revises_thought: Optional[int] = None,
    branch_from_thought: Optional[int] = None,
    branch_id: Optional[str] = None,
    needs_more_thoughts: Optional[bool] = None,
    thinking_module: Optional[SequentialThinkingModule] = None
) -> Union[str, Dict[str, Any]]
```

### `create_thinking_session()`

Convenience function for creating new thinking sessions.

```python
def create_thinking_session(disable_logging: bool = None) -> SequentialThinkingModule
```

## 📊 Data Structures

### `ThoughtData`

```python
@dataclass
class ThoughtData:
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: Optional[bool] = None
    revises_thought: Optional[int] = None
    branch_from_thought: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_thoughts: Optional[bool] = None
```

## 🎯 Use Cases

### 1. Basic Sequential Thinking

```python
thinking = create_thinking_session()

# Step 1: Initial analysis
process_sequential_thought(
    thought="I need to understand the problem first.",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=3,
    thinking_module=thinking
)

# Step 2: Break down the problem
process_sequential_thought(
    thought="The problem has three main components.",
    next_thought_needed=True,
    thought_number=2,
    total_thoughts=3,
    thinking_module=thinking
)

# Step 3: Conclusion
process_sequential_thought(
    thought="I have a clear solution now.",
    next_thought_needed=False,
    thought_number=3,
    total_thoughts=3,
    thinking_module=thinking
)
```

### 2. Revision and Branching

```python
thinking = create_thinking_session()

# Initial thought
process_sequential_thought(
    thought="I think the answer is 42.",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=2,
    thinking_module=thinking
)

# Revision
process_sequential_thought(
    thought="Actually, let me reconsider. The answer might be 24.",
    next_thought_needed=True,
    thought_number=2,
    total_thoughts=3,
    is_revision=True,
    revises_thought=1,
    thinking_module=thinking
)

# Branch from original thought
process_sequential_thought(
    thought="Let me explore what if the answer is 42?",
    next_thought_needed=False,
    thought_number=3,
    total_thoughts=3,
    branch_from_thought=1,
    branch_id="explore_42",
    thinking_module=thinking
)
```

### 3. Multiple Sessions

```python
# Create separate sessions for different tasks
math_thinking = create_thinking_session()
cooking_thinking = create_thinking_session()

# Math session
process_sequential_thought(
    thought="I need to solve 2x + 5 = 13",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=2,
    thinking_module=math_thinking
)

# Cooking session
process_sequential_thought(
    thought="I want to make pasta. I need to boil water first.",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=3,
    thinking_module=cooking_thinking
)
```

## 🔍 Integration with TheTroubleMaker Agent

The modular sequential thinking is already integrated into the TheTroubleMaker agent:

### In `app/tools.py`

```python
from app.sequential_thinking_module import SequentialThinkingModule, process_sequential_thought

# Global sequential thinking server instance
thinking_server = SequentialThinkingModule()

@sequential_thinking_toolkit.tool(
    name="sequentialthinking",
    description="...",
    annotations={...}
)
async def sequential_thinking_tool(...) -> str:
    # Use the modular function interface
    result = process_sequential_thought(
        thought=thought,
        next_thought_needed=nextThoughtNeeded,
        thought_number=thoughtNumber,
        total_thoughts=totalThoughts,
        is_revision=isRevision,
        revises_thought=revisesThought,
        branch_from_thought=branchFromThought,
        branch_id=branchId,
        needs_more_thoughts=needsMoreThoughts,
        thinking_module=thinking_server
    )
    
    return result
```

## 🧪 Testing

Run the test script to verify the implementation:

```bash
cd TheTroubleMaker-agent
python test_sequential_thinking.py
```

Run the examples:

```bash
cd TheTroubleMaker-agent
python examples/sequential_thinking_examples.py
```

## ⚙️ Configuration

### Environment Variables

- `DISABLE_THOUGHT_LOGGING`: Set to "true" to disable colored thought logging (default: "false")

### Dependencies

The implementation requires the `termcolor` package for colored output:

```bash
pip install termcolor
```

## 🔄 Migration from Old Implementation

The modular implementation is a drop-in replacement for the old `SequentialThinkingServer` class:

### Before (Old Implementation)
```python
class SequentialThinkingServer:
    def __init__(self):
        self.thought_history = []
        self.branches = {}
        self.disable_thought_logging = False

    def process_thought(self, input_data: dict) -> dict:
        # ... implementation
```

### After (Modular Implementation)
```python
from app.sequential_thinking_module import SequentialThinkingModule

thinking_server = SequentialThinkingModule()
# Use process_sequential_thought() function for processing thoughts
```

## 🎭 Roasting Integration

The sequential thinking module is particularly useful for the roasting functionality:

```python
# Analyze user's data breach for roasting
thinking = create_thinking_session()

process_sequential_thought(
    thought="User has been in 8 data breaches. This is significant exposure.",
    next_thought_needed=True,
    thought_number=1,
    total_thoughts=4,
    thinking_module=thinking
)

process_sequential_thought(
    thought="The breaches include passwords, emails, and personal info. This calls for a savage roast.",
    next_thought_needed=True,
    thought_number=2,
    total_thoughts=4,
    thinking_module=thinking
)

# ... continue with more thoughts

summary = thinking.get_summary()
print("Roasting analysis complete:", summary)
```

## 🚀 Benefits

1. **Modular**: Can be used as a standalone module or integrated into larger systems
2. **Function Interface**: Simple function calls for easy integration
3. **Session Management**: Multiple independent thinking sessions
4. **Error Handling**: Robust error handling and validation
5. **Logging**: Optional colored logging for debugging
6. **Type Safety**: Full type hints for better IDE support
7. **Exact Implementation**: Identical to the Python example implementation

## 📝 License

This implementation follows the same license as the main TheTroubleMaker agent project. 