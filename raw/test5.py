import pyautogui
import pytesseract
from time import sleep

# Configure pytesseract path (ensure Tesseract is installed)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def locate_and_click_file_button():
    # Take a screenshot of the current screen
    screenshot = pyautogui.screenshot()

    # Use pytesseract to extract text and its positions
    data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)

    # Search for the "File" button
    for i, text in enumerate(data['text']):
        if text.strip().lower() == 'file':
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            # Calculate center of the button and click it
            pyautogui.click(x + w // 2, y + h // 2)
            return True

    return False

def main():
    # Press Win + 5 to open the desired window
    pyautogui.hotkey('win', '5')
    sleep(2)  # Wait for the window to open

    # Locate and click the "File" menu button
    if locate_and_click_file_button():
        print("Successfully clicked the 'File' button.")
    else:
        print("Could not find the 'File' button.")

if __name__ == "__main__":
    main()
