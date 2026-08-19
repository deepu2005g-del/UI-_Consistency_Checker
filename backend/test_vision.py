import asyncio
import logging
from app.services.vision_service import extract_ui_from_screenshot

logging.basicConfig(level=logging.DEBUG)

async def test():
    # Provide a dummy image path
    with open("test.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\x99c\xf8\x0f\x04\x00\x09\xfb\x03\xfd\xe3U\xf2\x9c\x00\x00\x00\x00IEND\xaeB`\x82")
    
    res = await extract_ui_from_screenshot("test.png", "Test Page")
    print("Result:", res)

if __name__ == "__main__":
    asyncio.run(test())
