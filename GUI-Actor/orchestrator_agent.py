import google.generativeai as genai
from PIL import Image
import os

# Configure the API with your key
genai.configure(api_key='AIzaSyDMN_LE1wU6IJC5EQqrVSDn6FLaui_N5tg')

def test(action):
    """
    Placeholder function that executes a single action/click.
    
    Args:
        action: The action to perform (e.g., "Click on Finder icon")
    
    Returns:
        tuple: ("DONE", screenshot_path) - status and path to new screenshot
    """
    print(f"Executing: {action}")
    # Your actual action execution logic goes here
    # This should perform the click and capture a new screenshot
    
    # For now, returning placeholder
    new_screenshot_path = "updated_screenshot.png"  # Replace with actual new screenshot path
    print("DONE")
    return ("DONE", new_screenshot_path)

def get_next_action(screenshot_path, goal, chat_history=None):
    """
    Ask Gemini 2.5 Flash for the next immediate action based on current screenshot.
    
    Args:
        screenshot_path: Path to current screenshot
        goal: The overarching goal
        chat_history: List of previous messages for context (optional)
    
    Returns:
        str: The next action to take, or None if goal is complete
    """
    # Load the screenshot
    img = Image.open(screenshot_path)
    
    # Build context from chat history
    history_context = ""
    if chat_history and len(chat_history) > 0:
        history_context = "\n\nPrevious actions taken:\n"
        # Show last 3 actions to avoid repeating
        for action in chat_history[-3:]:
            history_context += f"- {action}\n"
        history_context += "\nDo NOT repeat the same action. Move to the NEXT step.\n"
    
    # Create the prompt
    prompt = f"""You are controlling a computer to achieve this goal: '{goal}'
{history_context}
Look at the current screenshot and determine the NEXT SINGLE ACTION needed.

Rules:
1. Give ONLY ONE action at a time
2. Be specific about what to click or type AND include the general location (top/middle/bottom/left/right of screen)
3. Extract the exact search terms or text from the goal - DO NOT make up different text
4. Always click a field BEFORE typing into it
5. After clicking a search bar or text field, the NEXT action should be to type the search query
6. After clicking on a YouTube video, check for a 'Skip Ad' button and click it if present
7. Once the video is playing, respond with "GOAL_COMPLETE"

Examples:
- "Click on the Safari icon at the bottom of the screen"
- "Click on the search bar at the top of the screen"
- "Type 'how to use github'"
- "Press Enter"
- "Click on the first video result in the middle of the screen"
- "Click the Skip Ad button in the bottom right"
- "GOAL_COMPLETE"

IMPORTANT: 
- When typing search queries, use the EXACT terms from the goal
- Always specify the general location of UI elements (top/middle/bottom/left/right/center)
- After clicking a search field, you MUST type the search query in the next action
- If you see a Skip Ad button, click it before saying GOAL_COMPLETE

What is the next action?"""
    
    # Build contents list (prompt + image)
    contents = [prompt, img]
    
    # If we have chat history, we can maintain context across calls
    # For now, we'll make fresh calls each time for simplicity
    
    # Send request to Gemini 2.5 Flash
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(contents)
    
    # Extract the text response
    response_text = response.text.strip()
    
    return response_text

def execute_goal_with_iterations(initial_screenshot_path, goal, max_iterations=20):
    """
    Main iterative function that:
    1. Gets next action from Gemini based on current screenshot
    2. Executes the action using test()
    3. Gets new screenshot
    4. Repeats until goal is complete or max iterations reached
    
    Args:
        initial_screenshot_path: Path to starting screenshot
        goal: The overarching goal to achieve
        max_iterations: Maximum number of steps to prevent infinite loops
    """
    
    print(f"Starting goal: {goal}")
    print(f"Initial screenshot: {initial_screenshot_path}\n")
    print(f"Using Gemini 2.5 Flash model\n")
    
    current_screenshot = initial_screenshot_path
    iteration = 0
    
    # Store conversation history for context (optional)
    conversation_history = []
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n{'='*60}")
        print(f"ITERATION {iteration}")
        print(f"{'='*60}")
        
        # Get next action from Gemini
        print(f"Analyzing screenshot: {current_screenshot}")
        next_action = get_next_action(current_screenshot, goal, conversation_history)
        
        print(f"\nGemini 2.5 Flash says: {next_action}")
        
        # Store in conversation history
        conversation_history.append({
            "screenshot": current_screenshot,
            "action": next_action
        })
        
        # Check if goal is complete
        if "GOAL_COMPLETE" in next_action.upper() or "goal is achieved" in next_action.lower():
            print("\n✓ Goal achieved!")
            break
        
        # Execute the action
        print(f"\nExecuting action...")
        status, new_screenshot = test(next_action)
        
        if status == "DONE":
            print(f"Action completed. New screenshot: {new_screenshot}")
            current_screenshot = new_screenshot
        else:
            print("Error executing action")
            break
    
    if iteration >= max_iterations:
        print(f"\n⚠ Reached maximum iterations ({max_iterations})")
    
    print(f"\nTotal iterations: {iteration}")
    print("Process complete!")
    return conversation_history

# Example usage
if __name__ == "__main__":
    # Set your API key as environment variable:
    # export GEMINI_API_KEY='your-api-key-here'
    # Or on Windows: set GEMINI_API_KEY=your-api-key-here
    
    # Example: Open Safari starting from home screen
    initial_screenshot = "homescreen.png"  # Replace with your screenshot path
    goal = "Open Safari browser"
    
    history = execute_goal_with_iterations(initial_screenshot, goal, max_iterations=20)