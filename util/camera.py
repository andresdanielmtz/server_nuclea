from flask import Blueprint, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
print(api_key)
headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

def process_image(id: str = "[Not an ID]", image_data: str = "[No Image Data]") -> jsonify:
    try:
        if not image_data or image_data == "[No Image Data]":
            return jsonify({"error": "No image data provided"}), 400
        
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Detect whether or not you detect an intruder, add the camera ID {id}. Only say YES or NO.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            },
                        },
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
            return jsonify({
                "error": "OpenAI API Error",
                "details": response_json['error']
            }), 500

        if 'choices' not in response_json or not response_json['choices']:
            return jsonify({
                "error": "Unexpected API response",
                "details": response_json
            }), 500

        message = response_json["choices"][0]["message"]["content"]


        off_keywords = [
            "unusual",
            "off",
            "weird",
            "strange",
            "surreal",
            "disconnection",
            "odd",
        ]
        is_off = any(keyword in message.lower() for keyword in off_keywords)

        return jsonify(
            {"message": message, "is_off": is_off, "full_response": response_json}
        ), 200

    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500