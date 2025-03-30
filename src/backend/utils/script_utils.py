import json
import os
import ctypes
from ctypes import windll
import pygetwindow as gw
import logging
from datetime import datetime

# Configure logging
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

logging.basicConfig(
    filename=f'{log_directory}/script_utils_{datetime.now().strftime("%Y%m%d")}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_element_coordinates(element_id):
    """ 
    Returns:
        element_x, element_y: Element's centre coordinates in the last screenshot.
    Raises:
        ValueError: If element_id is invalid or data structure is incorrect
    """
    try:
        # Get last screenshot
        if not os.path.exists("screenshots"):
            logging.error("Screenshots directory not found")
            raise FileNotFoundError("Screenshots directory does not exist")

        screenshots = os.listdir("screenshots")
        if not screenshots:
            logging.error("No screenshots found in directory")
            raise FileNotFoundError("No screenshots available")

        # Extract numbers from filenames and remove .png extension
        last_processed_screenshot = max(
            int(x.replace('.png', '')) for x in screenshots)

        # Load JSON data
        json_path = f"processed_screenshots/{last_processed_screenshot}.json"
        try:
            with open(json_path) as f:
                data = json.load(f)

            # Validate JSON structure
            if 'full_screen' not in data:
                logging.error(
                    f"Invalid JSON structure - missing 'full_screen' key")
                raise ValueError(
                    "Invalid JSON structure - missing 'full_screen' key")

            if 'compos' not in data:
                logging.error(f"Invalid JSON structure - missing 'compos' key")
                raise ValueError(
                    "Invalid JSON structure - missing 'compos' key")

            if not isinstance(data['compos'], list):
                logging.error(
                    f"Invalid JSON structure - 'compos' is not an array")
                raise ValueError(
                    "Invalid JSON structure - 'compos' is not an array")

            if element_id <= 0 or element_id > len(data['compos']):
                logging.error(
                    f"Invalid element_id: {element_id}. Valid range: 1 to {len(data['compos'])}")
                raise ValueError(f"Invalid element_id: {element_id}")

            is_full_screen = data['full_screen']

            element = data['compos'][element_id - 1]
            if 'relative_centre_coordinates' not in element:
                logging.error(
                    f"Element {element_id} missing relative_centre_coordinates")
                raise ValueError(
                    f"Element {element_id} has invalid data structure")

            relative_centre_coordinates = element['relative_centre_coordinates']

            if not isinstance(relative_centre_coordinates, list) or len(relative_centre_coordinates) != 2:
                logging.error(
                    f"Invalid coordinates format for element {element_id}")
                raise ValueError(
                    f"Invalid coordinates format for element {element_id}")

        except FileNotFoundError:
            logging.error(f"Processed screenshot JSON not found: {json_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in processed screenshot: {json_path}")
            raise

        # Get window information
        try:
            if not is_full_screen:
                user32 = ctypes.windll.user32
                user32.SetProcessDPIAware()
                active_window = gw.getActiveWindow()
                if not active_window:
                    logging.error("No active window found")
                    raise RuntimeError("Could not get active window")

                hwnd = active_window._hWnd
                rect = ctypes.wintypes.RECT()
                if not windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    logging.error("Failed to get window rectangle")
                    raise RuntimeError("Failed to get window dimensions")

                x, y = rect.left, rect.top
                width = rect.right - rect.left
                height = rect.bottom - rect.top

                absolute_centre_coordinates = (
                    x + (relative_centre_coordinates[0] * width)/100,
                    y + (relative_centre_coordinates[1] * height)/100
                )

                logging.info(
                    f"Successfully calculated coordinates for element {element_id}")
                return absolute_centre_coordinates[0], absolute_centre_coordinates[1]

            else:
                logging.info(
                    f"Successfully calculated coordinates for element {element_id}")
                return relative_centre_coordinates[0], relative_centre_coordinates[1]

        except Exception as e:
            logging.error(f"Error getting window coordinates: {str(e)}")
            raise

    except Exception as e:
        logging.error(f"Error in get_element_coordinates: {str(e)}")
        raise
