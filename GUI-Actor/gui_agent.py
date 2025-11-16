#!/usr/bin/env python3
"""
Autonomous GUI Agent using GUI-Actor-2B-Qwen2-VL
Controls your MacBook based on natural language commands
Press ESC to stop the agent
"""

import os
# avoid tokenizer fork race, set before transformers loads
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
import pyautogui
import tkinter as tk
from tkinter import scrolledtext
from PIL import Image, ImageGrab
import threading
import queue
import time
import sys
import os
import json
from datetime import datetime
from pynput import keyboard
from transformers import AutoProcessor
from gui_actor.modeling import Qwen2VLForConditionalGenerationWithPointer
from gui_actor.inference import inference

if sys.platform == 'darwin':
    import platform
    # tk deprecation noise on apple silicon. best effort placement
    if platform.machine() == 'arm64':
        os.environ['TK_SILENCE_DEPRECATION'] = '1'

MODEL_PATH = "microsoft/GUI-Actor-2B-Qwen2-VL"
TOPK_PREDICTIONS = 3
CONFIDENCE_THRESHOLD = 0.7
ACTION_DELAY = 0.5
SCREEN_SCALE = 1.0
# cap screenshot to avoid mps oom on retina displays
MAX_SCREENSHOT_SIZE = 768
LOG_DIR = "command_logs"

agent_running = False
stop_agent = False
status_queue = queue.Queue()
command_queue = queue.Queue()
command_counter = 0

class CommandLogger:
    """Logger for capturing all command execution details"""
    
    def __init__(self, base_dir=LOG_DIR):
        self.base_dir = base_dir
        self.current_log_dir = None
        self.log_data = {}
        
    def start_command_log(self, command_num, command_text):
        """Initialize a new command log directory"""
        os.makedirs(self.base_dir, exist_ok=True)
        self.current_log_dir = os.path.join(self.base_dir, f"command_{command_num}")
        os.makedirs(self.current_log_dir, exist_ok=True)
        self.log_data = {
            "command_number": command_num,
            "command_text": command_text,
            "timestamp": datetime.now().isoformat(),
            "parsed_action": None,
            "screenshot_path": None,
            "vlm_request": None,
            "vlm_response": None,
            "predicted_points": [],
            "selected_point": None,
            "execution_result": None,
            "errors": [],
            "debug_screenshot_path": None
        }
        log_status(f"📁 Logging to: {self.current_log_dir}")
        
    def log_parsed_action(self, action_dict):
        """Log the parsed action"""
        self.log_data["parsed_action"] = action_dict
        
    def log_screenshot(self, screenshot):
        """Save the screenshot sent to VLM"""
        if screenshot and self.current_log_dir:
            screenshot_path = os.path.join(self.current_log_dir, "screenshot.png")
            screenshot.save(screenshot_path)
            self.log_data["screenshot_path"] = screenshot_path
            log_status(f"💾 Screenshot saved: {screenshot_path}")
            return screenshot_path
        return None
    
    def log_vlm_request(self, instruction, screenshot_info):
        """Log the VLM request details"""
        self.log_data["vlm_request"] = {
            "instruction": instruction,
            "screenshot_size": screenshot_info,
            "model": MODEL_PATH,
            "topk": TOPK_PREDICTIONS
        }
    
    def log_vlm_response(self, prediction):
        """Log the VLM response"""
        if prediction:
            response_data = {}
            if 'topk_points' in prediction:
                response_data['topk_points'] = [
                    {"x": float(x), "y": float(y)} 
                    for x, y in prediction['topk_points']
                ]
                self.log_data["predicted_points"] = response_data['topk_points']
            
            if 'topk_scores' in prediction:
                response_data['topk_scores'] = [float(s) for s in prediction['topk_scores']]
            
            if 'response' in prediction:
                response_data['response'] = prediction['response']
            
            self.log_data["vlm_response"] = response_data
            log_status(f"🧠 VLM response logged")
    
    def log_selected_point(self, x, y, pixel_x, pixel_y):
        """Log the selected click point"""
        self.log_data["selected_point"] = {
            "normalized": {"x": float(x), "y": float(y)},
            "pixel": {"x": int(pixel_x), "y": int(pixel_y)}
        }
    
    def log_debug_screenshot(self, debug_path):
        """Log the debug screenshot path"""
        if debug_path and self.current_log_dir:
            import shutil
            dest_path = os.path.join(self.current_log_dir, "debug_annotated.png")
            shutil.copy(debug_path, dest_path)
            self.log_data["debug_screenshot_path"] = dest_path
            log_status(f"💾 Debug screenshot copied to: {dest_path}")
    
    def log_execution_result(self, success, action_type, details=None):
        """Log the execution result"""
        self.log_data["execution_result"] = {
            "success": success,
            "action_type": action_type,
            "details": details
        }
    
    def log_error(self, error_message):
        """Log an error"""
        self.log_data["errors"].append({
            "timestamp": datetime.now().isoformat(),
            "message": error_message
        })
    
    def finalize_log(self):
        """Save the complete log to JSON file"""
        if self.current_log_dir:
            log_file = os.path.join(self.current_log_dir, "command_log.json")
            with open(log_file, 'w') as f:
                json.dump(self.log_data, f, indent=2)
            log_status(f"💾 Command log saved: {log_file}")
            summary_file = os.path.join(self.current_log_dir, "summary.txt")
            with open(summary_file, 'w') as f:
                f.write(f"Command #{self.log_data['command_number']}\n")
                f.write(f"{'='*60}\n\n")
                f.write(f"Command: {self.log_data['command_text']}\n")
                f.write(f"Timestamp: {self.log_data['timestamp']}\n\n")
                if self.log_data['parsed_action']:
                    f.write(f"Parsed Action:\n")
                    f.write(f"  Type: {self.log_data['parsed_action'].get('type')}\n")
                    for key, value in self.log_data['parsed_action'].items():
                        if key != 'type':
                            f.write(f"  {key}: {value}\n")
                    f.write("\n")
                if self.log_data['vlm_request']:
                    f.write(f"VLM Request:\n")
                    f.write(f"  Instruction: {self.log_data['vlm_request']['instruction']}\n")
                    f.write(f"  Screenshot Size: {self.log_data['vlm_request']['screenshot_size']}\n\n")
                if self.log_data['predicted_points']:
                    f.write(f"Predicted Points:\n")
                    for i, point in enumerate(self.log_data['predicted_points']):
                        f.write(f"  #{i+1}: ({point['x']:.4f}, {point['y']:.4f})\n")
                    f.write("\n")
                if self.log_data['selected_point']:
                    f.write(f"Selected Point:\n")
                    f.write(f"  Normalized: ({self.log_data['selected_point']['normalized']['x']:.4f}, "
                           f"{self.log_data['selected_point']['normalized']['y']:.4f})\n")
                    f.write(f"  Pixel: ({self.log_data['selected_point']['pixel']['x']}, "
                           f"{self.log_data['selected_point']['pixel']['y']})\n\n")
                if self.log_data['execution_result']:
                    f.write(f"Execution Result:\n")
                    f.write(f"  Success: {self.log_data['execution_result']['success']}\n")
                    f.write(f"  Action Type: {self.log_data['execution_result']['action_type']}\n")
                    if self.log_data['execution_result']['details']:
                        f.write(f"  Details: {self.log_data['execution_result']['details']}\n")
                    f.write("\n")
                if self.log_data['errors']:
                    f.write(f"Errors:\n")
                    for error in self.log_data['errors']:
                        f.write(f"  [{error['timestamp']}] {error['message']}\n")
                    f.write("\n")
                f.write(f"Files:\n")
                f.write(f"  - screenshot.png: Original screenshot sent to VLM\n")
                if self.log_data['debug_screenshot_path']:
                    f.write(f"  - debug_annotated.png: Screenshot with predicted points marked\n")
                f.write(f"  - command_log.json: Complete log data in JSON format\n")
            log_status(f"💾 Summary saved: {summary_file}")

command_logger = CommandLogger()

class VLMModel:
    """Vision-Language Model wrapper for GUI grounding"""
    
    def __init__(self):
        self.model = None
        self.processor = None
        self.tokenizer = None
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        
    def load(self):
        """Load the GUI-Actor model"""
        log_status("🔄 Loading GUI-Actor-2B model...")
        log_status(f"   Device: {self.device}")
        try:
            if self.device == "mps":
                torch.mps.empty_cache()
            self.processor = AutoProcessor.from_pretrained(MODEL_PATH)
            self.tokenizer = self.processor.tokenizer
            # let accelerate place weights; helps small mac setups
            self.model = Qwen2VLForConditionalGenerationWithPointer.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True,
            ).eval()
            # enabling in eval is a bit hacky but reduces mem spikes
            if hasattr(self.model, 'gradient_checkpointing_enable'):
                try:
                    self.model.gradient_checkpointing_enable()
                    log_status("   ✓ Gradient checkpointing enabled")
                except:
                    pass
            log_status(f"   Model device: {next(self.model.parameters()).device}")
            log_status("✅ Model loaded successfully!")
            return True
        except Exception as e:
            log_status(f"❌ Error loading model: {str(e)}")
            import traceback
            log_status(f"   Traceback: {traceback.format_exc()}")
            return False
    
    def predict_click_location(self, screenshot, instruction):
        """Predict where to click based on instruction"""
        try:
            if screenshot.mode != 'RGB':
                screenshot = screenshot.convert('RGB')
            conversation = [
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "text",
                            "text": "You are a GUI agent. You are given a task and a screenshot of the screen. You need to perform a series of pyautogui actions to complete the task.",
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": screenshot,
                        },
                        {
                            "type": "text",
                            "text": instruction
                        },
                    ],
                },
            ]
            log_status(f"🧠 Running model inference...")
            # mps allocator is quirky; clearing cache reduces random oom
            if self.device == "mps":
                torch.mps.empty_cache()
            pred = inference(
                conversation, 
                self.model, 
                self.tokenizer, 
                self.processor, 
                use_placeholder=True, 
                topk=TOPK_PREDICTIONS
            )
            if self.device == "mps":
                torch.mps.empty_cache()
            return pred
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                log_status(f"❌ Out of memory error. Try reducing screenshot size.")
            else:
                log_status(f"❌ Runtime error: {str(e)}")
            return None
        except TypeError as e:
            if "'NoneType' object is not subscriptable" in str(e):
                log_status(f"❌ Model generation failed - likely MPS memory issue")
                log_status(f"   Try: 1) Reduce MAX_SCREENSHOT_SIZE, 2) Restart Python, 3) Close other apps")
            else:
                log_status(f"❌ Type error: {str(e)}")
            import traceback
            log_status(f"   Traceback: {traceback.format_exc()}")
            return None
        except Exception as e:
            log_status(f"❌ Prediction error: {str(e)}")
            import traceback
            log_status(f"   Traceback: {traceback.format_exc()}")
            return None

def take_screenshot():
    """Capture the current screen and resize if needed"""
    try:
        screenshot = ImageGrab.grab()
        width, height = screenshot.size
        # resize is a pragmatic cap, trading fidelity for stability on mps
        if width > MAX_SCREENSHOT_SIZE or height > MAX_SCREENSHOT_SIZE:
            if width > height:
                new_width = MAX_SCREENSHOT_SIZE
                new_height = int(height * (MAX_SCREENSHOT_SIZE / width))
            else:
                new_height = MAX_SCREENSHOT_SIZE
                new_width = int(width * (MAX_SCREENSHOT_SIZE / height))
            log_status(f"📐 Resizing screenshot from {width}x{height} to {new_width}x{new_height}")
            screenshot = screenshot.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            log_status(f"📐 Screenshot size: {width}x{height}")
        return screenshot
    except Exception as e:
        log_status(f"❌ Screenshot error: {str(e)}")
        return None

def show_click_visualization(x, y, duration=2.0):
    """Show a visual indicator at the click location"""
    try:
        overlay = tk.Toplevel()
        overlay.attributes('-topmost', True)
        overlay.attributes('-transparent', True)
        overlay.attributes('-alpha', 0.9)
        overlay.overrideredirect(True)
        overlay.config(bg='systemTransparent')
        size = 300
        overlay.geometry(f"{size}x{size}+{x-size//2}+{y-size//2}")
        canvas = tk.Canvas(overlay, width=size, height=size, bg='systemTransparent', highlightthickness=0)
        canvas.pack()
        center = size // 2
        canvas.create_oval(20, 20, size-20, size-20, outline='red', width=8)
        canvas.create_oval(60, 60, size-60, size-60, outline='red', width=6)
        canvas.create_oval(100, 100, size-100, size-100, outline='red', width=4)
        canvas.create_oval(center-10, center-10, center+10, center+10, fill='red', outline='red')
        canvas.create_line(center, 0, center, size, fill='red', width=3)
        canvas.create_line(0, center, size, center, fill='red', width=3)
        text_width = 120
        text_height = 30
        canvas.create_rectangle(center-text_width//2, 10, center+text_width//2, 10+text_height, 
                              fill='black', outline='red', width=2)
        canvas.create_text(center, 25, text=f"{x},{y}", fill='white', font=('Monaco', 14, 'bold'))
        overlay.after(int(duration * 1000), overlay.destroy)
        return overlay
    except Exception as e:
        log_status(f"⚠️  Visualization error: {str(e)}")
        return None

def move_and_click(x, y, screenshot_size=None, show_visual=True):
    """Move mouse to coordinates and click
    
    Args:
        x, y: Normalized coordinates (0-1) predicted by VLM relative to the screenshot
        screenshot_size: (width, height) of the screenshot the VLM analyzed
        show_visual: Whether to show visual indicator
    """
    try:
        screen_width, screen_height = pyautogui.size()
        if screenshot_size:
            screenshot_width, screenshot_height = screenshot_size
            log_status(f"   Screenshot dimensions: {screenshot_width}x{screenshot_height}")
            log_status(f"   Screen dimensions (logical): {screen_width}x{screen_height}")
            screenshot_x = x * screenshot_width
            screenshot_y = y * screenshot_height
            # mapping screenshot space -> logical screen; retina vs logical px are messy
            scale_x = screen_width / screenshot_width
            scale_y = screen_height / screenshot_height
            pixel_x = int(screenshot_x * scale_x * SCREEN_SCALE)
            pixel_y = int(screenshot_y * scale_y * SCREEN_SCALE)
            log_status(f"   Screenshot coords: ({screenshot_x:.1f}, {screenshot_y:.1f})")
            log_status(f"   Scale factors: ({scale_x:.3f}, {scale_y:.3f})")
            log_status(f"   Logical coords (for pyautogui): ({pixel_x}, {pixel_y})")
        else:
            pixel_x = int(x * screen_width * SCREEN_SCALE)
            pixel_y = int(y * screen_height * SCREEN_SCALE)
        log_status(f"🖱️  Moving to ({pixel_x}, {pixel_y})")
        log_status(f"   Screen size (logical): {screen_width}x{screen_height}")
        log_status(f"   Normalized coords: ({x:.4f}, {y:.4f})")
        # visualization disabled on macos due to overlay glitches
        # move
        pyautogui.moveTo(pixel_x, pixel_y, duration=0.3)
        time.sleep(1.0)
        actual_x, actual_y = pyautogui.position()
        log_status(f"🔍 Verification:")
        log_status(f"   Target position: ({pixel_x}, {pixel_y})")
        log_status(f"   Actual position: ({actual_x}, {actual_y})")
        # loose threshold; just a smoke alarm for scaling mismatch
        error_x = abs(actual_x - pixel_x)
        error_y = abs(actual_y - pixel_y)
        log_status(f"   Position error: ({error_x}, {error_y}) pixels")
        if error_x > 5 or error_y > 5:
            log_status(f"⚠️  WARNING: Mouse position error > 5 pixels!")
            log_status(f"   This might indicate a coordinate system mismatch")
        pyautogui.click()
        log_status(f"✅ Clicked at actual position ({actual_x}, {actual_y})")
        return True
    except Exception as e:
        log_status(f"❌ Click error: {str(e)}")
        return False

def type_text(text):
    """Type text at current cursor location"""
    try:
        log_status(f"⌨️  Typing: {text}")
        pyautogui.write(text, interval=0.05)
        log_status(f"✅ Text typed successfully")
        return True
    except Exception as e:
        log_status(f"❌ Typing error: {str(e)}")
        return False

def press_key(key):
    """Press a keyboard key"""
    try:
        log_status(f"⌨️  Pressing key: {key}")
        pyautogui.press(key)
        log_status(f"✅ Key pressed")
        return True
    except Exception as e:
        log_status(f"❌ Key press error: {str(e)}")
        return False

def parse_command(command):
    """Parse natural language command into action type and parameters"""
    command_lower = command.lower().strip()
    if any(word in command_lower for word in ['click', 'tap', 'press', 'select']):
        target = command_lower
        for word in ['click', 'tap', 'press', 'select', 'on', 'the', 'a', 'an']:
            target = target.replace(word, '')
        target = target.strip()
        return {'type': 'click', 'target': command}
    elif any(word in command_lower for word in ['type', 'write', 'enter']):
        import re
        quoted = re.search(r"['\"](.+?)['\"]", command)
        if quoted:
            text = quoted.group(1)
            return {'type': 'type', 'text': text}
        for word in ['type', 'write', 'enter']:
            if word in command_lower:
                parts = command_lower.split(word, 1)
                if len(parts) > 1:
                    text = parts[1].strip().split(' in ')[0].strip()
                    return {'type': 'type', 'text': text}
        return {'type': 'type', 'text': command}
    elif 'command' in command_lower or 'ctrl' in command_lower:
        return {'type': 'shortcut', 'command': command}
    else:
        return {'type': 'click', 'target': command}

def save_debug_screenshot(screenshot, points, instruction):
    """Save screenshot with predicted click locations marked"""
    try:
        from PIL import ImageDraw, ImageFont
        debug_img = screenshot.copy()
        draw = ImageDraw.Draw(debug_img)
        for i, (x, y) in enumerate(points[:3]):
            pixel_x = int(x * screenshot.width)
            pixel_y = int(y * screenshot.height)
            radius = 20
            color = ['red', 'orange', 'yellow'][i]
            draw.ellipse([pixel_x-radius, pixel_y-radius, pixel_x+radius, pixel_y+radius], 
                        outline=color, width=3)
            draw.line([pixel_x-radius-10, pixel_y, pixel_x+radius+10, pixel_y], fill=color, width=2)
            draw.line([pixel_x, pixel_y-radius-10, pixel_x, pixel_y+radius+10], fill=color, width=2)
            label = f"#{i+1}: ({pixel_x},{pixel_y})"
            draw.text((pixel_x+radius+5, pixel_y-10), label, fill=color)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"debug_click_{timestamp}.png"
        debug_img.save(filename)
        log_status(f"💾 Debug screenshot saved: {filename}")
        return filename
    except Exception as e:
        log_status(f"⚠️  Could not save debug screenshot: {str(e)}")
        return None

def execute_action(action_dict, vlm_model, screenshot=None):
    """Execute a parsed action
    
    Args:
        action_dict: Dictionary with action type and parameters
        vlm_model: The VLM model instance
        screenshot: Optional PIL Image to use (if None, will take a new screenshot)
    """
    global stop_agent
    if stop_agent:
        return False
    action_type = action_dict.get('type')
    command_logger.log_parsed_action(action_dict)
    if action_type == 'click':
        if screenshot is None:
            log_status(f"📸 Taking screenshot...")
            screenshot = take_screenshot()
            if screenshot is None:
                command_logger.log_error("Failed to take screenshot")
                return False
        else:
            log_status(f"📸 Using provided screenshot ({screenshot.width}x{screenshot.height})")
        command_logger.log_screenshot(screenshot)
        instruction = action_dict.get('target', '')
        log_status(f"🤖 Analyzing: '{instruction}'")
        screenshot_info = f"{screenshot.width}x{screenshot.height}"
        command_logger.log_vlm_request(instruction, screenshot_info)
        prediction = vlm_model.predict_click_location(screenshot, instruction)
        command_logger.log_vlm_response(prediction)
        if prediction and 'topk_points' in prediction:
            points = prediction['topk_points']
            if len(points) > 0:
                x, y = points[0]
                log_status(f"🎯 Predicted location: ({x:.4f}, {y:.4f})")
                debug_path = save_debug_screenshot(screenshot, points, instruction)
                if debug_path:
                    command_logger.log_debug_screenshot(debug_path)
                screenshot_size = (screenshot.width, screenshot.height)
                pixel_x = int(x * screenshot.width * SCREEN_SCALE)
                pixel_y = int(y * screenshot.height * SCREEN_SCALE)
                command_logger.log_selected_point(x, y, pixel_x, pixel_y)
                time.sleep(ACTION_DELAY)
                success = move_and_click(x, y, screenshot_size=screenshot_size)
                command_logger.log_execution_result(success, 'click', 
                    f"Clicked at ({pixel_x}, {pixel_y})")
                return success
            else:
                error_msg = "No click location found"
                log_status(f"⚠️  {error_msg}")
                command_logger.log_error(error_msg)
                command_logger.log_execution_result(False, 'click', error_msg)
                return False
        else:
            error_msg = "Prediction failed"
            log_status(f"⚠️  {error_msg}")
            command_logger.log_error(error_msg)
            command_logger.log_execution_result(False, 'click', error_msg)
            return False
    elif action_type == 'type':
        text = action_dict.get('text', '')
        time.sleep(ACTION_DELAY)
        success = type_text(text)
        command_logger.log_execution_result(success, 'type', f"Typed: {text}")
        return success
    elif action_type == 'shortcut':
        command = action_dict.get('command', '')
        if 'command+t' in command.lower() or 'ctrl+t' in command.lower():
            pyautogui.hotkey('command', 't')
            log_status(f"✅ Executed shortcut: Cmd+T")
            command_logger.log_execution_result(True, 'shortcut', 'Cmd+T')
            return True
        else:
            error_msg = f"Shortcut not implemented: {command}"
            log_status(f"⚠️  {error_msg}")
            command_logger.log_error(error_msg)
            command_logger.log_execution_result(False, 'shortcut', error_msg)
            return False
    return False

def run_agent_task(command, vlm_model):
    """Run a single agent task"""
    global stop_agent, command_counter
    command_counter += 1
    log_status(f"\n{'='*60}")
    log_status(f"📋 New Command #{command_counter}: {command}")
    log_status(f"{'='*60}")
    command_logger.start_command_log(command_counter, command)
    try:
        action = parse_command(command)
        log_status(f"🔍 Action type: {action['type']}")
        success = execute_action(action, vlm_model)
        if success:
            log_status(f"✅ Task completed successfully")
        else:
            log_status(f"⚠️  Task failed or was interrupted")
    except Exception as e:
        error_msg = f"Exception during execution: {str(e)}"
        log_status(f"❌ {error_msg}")
        command_logger.log_error(error_msg)
        success = False
    finally:
        command_logger.finalize_log()
        log_status(f"{'='*60}\n")
    return success

class StatusWindow:
    """Thread-safe status window using Tkinter"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🤖 GUI Agent Status")
        self.root.geometry("800x600")
        self.ready = False
        self.vlm_model = None
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            width=90,
            height=35,
            font=("Monaco", 11),
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white"
        )
        self.text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        control_frame = tk.Frame(self.root, bg="#2d2d2d")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        self.status_label = tk.Label(
            control_frame,
            text="🟢 Agent Ready",
            font=("Monaco", 12, "bold"),
            bg="#2d2d2d",
            fg="#00ff00"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        help_label = tk.Label(
            control_frame,
            text="Press ESC to stop the agent",
            font=("Monaco", 10),
            bg="#2d2d2d",
            fg="#ffaa00"
        )
        help_label.pack(side=tk.RIGHT, padx=10)
        self.append_text("🤖 GUI Agent Initialized\n")
        self.append_text("=" * 60 + "\n")
        self.append_text("Press ESC at any time to stop the agent\n")
        self.append_text("=" * 60 + "\n\n")
        self.ready = True
        self.root.after(100, self.update_status)
    
    def append_text(self, text):
        """Append text to the status window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_area.insert(tk.END, f"[{timestamp}] {text}\n")
        self.text_area.see(tk.END)
    
    def update_status(self):
        """Update status from queue (thread-safe)"""
        global agent_running, stop_agent
        try:
            while True:
                message = status_queue.get_nowait()
                self.append_text(message)
        except queue.Empty:
            pass
        try:
            while True:
                command = command_queue.get_nowait()
                self.process_command(command)
        except queue.Empty:
            pass
        if stop_agent:
            self.status_label.config(text="🔴 Agent Stopped", fg="#ff0000")
        elif agent_running:
            self.status_label.config(text="🟢 Agent Running", fg="#00ff00")
        else:
            self.status_label.config(text="🟡 Agent Ready", fg="#ffaa00")
        self.root.after(100, self.update_status)
    
    def process_command(self, command):
        """Process a command from stdin"""
        global agent_running, stop_agent
        if command.lower() in ['quit', 'exit', 'stop']:
            log_status("👋 Exiting...")
            stop_agent = True
            self.root.quit()
        else:
            agent_running = True
            run_agent_task(command, self.vlm_model)
            agent_running = False
        if not stop_agent:
            sys.stderr.write("\n🎤 Command: ")
            sys.stderr.flush()
    
    def run(self):
        """Start the Tkinter main loop"""
        self.root.mainloop()

def log_status(message):
    """Thread-safe status logging"""
    status_queue.put(message)
    print(message)

def stdin_reader_thread():
    """Background thread to read stdin commands"""
    global stop_agent
    time.sleep(1)
    while not stop_agent:
        try:
            # non-blocking stdin so tk mainloop never stalls
            import select
            if select.select([sys.stdin], [], [], 0.1)[0]:
                command = sys.stdin.readline().strip()
                if command:
                    command_queue.put(command)
        except EOFError:
            break
        except Exception as e:
            if not stop_agent:
                log_status(f"⚠️  Input error: {e}")
            break

def on_key_release(key):
    """Handle keyboard events"""
    global stop_agent, agent_running
    try:
        if key == keyboard.Key.esc:
            log_status("\n🛑 ESC pressed - Stopping agent...")
            stop_agent = True
            agent_running = False
            return False
    except:
        pass

def start_keyboard_listener():
    """Start listening for ESC key"""
    listener = keyboard.Listener(on_release=on_key_release, suppress=False)
    listener.start()
    return listener

def agent_worker(status_window):
    """Background worker thread for agent tasks"""
    global agent_running, stop_agent
    while not status_window.ready:
        time.sleep(0.1)
    time.sleep(0.5)
    import io
    stderr_backup = sys.stderr
    sys.stderr = io.StringIO()
    log_status("⌨️  Starting keyboard listener (ESC to stop)...")
    kb_listener = start_keyboard_listener()
    sys.stderr = stderr_backup
    vlm_model = VLMModel()
    if not vlm_model.load():
        log_status("❌ Failed to load model. Exiting.")
        stop_agent = True
        return
    log_status("\n✅ Agent is ready!")
    log_status("💡 Enter commands in terminal, or type 'quit' to exit\n")
    status_window.vlm_model = vlm_model
    stdin_thread = threading.Thread(target=stdin_reader_thread, daemon=True)
    stdin_thread.start()
    sys.stderr.write("\n🎤 Command: ")
    sys.stderr.flush()
    while not stop_agent:
        time.sleep(0.1)

def main():
    """Main program entry point"""
    global agent_running, stop_agent
    print("\n" + "="*60)
    print("🤖 Autonomous GUI Agent")
    print("   Using GUI-Actor-2B-Qwen2-VL")
    print("="*60 + "\n")
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.5
    print("⚠️  IMPORTANT macOS Permissions:")
    print("   1. System Settings > Privacy & Security > Accessibility")
    print("      - Add Terminal or your Python executable")
    print("   2. System Settings > Privacy & Security > Screen Recording")
    print("      - Add Terminal or your Python executable")
    print("\n")
    print("📱 Status window opening...\n")
    status_window = StatusWindow()
    status_window.root.update_idletasks()
    status_window.root.update()
    worker_thread = threading.Thread(target=agent_worker, args=(status_window,), daemon=True)
    worker_thread.start()
    try:
        status_window.run()
    except KeyboardInterrupt:
        stop_agent = True
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ GUI Error: {e}")
        import traceback
        traceback.print_exc()
        stop_agent = True

if __name__ == "__main__":
    # we rely on esc listener instead of pyautogui corner failsafe
    pyautogui.FAILSAFE = False
    main()