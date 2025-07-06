#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.tools import roast_user_with_sequential_thinking

async def test_roasting():
    """Test the roasting functionality"""
    print("🔥 Testing TroubleMaker Roasting Functionality 🔥")
    print("=" * 50)
    
    # Test with a sample email (you can replace this with a real email for testing)
    test_email = "test@example.com"
    
    print(f"Testing roast for: {test_email}")
    print("-" * 30)
    
    # Test different roast styles
    roast_styles = ["friendly", "savage", "dad_jokes", "tech_nerd", "random"]
    
    for style in roast_styles:
        print(f"\n🎭 Testing {style.upper()} roast style:")
        print("-" * 20)
        
        try:
            roast_result = await roast_user_with_sequential_thinking(
                email=test_email,
                roast_style=style,
                include_location=True
            )
            print(roast_result)
        except Exception as e:
            print(f"❌ Error with {style} roast: {str(e)}")
    
    print("\n" + "=" * 50)
    print("✅ Roasting test completed!")

if __name__ == "__main__":
    asyncio.run(test_roasting()) 