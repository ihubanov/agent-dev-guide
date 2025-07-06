#!/usr/bin/env python3
"""
Test script to verify agent consistency in handling data leak requests.
This will help identify if the agent is being inconsistent in its responses.
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from tools import _search_leak_impl
except ImportError:
    # Try alternative import path
    sys.path.append(os.path.dirname(__file__))
    from app.tools import _search_leak_impl

async def test_agent_consistency():
    """Test the agent's consistency in handling data leak requests"""
    
    print("🔍 Testing Agent Consistency for Data Leak Requests")
    print("=" * 60)
    
    # Test email
    test_email = "sniffski@gmail.com"
    
    print(f"\n📧 Testing with email: {test_email}")
    print("-" * 40)
    
    try:
        # Call the implementation function directly to see what it returns
        print("🔧 Calling _search_leak_impl function directly...")
        result = await _search_leak_impl(test_email, limit=100, lang="en", report_type="json")
        
        print(f"\n✅ Function call successful!")
        print(f"📊 Result type: {type(result).__name__}")
        print(f"📏 Result length: {len(result)}")
        print(f"🔍 Result preview: {repr(result[:500])}")
        
        # Check if result contains expected data
        if "breach" in result.lower() or "password" in result.lower() or "email" in result.lower():
            print("✅ Result contains expected breach data")
        else:
            print("⚠️ Result may not contain expected breach data")
            
        # Check for specific patterns
        if "sniffski@gmail.com" in result:
            print("✅ Result contains the test email")
        else:
            print("⚠️ Result does not contain the test email")
            
        if "password" in result.lower():
            print("✅ Result contains password information")
        else:
            print("⚠️ Result does not contain password information")
            
        if "ip" in result.lower():
            print("✅ Result contains IP information")
        else:
            print("⚠️ Result does not contain IP information")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        print(f"❌ Error type: {type(e).__name__}")
        return False
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_agent_consistency()) 