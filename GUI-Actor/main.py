#!/usr/bin/env python3
"""
Autonomous GUI Agent System
Combines orchestrator_agent (planning) with gui_agent (execution)
"""

import os
import sys

# CRITICAL: Set this BEFORE any other imports to prevent tokenizer fork issues
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import time
from datetime import datetime
from PIL import ImageGrab, Image
import pyautogui

# Import from our modules
from orchestrator_agent import get_next_action
from gui_agent import (
    VLMModel, 
    take_screenshot, 
    parse_command, 
    execute_action,
    CommandLogger,
    log_status as gui_log_status,
    command_counter,
    LOG_DIR
)

# ============================================================================
# CONFIGURATION
# ============================================================================

MAX_ITERATIONS = 30
SCREENSHOT_DIR = "autonomous_screenshots"
ACTION_DELAY = 1.0  # Delay between actions to let UI update

# ============================================================================
# GLOBAL STATE
# ============================================================================

iteration_count = 0
stop_execution = False
click_attempt_count = 0  # Track number of click attempts


# ============================================================================
# LOGGING
# ============================================================================

def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def save_iteration_screenshot(screenshot, iteration_num, action_description=""):
    """Save screenshot for this iteration"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    # Create safe filename from action description
    safe_action = "".join(c if c.isalnum() or c in (' ', '_') else '_' for c in action_description)
    safe_action = safe_action[:50]  # Limit length
    
    filename = f"iter_{iteration_num:03d}_{safe_action}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    
    screenshot.save(filepath)
    log(f"💾 Screenshot saved: {filepath}")
    return filepath


# ============================================================================
# MAIN AUTONOMOUS LOOP
# ============================================================================

def run_autonomous_agent(goal, max_iterations=MAX_ITERATIONS):
    """
    Main autonomous loop that coordinates between orchestrator and gui_agent
    
    Args:
        goal: The user's end goal (e.g., "Open Safari", "Send an email")
        max_iterations: Maximum number of actions to prevent infinite loops
    
    Returns:
        bool: True if goal was completed, False otherwise
    """
    global iteration_count, stop_execution, click_attempt_count
    
    log("\n" + "="*70)
    log("🤖 AUTONOMOUS GUI AGENT SYSTEM")
    log("="*70)
    log(f"🎯 Goal: {goal}")
    log(f"📊 Max iterations: {max_iterations}")
    log("="*70 + "\n")
    
    # Initialize VLM model for GUI agent
    log("🔄 Loading GUI-Actor model...")
    vlm_model = VLMModel()
    if not vlm_model.load():
        log("❌ Failed to load VLM model. Exiting.")
        return False
    
    log("✅ Model loaded successfully!\n")
    
    # Initialize command logger
    from gui_agent import command_logger
    
    iteration_count = 0
    click_attempt_count = 0  # Reset click counter
    conversation_history = []
    last_actions = []  # Track recent actions to detect loops
    
    try:
        while iteration_count < max_iterations and not stop_execution:
            iteration_count += 1
            
            log("\n" + "="*70)
            log(f"🔄 ITERATION {iteration_count}/{max_iterations}")
            log("="*70)
            
            # Step 1: Take screenshot
            log("📸 Capturing current screen state...")
            screenshot = take_screenshot()
            if screenshot is None:
                log("❌ Failed to capture screenshot")
                return False
            
            # Save screenshot for this iteration
            screenshot_path = save_iteration_screenshot(
                screenshot, 
                iteration_count, 
                f"before_action"
            )
            
            # Step 2: Ask orchestrator for next action
            log(f"🧠 Asking orchestrator: What's the next action for '{goal}'?")
            try:
                # Pass recent actions as history to prevent loops
                recent_actions = [h["action"] for h in conversation_history[-3:]] if conversation_history else []
                next_action = get_next_action(screenshot_path, goal, chat_history=recent_actions)
                log(f"💡 Orchestrator says: {next_action}")
                
                # Detect if we're stuck in a loop (same action repeated 3+ times)
                last_actions.append(next_action.lower().strip())
                if len(last_actions) > 3:
                    last_actions.pop(0)  # Keep only last 3 actions
                
                if len(last_actions) >= 3 and len(set(last_actions)) == 1:
                    log(f"⚠️  LOOP DETECTED: Same action repeated 3 times!")
                    log(f"   Action: {next_action}")
                    log(f"   Trying to break loop by typing the search query...")
                    # Extract search terms from the goal and type them
                    # For YouTube searches, extract the topic after "youtube" or "video"
                    goal_lower = goal.lower()
                    if "youtube" in goal_lower or "video" in goal_lower:
                        # Extract what comes after keywords like "on", "about", "for"
                        for keyword in ["on how to", "about", "on", "for"]:
                            if keyword in goal_lower:
                                search_query = goal_lower.split(keyword, 1)[1].strip()
                                next_action = f"Type '{search_query}'"
                                break
                        else:
                            # Fallback: use the whole goal
                            next_action = f"Type '{goal}'"
                    else:
                        next_action = f"Type '{goal}'"
                    last_actions.clear()  # Reset loop detection
                
            except Exception as e:
                log(f"❌ Orchestrator error: {str(e)}")
                return False
            
            # Store in history
            conversation_history.append({
                "iteration": iteration_count,
                "screenshot": screenshot_path,
                "action": next_action
            })
            
            # Step 3: Check if goal is complete
            if "GOAL_COMPLETE" in next_action.upper() or "goal is achieved" in next_action.lower():
                log("\n" + "="*70)
                log("🎉 SUCCESS! Goal has been achieved!")
                log("="*70)
                return True
            
            # Step 4: Parse the action
            log(f"🔍 Parsing action...")
            action_dict = parse_command(next_action)
            log(f"   Action type: {action_dict['type']}")
            
            # Step 5: Execute action via GUI agent
            log(f"⚡ Executing action via GUI agent...")
            
            # Start command logging for this action
            command_logger.start_command_log(iteration_count, next_action)
            
            try:
                # Check if this is a click action
                is_click_action = action_dict['type'] in ['click', 'CLICK']
                
                if is_click_action:
                    click_attempt_count += 1
                    
                if is_click_action and click_attempt_count == 1:
                    # First click - execute twice
                    log(f"🖱️  First click detected - executing double-click")
                    
                    # First click
                    success = execute_action(action_dict, vlm_model, screenshot=screenshot)
                    if success:
                        log(f"✅ First click executed")
                    
                    # Wait 1 second
                    log(f"⏳ Waiting 1s before second click...")
                    time.sleep(1.0)
                    
                    # Second click
                    success = execute_action(action_dict, vlm_model, screenshot=screenshot)
                    if success:
                        log(f"✅ Second click executed")
                else:
                    # Normal execution for non-click or subsequent clicks
                    success = execute_action(action_dict, vlm_model, screenshot=screenshot)
                
                if success:
                    log(f"✅ Action executed successfully")
                else:
                    log(f"⚠️  Action execution failed")
                    # Continue anyway - orchestrator will see the result
                
            except Exception as e:
                error_msg = f"Exception during action execution: {str(e)}"
                log(f"❌ {error_msg}")
                command_logger.log_error(error_msg)
            
            finally:
                # Finalize command logging
                command_logger.finalize_log()
            
            # Step 6: Wait for UI to update
            log(f"⏳ Waiting {ACTION_DELAY}s for UI to update...")
            time.sleep(ACTION_DELAY)
            
            log(f"✓ Iteration {iteration_count} complete\n")
    
    except KeyboardInterrupt:
        log("\n\n🛑 Stopped by user (Ctrl+C)")
        stop_execution = True
        return False
    
    except Exception as e:
        log(f"\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # If we reach here, we hit max iterations
    log("\n" + "="*70)
    log(f"⚠️  Reached maximum iterations ({max_iterations})")
    log("   Goal may not be complete")
    log("="*70)
    return False


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main program entry point"""
    
    print("\n" + "="*70)
    print("🤖 AUTONOMOUS GUI AGENT SYSTEM")
    print("   Orchestrator: Gemini 2.5 Flash (Planning)")
    print("   GUI Agent: GUI-Actor-2B-Qwen2-VL (Execution)")
    print("="*70 + "\n")
    
    # Check macOS permissions
    print("⚠️  IMPORTANT macOS Permissions Required:")
    print("   1. System Settings > Privacy & Security > Accessibility")
    print("      - Add Terminal or your Python executable")
    print("   2. System Settings > Privacy & Security > Screen Recording")
    print("      - Add Terminal or your Python executable")
    print("\n")
    
    # Configure pyautogui
    pyautogui.FAILSAFE = True  # Move mouse to corner to stop
    pyautogui.PAUSE = 0.5
    
    # Get goal from user
    if len(sys.argv) > 1:
        # Goal provided as command line argument
        goal = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("Enter your goal (e.g., 'Open Safari', 'Send an email'):")
        print("🎯 Goal: ", end="", flush=True)
        goal = input().strip()
    
    if not goal:
        print("❌ No goal provided. Exiting.")
        return
    
    # Confirm with user
    print(f"\n📋 Goal: {goal}")
    print("Press Enter to start, or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n👋 Cancelled by user")
        return
    
    # Run the autonomous agent
    success = run_autonomous_agent(goal)
    
    # Final summary
    print("\n" + "="*70)
    print("📊 EXECUTION SUMMARY")
    print("="*70)
    print(f"Goal: {goal}")
    print(f"Total iterations: {iteration_count}")
    print(f"Logs saved to: {LOG_DIR}/")
    print(f"Screenshots saved to: {SCREENSHOT_DIR}/")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
