#!/usr/bin/env python3
"""
Quick test script to verify autonomous system setup
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        print("  ✓ Importing orchestrator_agent...")
        from orchestrator_agent import get_next_action
        
        print("  ✓ Importing gui_agent...")
        from gui_agent import (
            VLMModel, 
            take_screenshot, 
            parse_command, 
            execute_action,
            CommandLogger
        )
        
        print("  ✓ Importing PIL...")
        from PIL import ImageGrab, Image
        
        print("  ✓ Importing pyautogui...")
        import pyautogui
        
        print("  ✓ Importing torch...")
        import torch
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        return False


def test_screenshot():
    """Test screenshot capture"""
    print("\nTesting screenshot capture...")
    
    try:
        from gui_agent import take_screenshot
        screenshot = take_screenshot()
        
        if screenshot:
            print(f"  ✓ Screenshot captured: {screenshot.size}")
            return True
        else:
            print("  ❌ Screenshot capture failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Screenshot error: {e}")
        return False


def test_command_parsing():
    """Test command parsing"""
    print("\nTesting command parsing...")
    
    try:
        from gui_agent import parse_command
        
        test_commands = [
            "Click on Safari icon",
            "Type hello world",
            "Press enter"
        ]
        
        for cmd in test_commands:
            result = parse_command(cmd)
            print(f"  ✓ '{cmd}' → {result['type']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Parsing error: {e}")
        return False


def test_gemini_api():
    """Test Gemini API configuration"""
    print("\nTesting Gemini API...")
    
    try:
        import google.generativeai as genai
        
        # Check if API key is configured
        # Note: This doesn't actually test the API, just checks if it's imported
        print("  ✓ Gemini API library imported")
        print("  ⚠️  Make sure your API key is configured in orchestrator_agent.py")
        return True
        
    except ImportError as e:
        print(f"  ❌ Gemini API not available: {e}")
        return False


def main():
    print("="*60)
    print("🧪 AUTONOMOUS SYSTEM TEST")
    print("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Screenshot", test_screenshot),
        ("Command Parsing", test_command_parsing),
        ("Gemini API", test_gemini_api),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! System is ready.")
        print("\nRun: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please fix issues before running.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
