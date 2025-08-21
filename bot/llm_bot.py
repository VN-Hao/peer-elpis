from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()
GEN_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEN_API_KEY)

conversation_history = []

def get_bot_response(user_text: str) -> str:
    global conversation_history

    # Append user message to history
    conversation_history.append(f"User: {user_text}")

    # Combine history into a single prompt
    prompt = "\n".join(conversation_history) + "\nAssistant:"

    # Generate response
    model = genai.GenerativeModel(model_name='gemini-2.5-flash')
    response = model.generate_content(prompt)

    # Extract text
    bot_reply = response.text.strip()

    # Append assistant reply to history
    conversation_history.append(f"Assistant: {bot_reply}")

    return bot_reply
