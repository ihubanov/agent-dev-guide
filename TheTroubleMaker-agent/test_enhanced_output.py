#!/usr/bin/env python3
"""
Test script to verify enhanced breach report output
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from tools import _search_leak_impl

async def test_enhanced_output():
    """Test the enhanced breach report output"""
    print("🔍 Testing Enhanced Breach Report Output...")
    
    # Test with a generic email
    test_email = "test@example.com"
    
    print(f"\n📧 Testing breach report for: {test_email}")
    
    try:
        # Call the search implementation
        result = await _search_leak_impl(test_email, 100, "en", "json")
        
        print(f"\n📄 Report Length: {len(result)} characters")
        print(f"📄 Report Preview: {result[:200]}...")
        
        # Check for key sections
        sections_to_check = [
            "🔮🔮🔮 WHAT I FOUND ON YOU 🔮🔮🔮",
            "🔥 YOUR COMPROMISED DATA",
            "🎯 WHAT I DISCOVERED ABOUT YOU",
            "💎 YOUR DEEPEST SECRETS REVEALED",
            "🚨 YOUR PERSONAL THREAT LEVEL",
            "🔮 WHAT I'M TELLING YOU"
        ]
        
        print(f"\n✅ Checking for required sections:")
        for section in sections_to_check:
            if section in result:
                print(f"   ✅ Found: {section}")
            else:
                print(f"   ❌ Missing: {section}")
        
        print(f"\n✅ Enhanced output test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_output()) 