""" * This script includes utility function_calleds for the backend server.
    * Developed by: Piyush Suteri
    * Know More: https://youtube.com/@piyushsuteri
"""
# TODO: Add system message role for function responses and calls. Add fontend status yield in chat_loop.

# *------------------------IMPORT LIBRARIES------------------------*
import os
import json
import time
from flask import jsonify
import google.generativeai as genai
import sys
import os
from PIL import Image
import shutil

try:
    from src.backend.utils import core_utils
except:
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..')))
    from backend.utils import core_utils
try:
    from src.backend.utils import agent_func
except:
    sys.path.insert(0, os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', '..')))
    from backend.utils import agent_func


# *------------------------GLOBAL VARIABLES------------------------*
CHAT_STORAGE_PATH = 'user_data/chats'
chat_histories = {}
current_chat_id = None
FORCE_STOP = False
chat_session = None
model = None
current_chat_id = None

# Ensure storage directory exists
os.makedirs(CHAT_STORAGE_PATH, exist_ok=True)


# *------------------------SYSTEM FUNCTIONS------------------------*
def init_gemini():
    """Initialize Gemini model and chat session"""
    global chat_session, model
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    # Create the model
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    try:
        with open("assets/prompts/system_prompt.md", "r") as f:
            system_instructions = f.read()
    except Exception as e:
        core_utils.log(
            f"[CONFIG] Error reading system instructions: {e}", 'warning')
        os._exit()

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash-lite",
        generation_config=generation_config,
        system_instruction=system_instructions,
        tools=[agent_func.execute_python_code,
               agent_func.take_screenshot],
    )

    chat_session = model.start_chat(history=[])
    core_utils.log("[CONFIG] Gemini configuration completed successfully")
    return True


def load_chat_history():
    """Load all chat histories from files"""
    try:
        global chat_histories
        chat_histories = {}

        for foldername in os.listdir(CHAT_STORAGE_PATH):
            chat_id = foldername
            with open(os.path.join(CHAT_STORAGE_PATH, foldername, chat_id + '.json'), 'r') as f:
                chat_histories[chat_id] = json.load(f)
        return chat_histories

    except Exception as e:
        core_utils.log(f"[load_chat_history()] {str(e)}", 'error')
        return False


def save_chat_history(chat_id, message, role, save_to_file=True):
    """Save specific chat history to file with proper JSON serialization"""
    try:
        if chat_id in chat_histories:
            filepath = os.path.join(
                CHAT_STORAGE_PATH, f"{chat_id}/{chat_id}.json")
            chat_histories[chat_id]['contents'].append({
                'role': role,
                'parts': [message]
            })
            os.makedirs(os.path.join(
                CHAT_STORAGE_PATH, chat_id), exist_ok=True)
            if save_to_file:
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(chat_histories[chat_id], f,
                                  ensure_ascii=False, indent=2)

                except Exception as e:
                    core_utils.log(
                        f"Error saving chat history: {str(e)}", 'error')

    except Exception as e:
        core_utils.log(f"[save_chat_history()] {str(e)}", 'error')


def generate_chat_title(message):
    """Generate a readable title from the first message"""
    words = message.strip().split()
    title = ' '.join(words[:4])  # Take first 4 words
    return title[:30] + ('...' if len(title) > 30 else '')


def clean_response_text(text):
    """Remove excessive newlines from response text"""
    # Replace multiple newlines with a single newline
    cleaned = '\n'.join(line for line in text.splitlines() if line.strip())
    return cleaned.strip()


def handle_function_call(function_called):
    """Execute function_called calls from Gemini and return the result"""
    try:
        if not function_called:
            core_utils.log(
                "[handle_function_call] Invalid function call object", 'error')
            return None, None

        if function_called.name == "execute_python_code":
            code = function_called.args.get("code")
            timeout = function_called.args.get("timeout") or 20

            if code:
                result = agent_func.execute_python_code(
                    code, wait_time=timeout)
                return result, None
            else:
                return "Invalid code provided", None

        elif function_called.name == "take_screenshot":
            full_screen = function_called.args.get("full_screen") or False
            min_grad = function_called.args.get("minimum_gradient") or 10
            min_ele_area = function_called.args.get(
                "minimum_element_area") or 50
            ffl_block = function_called.args.get("flood_fill_block") or 5
            screenshotID = agent_func.take_screenshot(
                full_screen, min_grad, ffl_block, min_ele_area)

            if screenshotID:
                screenshot = Image.open(
                    f"user_data/chats/{current_chat_id}/processed_screenshots/{screenshotID}.png")

            return None, screenshot

    except Exception as e:
        core_utils.log(f"[handle_function_call()] Error: {str(e)}", 'error')
        return None, None


def send(message, function_response=False, screenshot=None):
    """Improved function for sending message to gemini"""
    try:
        full_response = ""
        function = None
        chat_id = current_chat_id
        if screenshot:
            response = chat_session.send_message([message, screenshot])
            core_utils.log(
                "[send()] Successfuly sent message to gemini with screenshot attached")
        else:
            response = chat_session.send_message(message)
            core_utils.log("[send()] Successfuly sent message to gemini")

        # Process response parts
        for part in response.parts:
            if part.text:
                full_response += part.text.strip()
            elif fn := part.function_call:
                function = fn

        # Clean and store response
        full_response = clean_response_text(full_response)

        if function_response:
            user_message = str(message)
        else:
            user_message = message

        if full_response and function:
            ai_message = ' '.join([full_response, str(function)])
        elif function and not full_response:
            ai_message = str(function)
        else:
            ai_message = full_response

        save_chat_history(chat_id, user_message, 'user', False)
        save_chat_history(chat_id, ai_message, 'model', True)

        return full_response, function

    except Exception as e:
        core_utils.log(f"[send()] Error: {str(e)}", 'error')
        return False, None


def chat_loop(init_msg):
    try:
        global current_chat_id, FORCE_STOP
        FORCE_STOP = False  # Reset force stop flag at start

        is_new_chat = not current_chat_id or (
            current_chat_id not in chat_histories)
        if is_new_chat:
            current_chat_id = str(int(time.time() * 1000))
            agent_func.current_chat_id = current_chat_id
            chat_histories[current_chat_id] = {
                'contents': [],
                'title': generate_chat_title(init_msg)
            }
            core_utils.log("[chat_loop()] New chat created")

        message = init_msg
        max_turns = 20
        turn = 0
        function = None
        screenshot = None

        while turn < max_turns and not FORCE_STOP:  # Check FORCE_STOP in while condition
            turn += 1

            response, function = send(message, function, screenshot)
            screenshot = None
            core_utils.log(
                "[chat_loop()] Successfuly recieved message from gemini")

            if FORCE_STOP:
                break

            # Send initial response to client
            yield ('response', {
                'success': True,
                # Modify processing flag
                'processing': bool(function) and not FORCE_STOP,
                'response': response or '',
                'chatId': current_chat_id,
                'title': chat_histories[current_chat_id]['title'] if is_new_chat else None,
                'status': (function.args.get("title") or ("Executing code..." if function.name == 'execute_python_code' else 'Taking screenshot...')) if function else None,
            })

            if not function or FORCE_STOP:
                break

            # Handle function call
            result, screenshot = handle_function_call(function)
            if result and not FORCE_STOP:
                response_parts = [
                    genai.protos.Part(function_response=genai.protos.FunctionResponse(
                        name="execute_python_code", response={"result": result}))
                ]
                message = response_parts

            elif screenshot and not FORCE_STOP:
                message = "System: 'screenshot captured successfully': "

            else:
                break

        if FORCE_STOP:
            FORCE_STOP = False  # Reset the flag
            core_utils.log("[chat_loop()] Stopped processing")
            yield ('response', {
                'success': True,
                'processing': False,
                'response': "\n*Stopped processing*",
                'chatId': current_chat_id,
                'status': "Stopped processing"
            })

    except Exception as e:
        core_utils.log(f"[chat_loop] Error: {str(e)}", 'error')
        yield ('response', {
            'success': False,
            'error': str(e),
            'processing': False,
            'chatId': current_chat_id
        })


# *--------------- API endpoint functions ---------------*
# UTILITY FUNCTIONS FOR CHAT HISTORY API ENDPOINTS
def reset_chat_session():
    """Reset Gemini chat session"""
    global chat_session, model
    chat_session = model.start_chat(history=[])
    return jsonify({"success": True})


def get_chats():
    return jsonify(chat_histories)


def get_chat(chat_id):
    if chat_id in chat_histories:
        return jsonify(chat_histories[chat_id])
    return jsonify({'error': 'Chat not found'}), 404


def delete_chat(chat_id):
    """Permanently delete chat history file"""
    if chat_id in chat_histories:
        folderpath = os.path.join(CHAT_STORAGE_PATH, chat_id)
        shutil.rmtree(folderpath)
        del chat_histories[chat_id]    # Remove from memory
        return jsonify({'success': True})
    return jsonify({'error': 'Chat not found'}), 404


def load_chat(chat_id):
    """Load the complete chat history with proper message reconstruction"""
    try:
        global chat_session, model
        if chat_id not in chat_histories:
            return jsonify({'error': 'Chat not found'}), 404

        history = chat_histories[chat_id]['contents']
        chat_session = model.start_chat(history=history)
        return jsonify(chat_histories[chat_id])

    except Exception as e:
        core_utils.log(f"Error loading chat: {str(e)}", 'error')
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Successfuly loaded utility functions.")
