#!/usr/bin/env python3
"""
Test to detect macOS menubar offset
"""

import pyautogui
from PIL import ImageGrab
import AppKit

def test_menubar_offset():
    """Check if there's a menubar offset on macOS"""
    
    print("\n" + "="*60)
    print("🍎 Testing macOS Menubar Offset")
    print("="*60 + "\n")
    
    # Get screen info from pyautogui
    screen_width, screen_height = pyautogui.size()
    print(f"pyautogui screen size: {screen_width}x{screen_height}")
    
    # Get screen info from PIL
    screenshot = ImageGrab.grab()
    screenshot_width, screenshot_height = screenshot.size
    print(f"PIL screenshot size: {screenshot_width}x{screenshot_height}")
    
    # Get screen info from AppKit (native macOS)
    screen = AppKit.NSScreen.mainScreen()
    frame = screen.frame()
    visible_frame = screen.visibleFrame()
    
    print(f"\nmacOS NSScreen info:")
    print(f"  Full frame: {frame.size.width:.0f}x{frame.size.height:.0f}")
    print(f"  Visible frame: {visible_frame.size.width:.0f}x{visible_frame.size.height:.0f}")
    print(f"  Visible frame origin: ({visible_frame.origin.x:.0f}, {visible_frame.origin.y:.0f})")
    
    # Calculate menubar height
    menubar_height = frame.size.height - visible_frame.size.height - visible_frame.origin.y
    print(f"\n📏 Calculated menubar height: {menubar_height:.0f} pixels")
    
    # Check if there's a coordinate system difference
    if screenshot_height != screen_height:
        print(f"\n⚠️  WARNING: Screenshot height ({screenshot_height}) != pyautogui height ({screen_height})")
        print(f"   Difference: {abs(screenshot_height - screen_height)} pixels")
        
        # Check if it's a retina display issue
        if screenshot_height == screen_height * 2:
            print(f"   This appears to be a Retina display (2x scaling)")
    
    # Test actual mouse position
    print(f"\n🖱️  Testing mouse position accuracy...")
    print(f"   Moving mouse to (100, 100)...")
    pyautogui.moveTo(100, 100)
    actual_x, actual_y = pyautogui.position()
    print(f"   Actual position: ({actual_x}, {actual_y})")
    
    if actual_x == 100 and actual_y == 100:
        print(f"   ✅ Mouse positioning is accurate")
    else:
        print(f"   ⚠️  Mouse position differs by ({actual_x - 100}, {actual_y - 100})")
    
    print("\n" + "="*60)
    print("✅ Menubar offset test complete")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_menubar_offset()
