#!/usr/bin/env python3

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tools import sequential_thinking_tool

async def test_proper_sequential_thinking():
    """Test the proper use of sequential thinking tool (like the original implementation)"""
    print("🧠 Testing Proper Sequential Thinking Usage 🧠")
    print("=" * 60)
    
    print("This demonstrates how the LLM should use the sequential thinking tool:")
    print("- Each thought is generated dynamically by the LLM")
    print("- No hardcoded thoughts")
    print("- Thoughts can be revised or branched")
    print("- The process is flexible and adaptive")
    print("\n" + "-" * 40)
    
    # Example of how the LLM would use the tool
    print("Example: LLM analyzing data breach findings for roasting")
    print("\n1. First thought - Initial analysis:")
    
    # Simulate LLM calling the tool
    result1 = await sequential_thinking_tool(
        thought="I need to analyze this user's data breach findings. Let me start by examining the scope of the breach - how many databases were affected and what types of data were exposed.",
        nextThoughtNeeded=True,
        thoughtNumber=1,
        totalThoughts=5
    )
    print(f"Tool response: {result1}")
    
    print("\n2. Second thought - Deepening analysis:")
    result2 = await sequential_thinking_tool(
        thought="Now I can see the specific databases and data types. This gives me material for roasting. I should identify the most humorous aspects while being informative about security risks.",
        nextThoughtNeeded=True,
        thoughtNumber=2,
        totalThoughts=5
    )
    print(f"Tool response: {result2}")
    
    print("\n3. Third thought - Style determination:")
    result3 = await sequential_thinking_tool(
        thought="Based on the breach severity, I should choose an appropriate roast style. The number of breaches and types of data exposed will guide my tone - friendly for minor breaches, savage for major ones.",
        nextThoughtNeeded=True,
        thoughtNumber=3,
        totalThoughts=5
    )
    print(f"Tool response: {result3}")
    
    print("\n4. Fourth thought - Personalization:")
    result4 = await sequential_thinking_tool(
        thought="I need to personalize the roast based on the specific data found. Location data, password patterns, and breach types all provide unique roasting opportunities.",
        nextThoughtNeeded=True,
        thoughtNumber=4,
        totalThoughts=5
    )
    print(f"Tool response: {result4}")
    
    print("\n5. Final thought - Crafting the roast:")
    result5 = await sequential_thinking_tool(
        thought="Perfect! I have all the material I need. Time to craft a personalized roast that's both hilarious and informative. The user needs to know their data is out there, but I'll make them laugh about it while providing security advice.",
        nextThoughtNeeded=False,
        thoughtNumber=5,
        totalThoughts=5
    )
    print(f"Tool response: {result5}")
    
    print("\n" + "=" * 60)
    print("✅ Proper sequential thinking demonstration completed!")
    print("\nKey points:")
    print("- Each thought is generated dynamically by the LLM")
    print("- The tool processes and validates each thought")
    print("- Thoughts can be revised or branched as needed")
    print("- The process is flexible and adaptive")

if __name__ == "__main__":
    asyncio.run(test_proper_sequential_thinking()) 