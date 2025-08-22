#!/usr/bin/env python3
"""
Peer Elpis - Main Application Entry Point

Launches the complete AI assistant application with:
- Live2D avatar animation
- Voice synthesis and cloning
- Interactive chat interface
- HTTP server for avatar assets

This is the full-featured version. For chat-only mode, use launch_chat.py instead.
"""

import sys
import threading
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PyQt5.QtCore import Qt, QCoreApplication
from PyQt5.QtWidgets import QApplication
def start_local_server():
    # Serve the 'assets/avatars' folder
    avatars_path = os.path.join(os.path.dirname(__file__), "assets", "avatar")
    os.chdir(avatars_path)
    server = HTTPServer(("localhost", 8080), SimpleHTTPRequestHandler)
    print("Starting local HTTP server at http://localhost:8080")
    server.serve_forever()

# Start server in a separate daemon thread
threading.Thread(target=start_local_server, daemon=True).start()

# -------------------------------
# Launch PyQt app
# -------------------------------
if __name__ == "__main__":
    # Set required attribute before any WebEngine initialization
    QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
    # Import WebEngine AFTER setting attribute but BEFORE creating QApplication
    from PyQt5 import QtWebEngineWidgets  # noqa: F401
    app = QApplication(sys.argv)
    from ui.chat_window import ChatApp
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
