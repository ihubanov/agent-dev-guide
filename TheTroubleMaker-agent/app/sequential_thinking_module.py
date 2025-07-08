#!/usr/bin/env python3

import json
import os
import sys
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from termcolor import colored
import logging

logger = logging.getLogger(__name__)

# Environment variable to disable thought logging
DISABLE_THOUGHT_LOGGING = os.getenv("DISABLE_THOUGHT_LOGGING", "false").lower() == "true"


@dataclass
class ThoughtData:
    """Data structure for a single thought in the sequential thinking process"""
    thought: str
    thought_number: int
    total_thoughts: int
    next_thought_needed: bool
    is_revision: Optional[bool] = None
    revises_thought: Optional[int] = None
    branch_from_thought: Optional[int] = None
    branch_id: Optional[str] = None
    needs_more_thoughts: Optional[bool] = None


class SequentialThinkingModule:
    """
    A modular implementation of sequential thinking that can be called by functions.
    This is an exact implementation of the sequential thinking functionality from the Python example.
    """
    
    def __init__(self, disable_logging: Optional[bool] = None):
        """
        Initialize the sequential thinking module.
        
        Args:
            disable_logging: Override the DISABLE_THOUGHT_LOGGING environment variable
        """
        self.thought_history: List[ThoughtData] = []
        self.branches: Dict[str, List[ThoughtData]] = {}
        self.disable_thought_logging = disable_logging if disable_logging is not None else DISABLE_THOUGHT_LOGGING

    def _validate_thought_data(self, input_data: Dict[str, Any]) -> ThoughtData:
        """
        Validate and convert input data to ThoughtData.
        
        Args:
            input_data: Dictionary containing thought data
            
        Returns:
            ThoughtData object
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        data = input_data

        if not data.get("thought") or not isinstance(data["thought"], str):
            raise ValueError("Invalid thought: must be a string")
        if not data.get("thoughtNumber") or not isinstance(data["thoughtNumber"], int):
            raise ValueError("Invalid thoughtNumber: must be a number")
        if not data.get("totalThoughts") or not isinstance(data["totalThoughts"], int):
            raise ValueError("Invalid totalThoughts: must be a number")
        if not isinstance(data.get("nextThoughtNeeded"), bool):
            raise ValueError("Invalid nextThoughtNeeded: must be a boolean")

        return ThoughtData(
            thought=data["thought"],
            thought_number=data["thoughtNumber"],
            total_thoughts=data["totalThoughts"],
            next_thought_needed=data["nextThoughtNeeded"],
            is_revision=data.get("isRevision"),
            revises_thought=data.get("revisesThought"),
            branch_from_thought=data.get("branchFromThought"),
            branch_id=data.get("branchId"),
            needs_more_thoughts=data.get("needsMoreThoughts"),
        )

    def _format_thought(self, thought_data: ThoughtData) -> str:
        """
        Format a thought for logging with colored output.
        
        Args:
            thought_data: The thought data to format
            
        Returns:
            Formatted string for logging
        """
        thought_number = thought_data.thought_number
        total_thoughts = thought_data.total_thoughts
        thought = thought_data.thought
        is_revision = thought_data.is_revision
        revises_thought = thought_data.revises_thought
        branch_from_thought = thought_data.branch_from_thought
        branch_id = thought_data.branch_id

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
            context = ""

        header = f"{prefix} {thought_number}/{total_thoughts}{context}"
        border = "─" * (max(len(header), len(thought)) + 4)

        return f"""
┌{border}┐
│ {header} │
├{border}┤
│ {thought.ljust(len(border) - 2)} │
└{border}┘"""

    def process_thought(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single thought and return the response.
        
        Args:
            input_data: Dictionary containing thought data
            
        Returns:
            Dictionary with response data or error information
        """
        try:
            validated_input = self._validate_thought_data(input_data)

            # Update total thoughts if current thought number is higher
            if validated_input.thought_number > validated_input.total_thoughts:
                validated_input.total_thoughts = validated_input.thought_number
                logger.debug(f"🔧 [THINKING DEBUG] Updated total_thoughts from {validated_input.total_thoughts - 1} to {validated_input.total_thoughts}")

            # Add to thought history
            self.thought_history.append(validated_input)
            logger.debug(f"🔧 [THINKING DEBUG] Added thought {validated_input.thought_number}/{validated_input.total_thoughts} to history. Total thoughts: {len(self.thought_history)}")

            # Handle branching
            if validated_input.branch_from_thought and validated_input.branch_id:
                if validated_input.branch_id not in self.branches:
                    self.branches[validated_input.branch_id] = []
                self.branches[validated_input.branch_id].append(validated_input)
                logger.debug(f"🔧 [THINKING DEBUG] Added thought to branch {validated_input.branch_id}")

            # Log the thought if logging is enabled
            if not self.disable_thought_logging:
                formatted_thought = self._format_thought(validated_input)
                print(formatted_thought, file=sys.stderr, flush=True)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "thoughtNumber": validated_input.thought_number,
                                "totalThoughts": validated_input.total_thoughts,
                                "nextThoughtNeeded": validated_input.next_thought_needed,
                                "branches": list(self.branches.keys()),
                                "thoughtHistoryLength": len(self.thought_history),
                            },
                            indent=2
                        ),
                    }
                ]
            }
        except Exception as error:
            logger.error(f"Error processing thought: {error}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(
                            {
                                "error": str(error),
                                "status": "failed",
                            },
                            indent=2
                        ),
                    }
                ],
                "isError": True,
            }

    def get_thought_history(self) -> List[ThoughtData]:
        """
        Get the complete thought history.
        
        Returns:
            List of ThoughtData objects
        """
        return self.thought_history.copy()

    def get_branches(self) -> Dict[str, List[ThoughtData]]:
        """
        Get all branches.
        
        Returns:
            Dictionary of branch IDs to lists of ThoughtData
        """
        return self.branches.copy()

    def clear_history(self) -> None:
        """Clear all thought history and branches."""
        self.thought_history.clear()
        self.branches.clear()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current thinking state.
        
        Returns:
            Dictionary with summary information
        """
        return {
            "total_thoughts": len(self.thought_history),
            "branches": list(self.branches.keys()),
            "branch_count": len(self.branches),
            "latest_thought_number": max([t.thought_number for t in self.thought_history]) if self.thought_history else 0,
            "is_complete": not any(t.next_thought_needed for t in self.thought_history[-1:]) if self.thought_history else True
        }


# Function interface for easy calling
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
) -> Union[str, Dict[str, Any]]:
    """
    Process a sequential thought using the provided or default thinking module.
    
    Args:
        thought: The thought content
        next_thought_needed: Whether another thought is needed
        thought_number: Current thought number
        total_thoughts: Estimated total thoughts needed
        is_revision: Whether this revises previous thinking
        revises_thought: Which thought is being reconsidered
        branch_from_thought: Branching point thought number
        branch_id: Branch identifier
        needs_more_thoughts: If more thoughts are needed
        thinking_module: Optional SequentialThinkingModule instance (creates new one if None)
        
    Returns:
        JSON string response or error dictionary
    """
    if thinking_module is None:
        thinking_module = SequentialThinkingModule()
    
    input_data = {
        "thought": thought,
        "nextThoughtNeeded": next_thought_needed,
        "thoughtNumber": thought_number,
        "totalThoughts": total_thoughts,
        "isRevision": is_revision,
        "revisesThought": revises_thought,
        "branchFromThought": branch_from_thought,
        "branchId": branch_id,
        "needsMoreThoughts": needs_more_thoughts,
    }
    
    result = thinking_module.process_thought(input_data)
    
    if result.get("isError"):
        return result["content"][0]["text"]
    
    return result["content"][0]["text"]


# Convenience function for creating a new thinking session
def create_thinking_session(disable_logging: Optional[bool] = None) -> SequentialThinkingModule:
    """
    Create a new sequential thinking session.
    
    Args:
        disable_logging: Whether to disable thought logging
        
    Returns:
        New SequentialThinkingModule instance
    """
    return SequentialThinkingModule(disable_logging=disable_logging)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    thinking = create_thinking_session()
    
    # Process some thoughts
    result1 = process_sequential_thought(
        thought="I need to analyze this problem step by step",
        next_thought_needed=True,
        thought_number=1,
        total_thoughts=3,
        thinking_module=thinking
    )
    print("Result 1:", result1)
    
    result2 = process_sequential_thought(
        thought="Actually, I think I need to revise my approach",
        next_thought_needed=True,
        thought_number=2,
        total_thoughts=4,  # Updated estimate
        is_revision=True,
        revises_thought=1,
        thinking_module=thinking
    )
    print("Result 2:", result2)
    
    result3 = process_sequential_thought(
        thought="I've reached a conclusion",
        next_thought_needed=False,
        thought_number=3,
        total_thoughts=4,
        thinking_module=thinking
    )
    print("Result 3:", result3)
    
    # Get summary
    summary = thinking.get_summary()
    print("Summary:", summary) 