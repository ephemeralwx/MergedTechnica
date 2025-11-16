#!/usr/bin/env python3
"""
Test script to diagnose model generation issues
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

import torch
from PIL import Image, ImageGrab
from transformers import AutoProcessor
from gui_actor.modeling import Qwen2VLForConditionalGenerationWithPointer

print("="*70)
print("🔍 Model Generation Diagnostic Test")
print("="*70)

# Check device
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"\n✓ Device: {device}")

# Check memory
if device == "mps":
    print(f"✓ MPS available: {torch.backends.mps.is_available()}")
    print(f"✓ MPS built: {torch.backends.mps.is_built()}")

# Load model
print("\n🔄 Loading model...")
MODEL_PATH = "microsoft/GUI-Actor-2B-Qwen2-VL"

try:
    processor = AutoProcessor.from_pretrained(MODEL_PATH)
    tokenizer = processor.tokenizer
    print("✓ Processor loaded")
    
    model = Qwen2VLForConditionalGenerationWithPointer.from_pretrained(
        MODEL_PATH,
        torch_dtype=torch.float16,
        device_map="auto",
        low_cpu_mem_usage=True,
    ).eval()
    print("✓ Model loaded")
    print(f"✓ Model device: {next(model.parameters()).device}")
    
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Take a small screenshot
print("\n📸 Taking screenshot...")
try:
    screenshot = ImageGrab.grab()
    # Resize to small size for testing
    screenshot = screenshot.resize((640, 480), Image.Resampling.LANCZOS)
    print(f"✓ Screenshot size: {screenshot.size}")
except Exception as e:
    print(f"❌ Screenshot failed: {e}")
    exit(1)

# Test inference
print("\n🧠 Testing model inference...")
instruction = "Click on the center of the screen"

from qwen_vl_utils import process_vision_info
from gui_actor.constants import chat_template

conversation = [
    {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": "You are a GUI agent.",
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

try:
    # Prepare inputs
    print("  - Preparing inputs...")
    text = processor.apply_chat_template(
        conversation,
        tokenize=False,
        add_generation_prompt=False,
        chat_template=chat_template
    )
    text += "<|im_start|>assistant<|recipient|>os\npyautogui.click(<|pointer_start|><|pointer_pad|><|pointer_end|>)"
    
    image_inputs, video_inputs = process_vision_info(conversation)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt"
    )
    inputs = inputs.to(model.device)
    print(f"  - Input IDs shape: {inputs['input_ids'].shape}")
    print(f"  - Input device: {inputs['input_ids'].device}")
    
    # Clear cache
    if device == "mps":
        torch.mps.empty_cache()
    
    # Generate
    print("  - Running generation...")
    with torch.no_grad():
        results = model.generate(
            **inputs,
            max_new_tokens=1,
            return_dict_in_generate=True,
            output_hidden_states=True,
            output_scores=True,
        )
    
    print(f"  - Generation complete!")
    print(f"  - Results type: {type(results)}")
    print(f"  - Has sequences: {hasattr(results, 'sequences')}")
    print(f"  - Has hidden_states: {hasattr(results, 'hidden_states')}")
    print(f"  - Has scores: {hasattr(results, 'scores')}")
    
    if hasattr(results, 'sequences'):
        print(f"  - Sequences shape: {results.sequences.shape}")
    if hasattr(results, 'hidden_states'):
        print(f"  - Hidden states length: {len(results.hidden_states)}")
        if len(results.hidden_states) > 0:
            print(f"  - Hidden states[0] length: {len(results.hidden_states[0])}")
    
    print("\n✅ Model generation test PASSED!")
    
except Exception as e:
    print(f"\n❌ Model generation test FAILED!")
    print(f"   Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("✅ All tests passed!")
print("="*70)
