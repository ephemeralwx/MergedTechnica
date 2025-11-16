#!/usr/bin/env python3
"""
Test script to verify coordinate conversion is working correctly
"""

import pyautogui
from PIL import ImageGrab

# Get actual screen size
screen_width, screen_height = pyautogui.size()
print(f"🖥️  Actual screen size: {screen_width} x {screen_height}")

# Simulate taking a screenshot (like the agent does)
screenshot = ImageGrab.grab()
original_width, original_height = screenshot.size
print(f"📸 Original screenshot: {original_width} x {original_height}")

# Simulate downscaling (like the agent does)
MAX_SCREENSHOT_SIZE = 1280
if original_width > MAX_SCREENSHOT_SIZE or original_height > MAX_SCREENSHOT_SIZE:
    if original_width > original_height:
        new_width = MAX_SCREENSHOT_SIZE
        new_height = int(original_height * (MAX_SCREENSHOT_SIZE / original_width))
    else:
        new_height = MAX_SCREENSHOT_SIZE
        new_width = int(original_width * (MAX_SCREENSHOT_SIZE / original_height))
    print(f"📐 Downscaled screenshot: {new_width} x {new_height}")
else:
    new_width, new_height = original_width, original_height
    print(f"📐 No downscaling needed")

print("\n" + "="*60)
print("COORDINATE CONVERSION TEST")
print("="*60)

# Test case: VLM returns normalized coordinates
test_cases = [
    (0.5, 0.5, "Center of screen"),
    (0.0, 0.0, "Top-left corner"),
    (1.0, 1.0, "Bottom-right corner"),
    (0.3410, 0.8500, "Your Safari example"),
]

for norm_x, norm_y, description in test_cases:
    print(f"\n{description}:")
    print(f"  Normalized: ({norm_x:.4f}, {norm_y:.4f})")
    
    # WRONG way (using screen size)
    wrong_x = int(norm_x * screen_width)
    wrong_y = int(norm_y * screen_height)
    print(f"  ❌ WRONG (using screen size): ({wrong_x}, {wrong_y})")
    
    # CORRECT way (using screenshot size)
    correct_x = int(norm_x * new_width)
    correct_y = int(norm_y * new_height)
    print(f"  ✅ CORRECT (using screenshot size): ({correct_x}, {correct_y})")
    
    # Show the difference
    diff_x = abs(wrong_x - correct_x)
    diff_y = abs(wrong_y - correct_y)
    print(f"  📏 Difference: ({diff_x}, {diff_y}) pixels")

print("\n" + "="*60)
print("MOUSE POSITION TEST")
print("="*60)
print("\nMove your mouse around and watch the coordinates...")
print("Press Ctrl+C to stop\n")

try:
    import time
    last_pos = None
    while True:
        current_pos = pyautogui.position()
        if current_pos != last_pos:
            x, y = current_pos
            # Show what normalized coords would be
            norm_x = x / new_width
            norm_y = y / new_height
            print(f"Mouse at: ({x:4d}, {y:4d}) | Normalized: ({norm_x:.4f}, {norm_y:.4f})")
            last_pos = current_pos
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n✅ Test complete!")
