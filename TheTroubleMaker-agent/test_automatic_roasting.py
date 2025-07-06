#!/usr/bin/env python3

import asyncio
import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tools import _search_leak_impl

async def test_automatic_roasting():
    """Test the automatic roasting functionality in OSINT search"""
    print("🔥 Testing Automatic Roasting in OSINT Search 🔥")
    print("=" * 60)
    
    # Test with a sample email (you can replace this with a real email for testing)
    test_email = "test@example.com"
    
    print(f"Testing automatic roast for: {test_email}")
    print("-" * 40)
    
    try:
        # Call the search function that now includes automatic roasting
        result = await _search_leak_impl(test_email, 100, "en", "json")
        
        # Parse the result
        try:
            parsed_result = json.loads(result)
            
            # Check if automatic roast is included
            if "automatic_roast" in parsed_result:
                roast_data = parsed_result["automatic_roast"]
                print("✅ Automatic roast found!")
                print(f"🎭 Roast Style: {roast_data.get('style', 'unknown')}")
                print(f"📊 Breach Count: {roast_data.get('breach_count', 0)}")
                print(f"🗄️ Databases: {len(roast_data.get('databases', []))}")
                print("\n🔥 THE ROAST:")
                print("-" * 20)
                print(roast_data.get('content', 'No roast content found'))
                print("-" * 20)
                
                # Check if location roasting was included
                if "🌍" in roast_data.get('content', ''):
                    print("✅ Location-based roasting included!")
                else:
                    print("ℹ️ No location data available for roasting")
                    
            else:
                print("❌ No automatic roast found in response")
                print("Response structure:")
                print(json.dumps(parsed_result, indent=2)[:500] + "...")
                
        except json.JSONDecodeError:
            print("❌ Response is not valid JSON")
            print("Raw response:")
            print(result[:500] + "...")
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Automatic roasting test completed!")

if __name__ == "__main__":
    asyncio.run(test_automatic_roasting()) 