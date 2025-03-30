""" * This script includes the system functions that are used by the AI Computer Use Agent.
    * The functions include logging, window management, and other utility functions.
    * Developed by: Piyush Suteri
    * Know More: https://youtube.com/@piyushsuteri
"""


# *------------------------IMPORTING MODULES-----------------------*
import time
import logging
import pygetwindow as gw
from pywinauto import Application
import sys


# *------------------------GLOBAL VARIABLES------------------------*
LOGGING_ENABLED = True
SMOOTH_WINDOW_INTERVAL = 1
TIMEOUT = 30


# *-----------------------CONFIGURE LOGGING------------------------*
# Create custom loggers
file_logger = logging.getLogger('file_logger')
console_logger = logging.getLogger('console_logger')

# Configure file logger
file_handler = logging.FileHandler('logs/main.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
file_logger.addHandler(file_handler)
file_logger.setLevel(logging.INFO)

# Configure console logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(message)s'))
console_logger.addHandler(console_handler)
console_logger.setLevel(logging.INFO)


# *------------------------SYSTEM FUNCTIONS------------------------*
def log(message, level='info'):
    """ Custom logging function that logs to both file and console """
    if not LOGGING_ENABLED:
        return

    # Format the message
    formatted_msg = {
        'info': f"[INFO] {message}",
        'warning': f"[WARN] {message}",
        'error': f"[ERROR] {message}"
    }.get(level, f"[INFO] {message}")

    # Log to file
    file_logger.info(formatted_msg)

    # Log to console
    console_logger.info(formatted_msg)


def toggle_logging():
    """ Toggle logging on/off """
    global LOGGING_ENABLED
    LOGGING_ENABLED = not LOGGING_ENABLED
    log(f"Logging {'enabled' if LOGGING_ENABLED else 'disabled'}")


def call_with_retry(func, max_attempts=3, delay=1, *args, **kwargs):
    """Retry error-prone functions with a delay if they fail"""
    for attempts in range(max_attempts):
        try:
            if func(*args, **kwargs):
                return True
            else:
                attempts += 1
            time.sleep(delay)
        except Exception as e:
            attempts += 1
            log(
                f"[call_with_retry()] Attempt {attempts} failed: {e}", 'error')
            time.sleep(delay)

    log(f"[call_with_retry()] Function {func.__name__} failed after {max_attempts} attempts. Exiting with error code 1", 'error')
    sys.exit(1)


def focus_window(title):
    """Function to focus on a window by its title"""
    try:
        app = Application().connect(title=title)
        window = app.window(title=title)
        if window.exists():
            window.set_focus()
            time.sleep(SMOOTH_WINDOW_INTERVAL)
            return True
        else:
            return False
    except Exception as e:
        log(
            f"[focus_window()] Failed to focus window {title}: {e}", 'error')
        return False


def minimize_window(title):
    """Minimize a window by its exact title"""
    try:
        windows = gw.getAllWindows()
        for win in windows:
            if win.title.lower() == title.lower():  # Exact match (case insensitive)
                win.minimize()  # Minimize the window
                time.sleep(SMOOTH_WINDOW_INTERVAL)
                return True
        return False
    except Exception as e:
        log(
            f"[minimize_window()] Failed to minimize window {title}: {e}", 'error')
        return False


# *------------------------MAIN FUNCTION------------------------*
if __name__ == "__main__":
    log("System functions loaded successfully.")
