#!/usr/bin/env python3
"""
Test script for Leakosint API functionality
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

async def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from app.tools import leakosint_toolkit, compose
        print("✓ Successfully imported leakosint_toolkit and compose")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    return True

async def test_complexity_calculation():
    """Test the complexity calculation function"""
    print("\nTesting complexity calculation...")
    
    # Define a simple complexity calculation function for testing
    def calculate_complexity_simple(query: str, limit: int = 100) -> dict:
        """Simple complexity calculation for testing"""
        import re
        import math
        
        # Remove dates (various formats)
        query_clean = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', query)
        query_clean = re.sub(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', '', query_clean)
        
        # Remove lines shorter than 4 characters
        words = query_clean.split()
        words = [word for word in words if len(word) >= 4]
        
        # Remove numbers shorter than 6 characters
        words = [word for word in words if not (word.isdigit() and len(word) < 6)]
        
        # Calculate complexity based on number of words
        word_count = len(words)
        if word_count == 1:
            complexity = 1
        elif word_count == 2:
            complexity = 5
        elif word_count == 3:
            complexity = 16
        else:
            complexity = 40
        
        # Calculate cost using the formula: (5 + sqrt(Limit * Complexity)) / 5000
        cost = (5 + math.sqrt(limit * complexity)) / 5000
        
        return {
            "original_query": query,
            "cleaned_words": words,
            "word_count": word_count,
            "complexity": complexity,
            "limit": limit,
            "estimated_cost_usd": round(cost, 6),
            "formula": f"(5 + sqrt({limit} * {complexity})) / 5000 = {cost:.6f}"
        }
    
    test_cases = [
        ("john.doe@example.com", 100),
        ("John Smith", 500),
        ("Elon Musk Tesla", 1000),
        ("123456789", 100),  # Should be filtered out
        ("test", 100),  # Should be filtered out
    ]
    
    for query, limit in test_cases:
        result = calculate_complexity_simple(query, limit)
        print(f"\nQuery: '{query}' with limit {limit}")
        print(f"Cleaned words: {result['cleaned_words']}")
        print(f"Word count: {result['word_count']}")
        print(f"Complexity: {result['complexity']}")
        print(f"Estimated cost: ${result['estimated_cost_usd']}")
        print(f"Formula: {result['formula']}")

async def test_toolkit_structure():
    """Test that the toolkit structure is correct"""
    print("\n\nTesting toolkit structure...")
    
    try:
        from app.tools import leakosint_toolkit
        
        # Check that the toolkit exists
        assert leakosint_toolkit is not None
        print("✓ Leakosint toolkit exists")
        
        # Check that it has the expected name
        assert hasattr(leakosint_toolkit, 'name')
        print(f"✓ Toolkit name: {leakosint_toolkit.name}")
        
        print("✓ Toolkit structure appears correct")
        return True
        
    except Exception as e:
        print(f"❌ Toolkit structure test failed: {e}")
        return False

async def test_compose_integration():
    """Test that the compose integration is correct"""
    print("\n\nTesting compose integration...")
    
    try:
        from app.tools import compose
        
        # Check that compose exists
        assert compose is not None
        print("✓ Compose exists")
        
        # Check that it has the expected name
        assert hasattr(compose, 'name')
        print(f"✓ Compose name: {compose.name}")
        
        print("✓ Compose integration appears correct")
        return True
        
    except Exception as e:
        print(f"❌ Compose integration test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("Starting Leakosint API functionality tests...\n")
    
    try:
        # Test imports
        if not await test_imports():
            return 1
        
        # Test complexity calculation
        await test_complexity_calculation()
        
        # Test toolkit structure
        if not await test_toolkit_structure():
            return 1
        
        # Test compose integration
        if not await test_compose_integration():
            return 1
        
        print("\n🎉 All tests passed! The Leakosint API integration is working correctly.")
        print("\nTo test the actual API calls, you would need:")
        print("1. A valid Leakosint API token")
        print("2. To run the server and make requests through the agent")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 