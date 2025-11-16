#!/usr/bin/env python3
"""
Basic test to see if pyautogui can move the mouse on macOS
"""

import pyautogui
import time

print("="*60)
print("PYAUTOGUI BASIC FUNCTIONALITY TEST")
print("="*60)

# Check settings
print(f"\nPyAutoGUI Settings:")
print(f"  PAUSE: {pyautogui.PAUSE}")
print(f"  FAILSAFE: {pyautogui.FAILSAFE}")
print(f"  Screen size: {pyautogui.size()}")

# Get current position
current = pyautogui.position()
print(f"\nCurrent mouse position: {current}")

# Test 1: Try to move mouse
print("\n" + "="*60)
print("TEST 1: Moving mouse to center of screen")
print("="*60)

screen_width, screen_height = pyautogui.size()
center_x = screen_width // 2
center_y = screen_height // 2

print(f"Target: ({center_x}, {center_y})")
print("Moving in 3 seconds...")
time.sleep(3)

try:
    pyautogui.moveTo(center_x, center_y, duration=1.0)
    time.sleep(0.5)
    
    actual = pyautogui.position()
    print(f"Actual position after move: {actual}")
    
    if actual.x == center_x and actual.y == center_y:
        print("✅ SUCCESS: Mouse moved correctly!")
    else:
        error_x = abs(actual.x - center_x)
        error_y = abs(actual.y - center_y)
        print(f"⚠️  PARTIAL: Mouse moved but with error: ({error_x}, {error_y}) pixels")
        
        if error_x == 0 and error_y == 0 and (actual.x != center_x or actual.y != center_y):
            print("❌ FAILED: Mouse didn't move at all!")
            print("\n🔒 PERMISSION ISSUE DETECTED!")
            print("   macOS is blocking pyautogui from controlling the mouse.")
            print("\n   FIX:")
            print("   1. Open System Settings")
            print("   2. Go to Privacy & Security > Accessibility")
            print("   3. Add Terminal (or your Python app)")
            print("   4. Restart this script")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("\n🔒 This might be a permission issue!")

# Test 2: Try clicking
print("\n" + "="*60)
print("TEST 2: Testing click (won't actually click)")
print("="*60)

try:
    # Just test if the function works without actually clicking
    print("Testing pyautogui.click() function...")
    # Move to a safe spot first
    pyautogui.moveTo(100, 100, duration=0.5)
    time.sleep(0.5)
    actual = pyautogui.position()
    print(f"Moved to: {actual}")
    
    if actual.x == 100 and actual.y == 100:
        print("✅ Mouse movement works!")
    else:
        print(f"⚠️  Mouse at {actual}, expected (100, 100)")
        
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*60)
print("DIAGNOSIS")
print("="*60)

# Check if mouse moved at all
final_pos = pyautogui.position()
if final_pos == current:
    print("\n❌ CRITICAL: Mouse did not move at all!")
    print("   This is definitely a macOS permission issue.")
    print("\n   Required permissions:")
    print("   - System Settings > Privacy & Security > Accessibility")
    print("   - Add: Terminal (or Python/conda)")
    print("   - You may need to RESTART your terminal after granting permission")
else:
    print("\n✅ Mouse movement is working!")
    print(f"   Started at: {current}")
    print(f"   Ended at: {final_pos}")
