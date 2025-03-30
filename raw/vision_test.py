import os
import PIL.Image
import google.generativeai as genai
import pygetwindow as gw
from PIL import ImageGrab
from io import BytesIO
import ctypes
from ctypes import windll
import time

time_init = time.time()
# Set process DPI awareness
user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

chat_session = model.start_chat(
    history=[]
)

try:
    active_window = gw.getActiveWindow()
    if active_window.title != 'AI Agent':
        # Get the window rect in actual pixels
        hwnd = active_window._hWnd
        rect = ctypes.wintypes.RECT()
        windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        x, y = rect.left, rect.top
        width = rect.right - rect.left
        height = rect.bottom - rect.top
        
        # Take a screenshot of the window region
        screenshot = ImageGrab.grab(
            bbox=(x, y, x + width, y + height))
        # screenshot_io = BytesIO()
        # screenshot.save(screenshot_io, format='PNG')
        # # Reset the pointer to the beginning of the file-like object
        # screenshot_io.seek(0)
        # # Save the screenshot to a file
        screenshot.save("raw/screenshot.png", format='PNG')

except Exception as e:
    print("an error occured", e)
# PIL.Image.open("raw/eg.png"
# screenshot_file = genai.upload_file(screenshot_io, mime_type="image/png")

response = chat_session.send_message(["this is the image. Tell what do you see: ", screenshot])
print(response.text)
print("-------------------------------------------------")
response = chat_session.send_message("Hello")

print(response.text)
print(time.time()-time_init)