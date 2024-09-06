import traceback
from flask import jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
print(api_key)
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

def process_image(image_data: str = "[No Image Data]"):
    try:
        if not image_data or image_data == "[No Image Data]":
            return {"error": "No image data provided"}

        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze the image and if you identify a humanoid red figure, return YES, else if there is no humanoid red figure return NO"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    ],
                }
            ],
            "max_tokens": 300,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions", headers=headers, json=payload
        )
        response_json = response.json()

        if 'error' in response_json:
            return {
                "error": "OpenAI API Error",
                "details": response_json['error']
            }

        if 'choices' not in response_json or not response_json['choices']:
            return {
                "error": "Unexpected API response",
                "details": response_json
            }

        message = response_json["choices"][0]["message"]["content"]

        off_keywords = ["unusual", "off", "weird", "strange", "surreal", "disconnection", "odd"]
        is_off = any(keyword in message.lower() for keyword in off_keywords)

        return {"message": message, "is_off": is_off, "full_response": response_json}

    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
