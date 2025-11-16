import google.generativeai as genai

genai.configure(api_key='AIzaSyDMN_LE1wU6IJC5EQqrVSDn6FLaui_N5tg')

print("Available models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")
