""" * This script includes the functions that are called upon function call by gemini.
    * Developed by: Piyush Suteri
    * Know More: https://youtube.com/@piyushsuteri
"""


# *------------------------IMPORTING MODULES-----------------------*
import subprocess
import json
import os
import threading
import sys
import pygetwindow as gw
from PIL import ImageGrab
import ctypes
from ctypes import windll
from src.element_detection import element_detection
import shutil
import pyautogui


try:
    from src.backend.utils import core_utils
except:
    sys.path.append(os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../")))
    from backend.utils import core_utils

# *------------------------SYSTEM FUNCTIONS------------------------*
current_chat_id = None


def take_screenshot(full_screen: bool = False, minimum_gradient: int = 10, flood_fill_block: int = 5, minimum_element_area: int = 50):
    """
    Takes a screenshot of the active window.
    Args:
        minimum_gradient (int): Minimum gradient value for edge detection.
        flood_fill_block (int): Block size for flood fill algorithm.
        minimum_element_area (int): Minimum area for an element to be detected
    Returns:
        ScreenshotID (int): The ID of the screenshot taken.
    """
    try:
        if not full_screen:
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()

            active_window = gw.getActiveWindow()
            core_utils.log("[take_screenshot()] Taking screenshot.")
            hwnd = active_window._hWnd
            rect = ctypes.wintypes.RECT()
            windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            x, y = rect.left, rect.top
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            image = ImageGrab.grab(bbox=(x, y, x + width, y + height))
        else:
            image = pyautogui.screenshot()

        os.makedirs(
            f"user_data/chats/{current_chat_id}/screenshots", exist_ok=True)
        os.makedirs(
            f"user_data/chats/{current_chat_id}/processed_screenshots", exist_ok=True)

        # Read screenshot from chat folder and create next screenshot ID
        screenshot_id = len(os.listdir(
            f"user_data/chats/{current_chat_id}/screenshots")) + 1

        # Take a screenshot of the window region and save it
        input_path = f"user_data/chats/{current_chat_id}/screenshots/{screenshot_id}.png"
        image.save(input_path)

        # Process screenshot for element detection
        output_path = f"user_data/chats/{current_chat_id}/processed_screenshots/"
        element_detection.process_image(
            input_path, output_path, full_screen, min_grad=minimum_gradient, ffl_block=flood_fill_block, min_ele_area=minimum_element_area)
        return screenshot_id

    except Exception as e:
        core_utils.log(f"[take_screenshot()] Error: {str(e)}", 'error')
        return None


def execute_python_code(code: str, wait_time: int = 20, title: str = 'Executing code...'):
    """
    Executes Python code with a specified wait time, collects output/errors,
    and returns results even if the script is still running.

    Parameters:
        code (str): The Python code to execute.
        wait_time (int): Time in seconds to wait before returning the results.
        title (str): Title of the script that will be shown as status to users.

    Returns:
        str: JSON-formatted string containing output, errors, and return code (if available).
    """
    if not isinstance(code, str) or not code.strip():
        return json.dumps({"error": "Invalid code provided. Must be a non-empty string."})

    # Create absolute paths for directories
    chat_dir = os.path.abspath(f"user_data/chats/{current_chat_id}")
    scripts_dir = os.path.join(chat_dir, "scripts")

    # Ensure directories exist
    os.makedirs(scripts_dir, exist_ok=True)

    script_id = len(os.listdir(scripts_dir)) + 1
    script_path = os.path.join(scripts_dir, f"{script_id}.py")

    try:
        core_utils.log(f"[execute_python_code()] EXECUTING CODE")

        # Copy system function file to scripts folder if not already present
        script_files = os.listdir(scripts_dir)

        if "utils.py" not in script_files:
            shutil.copy("src/backend/utils/script_utils.py",
                        f"{scripts_dir}/utils.py")

        # Create script file
        with open(script_path, 'w') as file:
            file.write(f'import utils\n{code}')

        # Execute the script with subprocess
        process = subprocess.Popen(
            ['python', f'scripts/{script_id}.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=chat_dir
        )

        # Thread-safe container for the output
        result = {"stdout": "", "stderr": "", "return_code": None}

        def read_output():
            try:
                stdout, stderr = process.communicate()
                result["stdout"] = stdout
                result["stderr"] = stderr
                result["return_code"] = process.returncode
            except Exception as e:
                result["error"] = f"Error reading process output: {str(e)}"

        # Run the read_output function in a separate thread
        thread = threading.Thread(target=read_output)
        thread.start()

        # Wait for the specified time
        thread.join(timeout=wait_time)

        # If the thread is still running, the script is still executing
        if thread.is_alive():
            # Do not terminate the process, just return the current state
            return json.dumps({
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": None,
                "status": "Script is still running"
            })

        # If the thread is finished, return the full result
        return json.dumps({
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "return_code": result["return_code"]
        })

    except Exception as e:
        if process:
            process.kill()
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
