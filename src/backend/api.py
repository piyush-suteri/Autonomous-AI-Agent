""" * This script includes the backend API for the Agent.
    * Developed by: Piyush Suteri
    * Know More: https://youtube.com/@piyushsuteri
"""


# *------------------------IMPORT LIBRARIES------------------------*
from flask import Flask, send_from_directory, jsonify
try:
    from flask_socketio import SocketIO, emit
except ImportError:
    raise ImportError("flask-socketio not installed. Run: pip install flask-socketio")

try:
    from flask_cors import CORS
except ImportError:
    raise ImportError("flask-cors not installed. Run: pip install flask-cors")
import os

try:
    from src.backend.utils import core_utils
except:
    from utils import core_utils
try:
    from src.backend.utils import gemini_utils
except:
    from utils import gemini_utils
try:
    from src.backend.utils import agent_func
except:
    from utils import agent_func


# Initialize Flask app with CORS
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


def create_app():
    """Create and configure Flask app"""
    gemini_utils.init_gemini()
    gemini_utils.load_chat_history()  # Load existing chats

    # Add chat history endpoints
    @app.route('/api/chats', methods=['GET'])
    def get_chats(): return gemini_utils.get_chats()

    @app.route('/api/chats/<chat_id>', methods=['GET'])
    def get_chat(chat_id): return gemini_utils.get_chat(chat_id)

    @app.route('/api/chats/<chat_id>', methods=['DELETE'])
    def delete_chat(chat_id): return gemini_utils.delete_chat(chat_id)

    @app.route('/api/chats/<chat_id>/load', methods=['POST'])
    def load_chat(chat_id): return gemini_utils.load_chat(chat_id)

    @app.route('/api/reset', methods=['POST'])
    def reset_chat(): return gemini_utils.reset_chat_session()

    # Update static file serving routes
    @app.route('/')
    def index():
        frontend_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../frontend'))
        core_utils.log(f"[DEBUG] Serving frontend from: {frontend_dir}")
        try:
            return send_from_directory(frontend_dir, 'index.html')
        except Exception as e:
            core_utils.log(
                f"[ERROR] Failed to serve index.html: {str(e)}", 'error')
            return f"Error: Could not find frontend files at {frontend_dir}", 404

    @app.route('/<path:path>')
    def static_files(path):
        frontend_dir = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '../frontend'))
        try:
            return send_from_directory(frontend_dir, path)
        except Exception as e:
            core_utils.log(
                f"[ERROR] Failed to serve {path}: {str(e)}", 'error')
            return f"Error: Could not find {path}", 404

    core_utils.log("[CONFIG] Flask app created successfully")
    return app


@socketio.on('connect')
def handle_connect():
    core_utils.log("[handle_connect()] Client connected")
    emit('connection_response', {'data': 'Connected'})


@socketio.on('disconnect')
def handle_disconnect():
    core_utils.log("[handle_connect()] Client disconnected")


@socketio.on('message')
def handle_message(data):
    try:
        message = data.get('message', '')
        gemini_utils.current_chat_id = data.get('chatId')
        agent_func.current_chat_id = data.get('chatId')

        for event_type, response_data in gemini_utils.chat_loop(message):
            emit(event_type, response_data)

    except Exception as e:
        core_utils.log(f"[handle_message()] Error: {str(e)}", 'error')
        emit('response', {
            'success': False,
            'error': str(e),
            'processing': False
        })


@app.route('/force_stop', methods=['POST'])
def force_stop():
    try:
        gemini_utils.FORCE_STOP = True
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Only run if executed directly
if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True)
