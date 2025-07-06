#!/usr/bin/env python3
"""
Simple test to verify agent consistency by checking the system prompt and tool configuration.
"""

import os

def test_system_prompt():
    """Test if the system prompt has the correct instructions"""
    
    print("🔍 Testing System Prompt for Consistency")
    print("=" * 50)
    
    # Read the system prompt
    prompt_path = "system_prompt.txt"
    if not os.path.exists(prompt_path):
        print(f"❌ System prompt file not found: {prompt_path}")
        return False
    
    with open(prompt_path, 'r') as f:
        prompt_content = f.read()
    
    print(f"✅ System prompt file found: {prompt_path}")
    print(f"📏 Content length: {len(prompt_content)} characters")
    
    # Check for critical instructions
    critical_checks = [
        ("IMMEDIATELY call the `leakosint_search_leak` tool", "Immediate tool call instruction"),
        ("Do NOT think about whether to do it - just do it", "No thinking instruction"),
        ("ALWAYS show ALL the data found", "Show all data instruction"),
        ("NEVER make up or hide information", "Honesty instruction"),
        ("EXACT TOOL NAME: Use `leakosint_search_leak`", "Exact tool name instruction"),
        ("🔮🔮🔮 WHAT I FOUND ON YOU 🔮🔮🔮", "Dramatic format header"),
        ("The shadows have been talking", "Dramatic style instruction"),
    ]
    
    all_passed = True
    for check_text, description in critical_checks:
        if check_text in prompt_content:
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: Missing")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎯 All critical instructions found in system prompt!")
        return True
    else:
        print("⚠️ Some critical instructions missing from system prompt!")
        return False

def test_tool_configuration():
    """Test if the tool configuration is correct"""
    
    print("\n🔧 Testing Tool Configuration")
    print("=" * 50)
    
    # Check if tools.py exists
    tools_path = "app/tools.py"
    if not os.path.exists(tools_path):
        print(f"❌ Tools file not found: {tools_path}")
        return False
    
    print(f"✅ Tools file found: {tools_path}")
    
    # Read the tools file to check for tool definitions
    with open(tools_path, 'r') as f:
        tools_content = f.read()
    
    # Check for tool definitions
    tool_checks = [
        ("@leakosint_toolkit.tool", "Leakosint toolkit decorator"),
        ("name=\"search_leak\"", "Search leak tool name"),
        ("leakosint_search_leak", "Correct tool name in description"),
    ]
    
    all_passed = True
    for check_text, description in tool_checks:
        if check_text in tools_content:
            print(f"✅ {description}: Found")
        else:
            print(f"❌ {description}: Missing")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎯 All tool configurations found!")
        return True
    else:
        print("⚠️ Some tool configurations missing!")
        return False

def main():
    """Run all consistency tests"""
    
    print("🔍 TheTroubleMaker Agent Consistency Test")
    print("=" * 60)
    
    # Test system prompt
    prompt_ok = test_system_prompt()
    
    # Test tool configuration
    tools_ok = test_tool_configuration()
    
    print("\n" + "=" * 60)
    print("🎯 FINAL RESULTS:")
    
    if prompt_ok and tools_ok:
        print("✅ All tests passed! Agent should be consistent.")
        print("\n💡 If the agent is still being inconsistent, the issue might be:")
        print("   - The LLM not following the instructions properly")
        print("   - Context window limitations")
        print("   - Tool calling framework issues")
        print("   - Need for more explicit instructions")
    else:
        print("❌ Some tests failed! Agent configuration needs fixing.")
    
    return prompt_ok and tools_ok

if __name__ == "__main__":
    main() 