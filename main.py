import sys
import threading
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PyQt5.QtWidgets import QApplication
from ui.chat_window import ChatApp

# -------------------------------
# Start local HTTP server in background
# -------------------------------
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
    app = QApplication(sys.argv)
    window = ChatApp()
    window.show()
    sys.exit(app.exec_())
