#!/usr/bin/env python3
"""
Peer Elpis - Chat Application Launcher

Launches the enhanced chat application with voice integration.
This is the lightweight version without the Live2D avatar.

Features:
- AI-powered chat with Google Generative AI
- Advanced voice synthesis using OpenVoice
- Voice engine management (save/load)
- Sample voice selection and processing
- Clean, responsive PyQt5 interface

For the full experience with avatar, use main.py instead.
"""
import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from ui.chat_window import ChatApp
from services.voice_engine_service import VoiceEngineService

def main():
    """Launch the chat app with voice integration."""
    app = QApplication(sys.argv)
    app.setApplicationName("Peer Elpis - AI Chat")
    
    # Create enhanced voice service
    voice_service = VoiceEngineService()
    
    # Create and show chat app
    chat_app = ChatApp(voice_service=voice_service)
    chat_app.show()
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
