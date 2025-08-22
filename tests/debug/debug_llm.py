#!/usr/bin/env python3
"""
Test LLM service independently
"""
import sys
import os
# Add project root to path (go up two levels from tests/debug/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from bot.llm_bot import get_bot_response

def test_llm():
    """Test LLM functionality."""
    print("=== Testing LLM ===")
    
    test_messages = [
        "Hello!",
        "How are you?",
        "What's your name?"
    ]
    
    for msg in test_messages:
        print(f"\nUser: {msg}")
        try:
            response = get_bot_response(msg)
            print(f"Bot: {response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_llm()
