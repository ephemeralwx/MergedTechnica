#!/usr/bin/env python3
"""
Test actual clicking behavior to diagnose the 30-pixel offset issue
"""

import pyautogui
from PIL import ImageGrab, ImageDraw
import time

def test_click_with_screenshot():
    """Test clicking using the same logic as gui_agent.py"""
    
    print("\n" + "="*60)
    print("🎯 Testing Actual Click Behavior")
    print("="*60 + "\n")
    
    # Take a screenshot (like the agent does)
    screenshot = ImageGrab.grab()
    screenshot_width, screenshot_height = screenshot.size
    print(f"Screenshot size: {screenshot_width}x{screenshot_height}")
    
    # Get screen dimensions (what pyautogui uses)
    screen_width, screen_height = pyautogui.size()
    print(f"Screen size (logical): {screen_width}x{screen_height}")
    
    # Simulate VLM predicting center of screen
    norm_x, norm_y = 0.5, 0.5
    print(f"\nVLM prediction (normalized): ({norm_x}, {norm_y})")
    
    # Current code logic (AFTER fix - no +2 offset)
    screenshot_x = norm_x * screenshot_width
    screenshot_y = norm_y * screenshot_height
    print(f"Screenshot coords: ({screenshot_x:.1f}, {screenshot_y:.1f})")
    
    scale_x = screen_width / screenshot_width
    scale_y = screen_height / screenshot_height
    print(f"Scale factors: ({scale_x:.3f}, {scale_y:.3f})")
    
    pixel_x = int(screenshot_x * scale_x)
    pixel_y = int(screenshot_y * scale_y)
    print(f"Calculated screen coords: ({pixel_x}, {pixel_y})")
    
    # Expected center
    expected_x = screen_width // 2
    expected_y = screen_height // 2
    print(f"Expected center: ({expected_x}, {expected_y})")
    
    # Draw a target on the screenshot at the VLM prediction point
    draw = ImageDraw.Draw(screenshot)
    target_x = int(norm_x * screenshot_width)
    target_y = int(norm_y * screenshot_height)
    
    # Draw crosshairs
    size = 100
    draw.line([target_x - size, target_y, target_x + size, target_y], fill='red', width=10)
    draw.line([target_x, target_y - size, target_x, target_y + size], fill='red', width=10)
    draw.ellipse([target_x - 30, target_y - 30, target_x + 30, target_y + 30], outline='red', width=10)
    
    screenshot.save("test_target.png")
    print(f"\n💾 Saved screenshot with target to: test_target.png")
    print(f"   Target is at screenshot pixel: ({target_x}, {target_y})")
    
    print(f"\n🖱️  Will move mouse to: ({pixel_x}, {pixel_y})")
    print(f"   Starting in 3 seconds... Watch the cursor!")
    time.sleep(3)
    
    # Move mouse
    pyautogui.moveTo(pixel_x, pixel_y, duration=0.5)
    time.sleep(2)
    
    # Verify
    actual_x, actual_y = pyautogui.position()
    print(f"\n✅ Mouse moved to: ({actual_x}, {actual_y})")
    print(f"   Error from target: ({actual_x - pixel_x}, {actual_y - pixel_y}) pixels")
    
    print("\n" + "="*60)
    print("Open test_target.png to see where the red crosshair is.")
    print("The mouse should have moved to that exact location.")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_click_with_screenshot()
