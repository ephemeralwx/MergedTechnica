import torch
from qwen_vl_utils import process_vision_info  # Optional, but included for completeness
from datasets import load_dataset
from transformers import AutoProcessor  # Use AutoProcessor as per repo
from gui_actor.constants import chat_template
from gui_actor.modeling import Qwen2VLForConditionalGenerationWithPointer
from gui_actor.inference import inference

# Load the 2B model
model_name_or_path = "microsoft/GUI-Actor-2B-Qwen2-VL"
data_processor = AutoProcessor.from_pretrained(model_name_or_path)
tokenizer = data_processor.tokenizer
model = Qwen2VLForConditionalGenerationWithPointer.from_pretrained(
    model_name_or_path,
    torch_dtype=torch.float16,  # Optimized for Apple Silicon
    device_map="auto",  # Auto-uses MPS on M2 Pro
    # No attn_implementation (falls back to MPS-compatible SDPA)
).eval()

# Prepare example (downloads ScreenSpot dataset if needed; ~100 MB)
dataset = load_dataset("rootsautomation/ScreenSpot")["test"]
example = dataset[0]
print(f"Instruction: {example['instruction']}")
print(f"ground-truth action region (x1, y1, x2, y2): {[round(i, 2) for i in example['bbox']]}")

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
                "image": example["image"],  # PIL.Image.Image; replace with your own if needed, e.g., Image.open("path/to/screenshot.png")
                # Or use "image_url": "file:///path/to/image.png" for local files
            },
            {
                "type": "text",
                "text": example["instruction"]
            },
        ],
    },
]

# Run inference (topk=3 for multiple candidate points; adjust as needed)
pred = inference(conversation, model, tokenizer, data_processor, use_placeholder=True, topk=3)
px, py = pred["topk_points"][0]
print(f"Predicted click point: [{round(px, 4)}, {round(py, 4)}]")