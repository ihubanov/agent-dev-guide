#!/usr/bin/env python3
"""
Debug test script for Leakosint API calls
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_leakosint_api():
    """Test the Leakosint API calls with debug prints"""
    
    print("🔧 [DEBUG] Starting Leakosint API debug test...")
    print(f"🔧 [DEBUG] Current working directory: {os.getcwd()}")
    print(f"🔧 [DEBUG] Environment variables:")
    print(f"   - LEAKOSINT_API_KEY: {'✓ Set' if os.getenv('LEAKOSINT_API_KEY') else '✗ Not set'}")
    print(f"   - PORT: {os.getenv('PORT', 'Not set')}")
    print(f"   - HOST: {os.getenv('HOST', 'Not set')}")
    
    try:
        # Import the settings to check API key
        from app.configs import settings
        print(f"🔑 [DEBUG] Settings API key: {'✓ Present' if settings.leakosint_api_key else '✗ Missing'}")
        
        # Import the private implementation functions directly
        from app.tools import _calculate_complexity_impl, _search_leak_impl, _batch_search_leak_impl
        print("✅ [DEBUG] Successfully imported Leakosint private implementation functions")
        
        # Test complexity calculation first
        print("\n🧮 [DEBUG] Testing complexity calculation...")
        complexity_result = await _calculate_complexity_impl("test@example.com", 100)
        print(f"📊 [DEBUG] Complexity result: {complexity_result}")
        
        # Test single search (this will show debug prints)
        print("\n🔍 [DEBUG] Testing single search...")
        search_result = await _search_leak_impl("test@example.com", 100)
        print(f"📊 [DEBUG] Search result: {search_result}")
        
        # Test batch search (this will show debug prints)
        print("\n🔍 [DEBUG] Testing batch search...")
        batch_result = await _batch_search_leak_impl(["test@example.com", "john@example.com"], 100)
        print(f"📊 [DEBUG] Batch search result: {batch_result}")
        
    except Exception as e:
        print(f"❌ [DEBUG] Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_leakosint_api()) 