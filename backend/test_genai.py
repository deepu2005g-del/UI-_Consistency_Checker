import os
import asyncio
from dotenv import load_dotenv
load_dotenv(".env")
from PIL import Image
from google import genai
from google.genai import types

async def main():
    try:
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        img = Image.new('RGB', (10, 10), color = 'red')
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=["What color is this?", img],
            config=types.GenerateContentConfig(
                temperature=0.1,
            )
        )
        print("Success:", response.text)
    except Exception as e:
        print("Error:", e)

asyncio.run(main())
