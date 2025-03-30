import os
import google.generativeai as genai

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
  history=[
    {
      "role": "user",
      "parts": [
        "hi",
      ],
    },
    {
      "role": "model",
      "parts": [
        "Hi there! How can I help you today? Are you looking for information, want to chat, or something else? Let me know! 😊\n",
      ],
    },
  ]
)


while True:
  user_input = input("You: ")
  if user_input.lower() == "exit":
      break

  response = chat_session.send_message(user_input, stream=True)

  print("Model: ", end="", flush=True) # Use flush=True for immediate output
  for chunk in response:
    print(chunk.text, end="", flush=True) # Use flush=True for immediate output
  print() # Print a newline after the response


print("Chat session ended.")