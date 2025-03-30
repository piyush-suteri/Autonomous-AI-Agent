import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


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

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
    upload_to_gemini("raw/eg.png", mime_type="image/png"),
]

chat_session = model.start_chat(
    history=[],
)
chat_session.history.append({
    "role": "user",
    "parts": [
        files[0],
    ],
},)

response = chat_session.send_message("What do you see")

print(response.text)
print(chat_session.history)