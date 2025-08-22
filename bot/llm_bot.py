from dotenv import load_dotenv
import os
import google.generativeai as genai

load_dotenv()
GEN_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GENAI_API_KEY")

if GEN_API_KEY:
    try:
        genai.configure(api_key=GEN_API_KEY)
    except Exception:
        pass

conversation_history = []
_warned_api = False

def _fallback_response(user_text: str) -> str:
    # Very lightweight local echo-style fallback
    if user_text.lower() in {"hi", "hello"}:
        return "Hello! (offline mode)"
    return f"(offline) You said: {user_text[:200]}"

def get_bot_response(user_text: str) -> str:
    global conversation_history, _warned_api
    conversation_history.append(f"User: {user_text}")
    prompt = "\n".join(conversation_history) + "\nAssistant:"

    # Abort early if no key
    if not GEN_API_KEY:
        reply = _fallback_response(user_text)
        conversation_history.append(f"Assistant: {reply}")
        return reply

    try:
        # Use the modern GenerativeModel API (v0.3.0+)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        bot_reply = response.text.strip() if response.text else ""

        if not bot_reply:
            bot_reply = _fallback_response(user_text)
    except Exception as e:
        if not _warned_api:
            print(f"[LLM] Falling back due to error: {e}")
            _warned_api = True
        bot_reply = _fallback_response(user_text)

    conversation_history.append(f"Assistant: {bot_reply}")
    return bot_reply
