#!/usr/bin/env python3
"""
Test script to verify location analysis functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from tools import analyze_location_data

async def test_location_analysis():
    """Test location analysis functionality"""
    print("🔍 Testing Location Analysis...")
    
    # Test with a generic email
    test_email = "test@example.com"
    
    print(f"\n📧 Testing location analysis for: {test_email}")
    
    try:
        # Call the location analysis function
        result = await analyze_location_data(test_email, 100)
        
        print(f"\n📄 Analysis Length: {len(result)} characters")
        print(f"📄 Analysis Preview: {result[:200]}...")
        
        # Check for key sections
        sections_to_check = [
            "🔮🔮🔮 LOCATION INTELLIGENCE REPORT 🔮🔮🔮",
            "🌍 YOUR LOCATION SECRETS REVEALED 🌍",
            "🔍 SHADOW IP ADDRESSES",
            "🌍 LOCATION RISK SCORE",
            "🔮 WHAT I'M TELLING YOU"
        ]
        
        print(f"\n✅ Checking for required sections:")
        for section in sections_to_check:
            if section in result:
                print(f"   ✅ Found: {section}")
            else:
                print(f"   ❌ Missing: {section}")
        
        print(f"\n✅ Location analysis test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_location_analysis()) 