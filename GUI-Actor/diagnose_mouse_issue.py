#!/usr/bin/env python3
"""
Comprehensive diagnostic for mouse control issues on macOS
"""

import pyautogui
import time
import sys

print("="*70)
print("MOUSE CONTROL DIAGNOSTIC FOR macOS")
print("="*70)

# Step 1: Check current position
print("\n[1/5] Checking current mouse position...")
try:
    pos = pyautogui.position()
    print(f"✅ Current position: {pos}")
except Exception as e:
    print(f"❌ ERROR: Cannot read mouse position: {e}")
    sys.exit(1)

# Step 2: Check screen size
print("\n[2/5] Checking screen size...")
try:
    size = pyautogui.size()
    print(f"✅ Screen size: {size}")
except Exception as e:
    print(f"❌ ERROR: Cannot get screen size: {e}")
    sys.exit(1)

# Step 3: Test mouse movement
print("\n[3/5] Testing mouse movement...")
print("⏰ In 3 seconds, I will try to move your mouse to (100, 100)")
print("   Watch your cursor carefully!")

for i in range(3, 0, -1):
    print(f"   {i}...")
    time.sleep(1)

initial_pos = pyautogui.position()
print(f"\n   Initial position: {initial_pos}")

try:
    print("   Attempting to move to (100, 100)...")
    pyautogui.moveTo(100, 100, duration=0.5)
    time.sleep(0.3)
    
    new_pos = pyautogui.position()
    print(f"   Position after moveTo: {new_pos}")
    
    if new_pos.x == 100 and new_pos.y == 100:
        print("   ✅ SUCCESS! Mouse moved correctly!")
    elif new_pos == initial_pos:
        print("   ❌ FAILED! Mouse did not move at all!")
        print("\n" + "="*70)
        print("🔒 PERMISSION ISSUE DETECTED!")
        print("="*70)
        print("\nYour Mac is blocking Python from controlling the mouse.")
        print("\nTO FIX:")
        print("1. Open 'System Settings' (or System Preferences)")
        print("2. Go to 'Privacy & Security' > 'Accessibility'")
        print("3. Click the lock icon to make changes")
        print("4. Look for 'Terminal' or 'Python' in the list")
        print("5. If not there, click '+' and add:")
        print("   - Terminal.app (if running from terminal)")
        print("   - Or your Python executable")
        print("6. Make sure the checkbox is ENABLED")
        print("7. You may need to RESTART Terminal/Python")
        print("\nAlternatively, try running with sudo (not recommended):")
        print("   sudo python gui_agent.py")
        sys.exit(1)
    else:
        print(f"   ⚠️  PARTIAL: Mouse moved to {new_pos} instead of (100, 100)")
        print(f"   Error: ({abs(new_pos.x - 100)}, {abs(new_pos.y - 100)}) pixels")
        
except Exception as e:
    print(f"   ❌ ERROR during moveTo: {e}")
    sys.exit(1)

# Step 4: Test clicking
print("\n[4/5] Testing click functionality...")
print("⏰ In 2 seconds, I will click at the current position")
print("   (This should be safe)")

time.sleep(2)

try:
    print("   Attempting click...")
    pyautogui.click()
    print("   ✅ Click command executed!")
except Exception as e:
    print(f"   ❌ ERROR during click: {e}")

# Step 5: Test with your actual coordinates
print("\n[5/5] Testing with your actual coordinates from log...")
print("   Target: (399, 776)")
print("⏰ In 2 seconds, I will move there...")

time.sleep(2)

try:
    print("   Moving to (399, 776)...")
    pyautogui.moveTo(399, 776, duration=0.5)
    time.sleep(0.3)
    
    final_pos = pyautogui.position()
    print(f"   Final position: {final_pos}")
    
    if final_pos.x == 399 and final_pos.y == 776:
        print("   ✅ Perfect! Moved to exact coordinates!")
    else:
        error_x = abs(final_pos.x - 399)
        error_y = abs(final_pos.y - 776)
        print(f"   ⚠️  Position error: ({error_x}, {error_y}) pixels")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nIf the mouse moved successfully, your pyautogui is working!")
print("If not, you need to grant Accessibility permissions.")
