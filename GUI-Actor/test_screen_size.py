#!/usr/bin/env python3
"""
Test to check screen size detection on macOS Retina displays
"""

import pyautogui
from PIL import ImageGrab

print("="*60)
print("SCREEN SIZE DETECTION TEST")
print("="*60)

# Method 1: pyautogui
pyautogui_size = pyautogui.size()
print(f"\n1. pyautogui.size(): {pyautogui_size[0]} x {pyautogui_size[1]}")

# Method 2: PIL ImageGrab
screenshot = ImageGrab.grab()
pil_size = screenshot.size
print(f"2. PIL ImageGrab: {pil_size[0]} x {pil_size[1]}")

# Check if they match
if pyautogui_size[0] != pil_size[0] or pyautogui_size[1] != pil_size[1]:
    print("\n⚠️  MISMATCH DETECTED!")
    print(f"   Ratio: {pil_size[0]/pyautogui_size[0]:.2f}x (width), {pil_size[1]/pyautogui_size[1]:.2f}x (height)")
    print(f"   This is likely a Retina display with HiDPI scaling")
    print(f"\n   pyautogui uses LOGICAL coordinates: {pyautogui_size[0]} x {pyautogui_size[1]}")
    print(f"   PIL uses PHYSICAL pixels: {pil_size[0]} x {pil_size[1]}")
else:
    print("\n✅ Sizes match - no scaling detected")

print("\n" + "="*60)
print("MOUSE COORDINATE TEST")
print("="*60)

# Test mouse movement
print("\nTesting if pyautogui coordinates match screen...")
print("Move your mouse to the TOP-LEFT corner and press Enter")
input()
pos = pyautogui.position()
print(f"Position at top-left: {pos}")

print("\nMove your mouse to the BOTTOM-RIGHT corner and press Enter")
input()
pos = pyautogui.position()
print(f"Position at bottom-right: {pos}")
print(f"Expected (pyautogui): ~({pyautogui_size[0]-1}, {pyautogui_size[1]-1})")
print(f"Expected (PIL): ~({pil_size[0]-1}, {pil_size[1]-1})")

print("\n" + "="*60)
print("CONCLUSION")
print("="*60)
print("\nOn macOS Retina displays:")
print("- pyautogui works in LOGICAL coordinates (e.g., 1512x982)")
print("- PIL ImageGrab captures PHYSICAL pixels (e.g., 3024x1964)")
print("- You MUST use pyautogui.size() for mouse movements!")
print("- Screenshots will be 2x larger than pyautogui coordinates")
