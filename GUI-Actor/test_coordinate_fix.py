#!/usr/bin/env python3
"""
Test coordinate transformation to verify the fix
Tests that VLM normalized coordinates map correctly to screen coordinates
"""

import pyautogui
from PIL import Image, ImageGrab, ImageDraw, ImageFont
import time

def test_coordinate_transformation():
    """Test that coordinate transformation works correctly"""
    
    print("\n" + "="*60)
    print("🧪 Testing Coordinate Transformation Fix")
    print("="*60 + "\n")
    
    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()
    print(f"Screen dimensions: {screen_width}x{screen_height}")
    
    # Simulate a screenshot (could be resized)
    screenshot = ImageGrab.grab()
    screenshot_width, screenshot_height = screenshot.size
    print(f"Screenshot dimensions: {screenshot_width}x{screenshot_height}")
    
    # Test cases: normalized coordinates (0-1) that VLM would output
    test_cases = [
        (0.5, 0.5, "Center"),
        (0.25, 0.25, "Top-left quadrant"),
        (0.75, 0.75, "Bottom-right quadrant"),
        (0.1, 0.1, "Near top-left corner"),
        (0.9, 0.9, "Near bottom-right corner"),
    ]
    
    print("\n" + "-"*60)
    print("Testing coordinate transformations:")
    print("-"*60)
    
    for norm_x, norm_y, description in test_cases:
        # OLD BUGGY CODE (with +2 offset):
        # screenshot_x = norm_x * screenshot_width
        # screenshot_y = norm_y * screenshot_height
        # scale_x = screen_width / screenshot_width
        # scale_y = screen_height / screenshot_height
        # pixel_x_old = int(screenshot_x * scale_x)
        # pixel_y_old = int(screenshot_y * scale_y) + 2
        
        # NEW FIXED CODE (no offset):
        screenshot_x = norm_x * screenshot_width
        screenshot_y = norm_y * screenshot_height
        scale_x = screen_width / screenshot_width
        scale_y = screen_height / screenshot_height
        pixel_x = int(screenshot_x * scale_x)
        pixel_y = int(screenshot_y * scale_y)
        
        # Expected coordinates (direct calculation)
        expected_x = int(norm_x * screen_width)
        expected_y = int(norm_y * screen_height)
        
        # Calculate error
        error_x = abs(pixel_x - expected_x)
        error_y = abs(pixel_y - expected_y)
        
        print(f"\n{description}:")
        print(f"  Normalized: ({norm_x:.2f}, {norm_y:.2f})")
        print(f"  Screenshot space: ({screenshot_x:.1f}, {screenshot_y:.1f})")
        print(f"  Screen space: ({pixel_x}, {pixel_y})")
        print(f"  Expected: ({expected_x}, {expected_y})")
        print(f"  Error: ({error_x}, {error_y}) pixels")
        
        if error_x > 2 or error_y > 2:
            print(f"  ⚠️  WARNING: Error > 2 pixels!")
        else:
            print(f"  ✅ OK")
    
    print("\n" + "="*60)
    print("✅ Coordinate transformation test complete")
    print("="*60 + "\n")


def test_visual_click_accuracy():
    """Visual test: Click at specific screen locations and verify accuracy"""
    
    print("\n" + "="*60)
    print("🎯 Visual Click Accuracy Test")
    print("="*60 + "\n")
    print("This test will move the mouse to 5 locations on screen.")
    print("Watch to see if the cursor goes to the correct position.")
    print("\nStarting in 3 seconds...")
    time.sleep(3)
    
    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()
    
    # Test points (in normalized coordinates)
    test_points = [
        (0.5, 0.5, "Center"),
        (0.25, 0.25, "Top-left"),
        (0.75, 0.25, "Top-right"),
        (0.25, 0.75, "Bottom-left"),
        (0.75, 0.75, "Bottom-right"),
    ]
    
    for norm_x, norm_y, label in test_points:
        # Calculate screen coordinates (simulating the fixed code)
        pixel_x = int(norm_x * screen_width)
        pixel_y = int(norm_y * screen_height)
        
        print(f"\n🖱️  Moving to {label}: ({pixel_x}, {pixel_y})")
        
        # Move mouse
        pyautogui.moveTo(pixel_x, pixel_y, duration=0.5)
        time.sleep(0.5)
        
        # Verify actual position
        actual_x, actual_y = pyautogui.position()
        error_x = abs(actual_x - pixel_x)
        error_y = abs(actual_y - pixel_y)
        
        print(f"   Target: ({pixel_x}, {pixel_y})")
        print(f"   Actual: ({actual_x}, {actual_y})")
        print(f"   Error: ({error_x}, {error_y}) pixels")
        
        if error_x > 5 or error_y > 5:
            print(f"   ⚠️  WARNING: Position error > 5 pixels!")
        else:
            print(f"   ✅ Accurate")
        
        time.sleep(1)
    
    print("\n" + "="*60)
    print("✅ Visual test complete")
    print("="*60 + "\n")


def test_screenshot_resize_scenario():
    """Test coordinate transformation when screenshot is resized"""
    
    print("\n" + "="*60)
    print("📐 Testing Resized Screenshot Scenario")
    print("="*60 + "\n")
    
    # Get actual screen dimensions
    screen_width, screen_height = pyautogui.size()
    print(f"Actual screen: {screen_width}x{screen_height}")
    
    # Simulate a resized screenshot (like MAX_SCREENSHOT_SIZE = 768)
    MAX_SIZE = 768
    if screen_width > MAX_SIZE or screen_height > MAX_SIZE:
        if screen_width > screen_height:
            screenshot_width = MAX_SIZE
            screenshot_height = int(screen_height * (MAX_SIZE / screen_width))
        else:
            screenshot_height = MAX_SIZE
            screenshot_width = int(screen_width * (MAX_SIZE / screen_height))
    else:
        screenshot_width = screen_width
        screenshot_height = screen_height
    
    print(f"Resized screenshot: {screenshot_width}x{screenshot_height}")
    
    # Test a specific point
    norm_x, norm_y = 0.5, 0.5  # Center of screen
    
    # Calculate using the fixed transformation
    screenshot_x = norm_x * screenshot_width
    screenshot_y = norm_y * screenshot_height
    scale_x = screen_width / screenshot_width
    scale_y = screen_height / screenshot_height
    pixel_x = int(screenshot_x * scale_x)
    pixel_y = int(screenshot_y * scale_y)
    
    # Expected (should be center of actual screen)
    expected_x = screen_width // 2
    expected_y = screen_height // 2
    
    print(f"\nTest point: Center (0.5, 0.5)")
    print(f"  Screenshot coords: ({screenshot_x:.1f}, {screenshot_y:.1f})")
    print(f"  Scale factors: ({scale_x:.3f}, {scale_y:.3f})")
    print(f"  Calculated screen coords: ({pixel_x}, {pixel_y})")
    print(f"  Expected screen coords: ({expected_x}, {expected_y})")
    print(f"  Error: ({abs(pixel_x - expected_x)}, {abs(pixel_y - expected_y)}) pixels")
    
    if abs(pixel_x - expected_x) <= 1 and abs(pixel_y - expected_y) <= 1:
        print(f"  ✅ Transformation is accurate!")
    else:
        print(f"  ⚠️  Transformation has error")
    
    print("\n" + "="*60)
    print("✅ Resize scenario test complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🧪 Running Coordinate Fix Tests\n")
    
    # Run tests
    test_coordinate_transformation()
    test_screenshot_resize_scenario()
    
    # Ask user if they want to run visual test
    response = input("\n🎯 Run visual click test? (moves mouse around screen) [y/N]: ")
    if response.lower() == 'y':
        test_visual_click_accuracy()
    else:
        print("Skipping visual test.")
    
    print("\n✅ All tests complete!\n")
