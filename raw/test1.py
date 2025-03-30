"""
Install an additional SDK for JSON schema support Google AI Python SDK

$ pip install google.ai.generativelanguage
"""

import os
import json
import tempfile
import subprocess
import threading
import sys
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
# from src.functions.agent_func import execute_python_code

result = None
name = "Piyush"

def execute_python_code(code: str, wait_time: int=30):
    """
    Executes Python code with a specified wait time, collects output/errors,
    and returns results even if the script is still running.

    Parameters:
        code (str): The Python code to execute.
        wait_time (int): Time in seconds to wait before returning the results.

    Returns:
        str: JSON-formatted string containing output, errors, and return code (if available).
    """
    if not isinstance(code, str) or not code.strip():
        return json.dumps({"error": "Invalid code provided. Must be a non-empty string."})

    process = None
    temp_file = None

    try:
        # Create a temporary file to store the code
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
            temp_file = temp.name
            temp.write(code.encode('utf-8'))  # Properly encode the string to bytes

        # Execute the script with subprocess
        process = subprocess.Popen(
            ['python', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
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
            result  = json.dumps({
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
                "return_code": None,
                "status": "Script is still running"
            })
            return result

        # If the thread is finished, return the full result
        result = json.dumps({
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "return_code": result["return_code"]
        })
        return result

    except Exception as e:
        if process:
            process.kill()
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})

    finally:
        # Clean up temporary file
        try:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}")


def greet(wish: str):
    global result
    result = wish
    return wish

def getName():
    return name

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
  tools = [execute_python_code],
  system_instruction="Use `execute_python_code` function to run python code on users request. Pass code as argument and timeout (optional). You can run any python code using this function. This function is specifically useful for interacting with computer in this environment. You can open applications using subprocess and later use pyautogui to interact with them. If you run into any error tell all errors exactly to user."
)

chat_session = model.start_chat(
  history=[], enable_automatic_function_calling=True
)

# print(execute_python_code("print('hello')"))
# result =""

response = chat_session.send_message("Run python code to print('hello') and tell me the output")

# Print out each of the function calls requested from this single call.
# Note that the function calls are not executed. You need to manually execute the function calls.
# For more see: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Function_calling.ipynb
print(response)
# for part in response.parts:
#   if fn := part.function_call:
#     args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
#     print(f"{fn.name}({args})")
#     if fn.name == "add":
#       print("Executing the function call")
#       result = greet(**fn.args)

print(result)
print(chat_session.history)



"""LOGS: 
PS E:\My space\Data\Projects\Code\Gemini_agent> & C:/Users/piyus/AppData/Local/Programs/Python/Python310/python.exe "e:/My space/Data/Projects/Code/Gemini_agent/raw/test1.py"
response:
GenerateContentResponse(
    done=True,
    iterator=None,
    result=protos.GenerateContentResponse({
      "candidates": [
        {
          "content": {
            "parts": [
              {
                "text": "The output of the code is:\nhello\n"
              }
            ],
            "role": "model"
          },
          "finish_reason": "STOP",
          "safety_ratings": [
            {
              "category": "HARM_CATEGORY_HATE_SPEECH",
              "probability": "NEGLIGIBLE"
            },
            {
              "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
              "probability": "NEGLIGIBLE"
            },
            {
              "category": "HARM_CATEGORY_HARASSMENT",
              "probability": "NEGLIGIBLE"
            },
            {
              "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
              "probability": "NEGLIGIBLE"
            }
          ],
          "avg_logprobs": -0.2543493270874023
        }
      ],
      "usage_metadata": {
        "prompt_token_count": 296,
        "candidates_token_count": 10,
        "total_token_count": 306
      }
    }),
)
None
[parts {
  text: "Run python code to print(\'hello\') and tell me the output"
}
role: "user"
, parts {
  function_call {
    name: "execute_python_code"
    args {
      fields {
        key: "code"
        value {
          string_value: "print(\'hello\')"
        }
      }
    }
  }
}
role: "model"
, 

parts {
  function_response {
    name: "execute_python_code"
    response {
      fields {
        key: "result"
        value {
          string_value: "{\"stdout\": \"hello\\n\", \"stderr\": \"\", \"return_code\": 0}"       
        }
      }
    }
  }
}
role: "user"

, parts {
  text: "The output of the code is:\nhello\n"
}
role: "model"
]
WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1737453856.838672   10752 init.cc:229] grpc_wait_for_shutdown_with_timeout() timed out.
PS E:\My space\Data\Projects\Code\Gemini_agent> 
"""