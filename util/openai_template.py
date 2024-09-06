
import base64
import requests
from dotenv import load_dotenv
import os

load_dotenv()

# OpenAI API Key
api_key = os.getenv("OPENAI_API_KEY")

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

# Path to your image
image_path = os.path.join('.','borzoi_test.jpg')

# Getting the base64 string
base64_image = encode_image(image_path)

headers = {
  "Content-Type": "application/json",
  "Authorization": f"Bearer {api_key}"
}

payload = {
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "Could you please describe me what this is?."
        },
        {
          "type": "image_url",
          "image_url": {
            "url": f"data:image/jpeg;base64,{base64_image}"
          }
        }
      ]
    }
  ],
  "max_tokens": 300
}

response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
response_json = response.json()
message = response_json['choices'][0]['message']['content']


off_keywords = ["unusual", "off", "weird", "strange", "surreal", "disconnection", "odd"]
is_off = any(keyword in message.lower() for keyword in off_keywords)

print(response_json)
print(message)
print(is_off)
