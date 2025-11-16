#!/usr/bin/env python3
"""
Test the orchestrator agent's get_next_action function
"""
import google.generativeai as genai
from PIL import ImageGrab
import sys

# Configure the API with your key
genai.configure(api_key='AIzaSyDMN_LE1wU6IJC5EQqrVSDn6FLaui_N5tg')

def get_next_action(screenshot, goal):
    """
    Ask Gemini for the next immediate action based on current screenshot.
    
    Args:
        screenshot: PIL Image object
        goal: The overarching goal
    
    Returns:
        str: The next action to take
    """
    # Create the prompt
    prompt = f"""Given the screenshot provided, and the overarching goal: '{goal}'.

What is the SINGLE NEXT immediate action to take? 
- Give me only ONE action that involves clicking on something visible in this screenshot
- Be specific about what to click (e.g., "Click on the Finder icon in the dock")
- If the goal is already achieved, respond with exactly: GOAL_COMPLETE
- Format: Just state the action clearly in one sentence, no numbering or extra text"""
    
    # Build contents list (prompt + image)
    contents = [prompt, screenshot]
    
    # Send request to Gemini (using stable model)
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(contents)
    
    # Extract the text response
    response_text = response.text.strip()
    
    return response_text

if __name__ == "__main__":
    # Get goal from command line or use default
    goal = sys.argv[1] if len(sys.argv) > 1 else "Open Safari browser"
    
    print(f"🎯 Goal: {goal}")
    print("📸 Taking screenshot...")
    
    # Take a screenshot of current screen
    screenshot = ImageGrab.grab()
    
    # Optionally save it for reference
    screenshot.save("test_screenshot.png")
    print("💾 Screenshot saved as test_screenshot.png")
    
    print("🤖 Asking Gemini for next action...")
    
    # Get the next action
    next_action = get_next_action(screenshot, goal)
    
    print(f"\n{'='*60}")
    print(f"✨ Gemini's Response:")
    print(f"{'='*60}")
    print(next_action)
    print(f"{'='*60}\n")
