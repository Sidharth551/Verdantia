import os
import time
import io
from dotenv import load_dotenv
from PIL import Image
import google.generativeai as genai

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found. Please set it in your .env file.")
genai.configure(api_key=GEMINI_API_KEY)

# Gemini models
text_model = genai.GenerativeModel("gemini-2.5-flash-lite")
vision_model = genai.GenerativeModel("gemini-1.5-flash")


def ask_gemini(prompt: str, max_retries: int = 2, temperature: float = 0.7) -> str:
    """
    Sends a prompt to Gemini text model and returns a mission-focused recycling response.
    """
    system_prompt = (
        "You are Verdantia AI, a friendly and knowledgeable recycling assistant created to help users dispose of items properly.\n"
        "Your responsibilities:\n"
        "1. ♻️ Identify the item from the user prompt\n"
        "2. ✅ Determine the correct disposal method (recycle, compost, landfill, e-waste, hazardous, etc)\n"
        "3. 🧾 Educate the user with clear, useful disposal instructions\n"
        "4. 🌍 Briefly explain why proper disposal is important (e.g., environmental impact)\n"
        "5. 🚫 NEVER answer unrelated questions, NEVER say 'check locally' unless absolutely necessary\n"
        "Respond like a real human recycling assistant — use clear formatting (bullets or points) and limit to ~120 words.\n"
    )

    full_prompt = f"{system_prompt}\nUser: {prompt}"

    for attempt in range(max_retries):
        try:
            response = text_model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": 384
                }
            )
            if hasattr(response, "text"):
                return response.text.strip()
            return "❌ Gemini returned an unexpected response."
        except Exception as e:
            print(f"[ask_gemini error] Attempt {attempt + 1}: {str(e)}")
            time.sleep(1)

    return "⚠️ Sorry, I couldn't respond right now. Please try again shortly."


def classify_item_with_ai(item_description: str) -> str:
    """
    Classifies a user-described item and provides disposal guidance.
    """
    prompt = (
        f"Item description: \"{item_description}\"\n\n"
        f"Classify this item into one of: Plastic, Paper, Metal, Glass, E-Waste, Organic/Compost, Hazardous, Mixed, or Landfill.\n"
        f"Then provide:\n"
        f"- ✅ Its category\n"
        f"- 🧾 How to dispose of it safely\n"
        f"- ♻️ Quick education on the material's environmental impact\n"
    )
    return ask_gemini(prompt, temperature=0.4)


def classify_image_with_vision_ai(image_pil: Image.Image, max_retries: int = 2) -> str:
    """
    Classifies an item from an image using Gemini Vision and returns an Verdantia AI styled response.
    """
    prompt = (
        "You are Verdantia AI, an expert recycling assistant helping users understand how to properly dispose of the item shown in the image.\n"
        "Your response MUST follow this format:\n\n"
        "Hello there! I'm Verdantia AI, ready to help you with your [item name].\n"
        "Item: [Name of the item].\n"
        "Disposal Method: [e.g. Recyclable, Compost, Landfill, Special Drop-off, etc.]\n"
        "Instructions:\n"
        "- [Step 1]\n"
        "- [Step 2]\n"
        "- [Step 3 (optional)]\n"
        "Why it matters: [Brief, powerful explanation of the environmental impact of proper disposal.]\n\n"
        "Be specific. NEVER say 'check locally' unless absolutely necessary. NEVER return unrelated content.\n"
        "Keep it friendly, professional, and clear. Use relevant emojis."
    )

    # PIL image to PNG byte stream
    image_bytes = io.BytesIO()
    image_pil.save(image_bytes, format="PNG")
    image_data = image_bytes.getvalue()

    for attempt in range(max_retries):
        try:
            response = vision_model.generate_content(
                contents=[
                    prompt,
                    {
                        "mime_type": "image/png",
                        "data": image_data
                    }
                ],
                generation_config={
                    "temperature": 0.4,
                    "max_output_tokens": 1024  # More space for a proper structured response
                }
            )
            if hasattr(response, "text"):
                return response.text.strip()
            return "❌ Gemini Vision returned an unexpected response."

        except Exception as e:
            error_str = str(e)
            print(f"[Vision Model Error] Attempt {attempt + 1} failed: {error_str}")

            if "429" in error_str or "quota" in error_str.lower():
                return (
                    "⚠️ Gemini Vision API quota exceeded.\n"
                    "Try again later or check your API plan.\n"
                    "More info: https://ai.google.dev/gemini-api/docs/rate-limits"
                )

            time.sleep(1)

    return "⚠️ Sorry, I couldn't classify the image at this time. Please try again later."
