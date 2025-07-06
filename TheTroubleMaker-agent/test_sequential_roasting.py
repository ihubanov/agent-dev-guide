#!/usr/bin/env python3

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tools import _search_leak_impl, thinking_server

async def test_sequential_thinking_roasting():
    """Test the sequential thinking process in roasting"""
    print("🧠 Testing Sequential Thinking Roasting Process 🧠")
    print("=" * 60)
    
    # Test with a sample email
    test_email = "test@example.com"
    
    print(f"Testing sequential thinking roast for: {test_email}")
    print("-" * 40)
    
    try:
        # Call the search function that now uses sequential thinking
        result = await _search_leak_impl(test_email, 100, "en", "json")
        
        # Parse the result
        try:
            parsed_result = json.loads(result)
            
            # Check if automatic roast is included
            if "automatic_roast" in parsed_result:
                roast_data = parsed_result["automatic_roast"]
                print("✅ Sequential thinking roast found!")
                print(f"🎭 Roast Style: {roast_data.get('style', 'unknown')}")
                print(f"📊 Breach Count: {roast_data.get('breach_count', 0)}")
                print(f"🗄️ Databases: {len(roast_data.get('databases', []))}")
                
                # Show the sequential thinking process
                print("\n🧠 SEQUENTIAL THINKING PROCESS:")
                print("-" * 30)
                
                # Display the thought history from the thinking server
                print(f"Total thoughts processed: {len(thinking_server.thought_history)}")
                print(f"Branches created: {len(thinking_server.branches)}")
                
                for i, thought in enumerate(thinking_server.thought_history):
                    print(f"\n💭 Thought {i+1}:")
                    print(f"   Content: {thought.get('thought', 'No content')}")
                    print(f"   Number: {thought.get('thoughtNumber', 'N/A')}")
                    print(f"   Total: {thought.get('totalThoughts', 'N/A')}")
                    print(f"   Next needed: {thought.get('nextThoughtNeeded', 'N/A')}")
                
                print("\n🔥 FINAL ROAST:")
                print("-" * 20)
                print(roast_data.get('content', 'No roast content found'))
                print("-" * 20)
                
            else:
                print("❌ No sequential thinking roast found in response")
                print("Response structure:")
                print(json.dumps(parsed_result, indent=2)[:500] + "...")
                
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON")
            print("Raw response:")
            print(result[:500] + "...")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Sequential thinking roasting test completed!")

if __name__ == "__main__":
    asyncio.run(test_sequential_thinking_roasting()) 