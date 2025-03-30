"""AI Computer Use Agent that allows AI to control your computer on your behalf."""

import threading
from src.backend import api
import webview
import pygetwindow
import time


def start_server():
    """Start the Flask server"""
    app = api.create_app()
    api.socketio.run(app, host='127.0.0.1', port=5000)


def window_manager():
    """Keep the webview window in focus at left side of screen and other apps that open during the session are automatically moved to right i.e. split screen between the two"""
    while True:
        try:
            # Get AI agent window and active window
            ai_window = pygetwindow.getWindowsWithTitle('AI Agent')[0]
            active = pygetwindow.getActiveWindow()

            # Skip if active window is AI agent or if no window is active
            if not active or active.title == 'AI Agent':
                time.sleep(1)
                continue

            # Check if active window overlaps with AI agent window
            if active.left < ai_window.width:
                # Move and resize active window
                new_width = max(400, active.width -
                                (ai_window.width - active.left))
                active.moveTo(ai_window.width + 10, 0)
                time.sleep(0.5)
                active.resizeTo(new_width, active.height)

        except Exception:
            pass

        time.sleep(0.5)


def main():
    # Start Flask server in a separate thread
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    # window_manager_thread = threading.Thread(target=window_manager)
    # window_manager_thread.start()

    # Configure webview window
    window = webview.create_window(
        title='AI Agent',
        url='http://localhost:5000',
        width=450,
        height=830,
        resizable=True,
        text_select=True,
        x=0, y=0
    )

    # Start webview
    webview.start()


if __name__ == '__main__':
    main()
