#!/usr/bin/env python3
"""
Demo script for the Enhanced Avatar Customization System
Shows how to use the new chatbot name and avatar model selection features
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.chat_window import ChatApp

def main():
    """Launch the enhanced chat application with customization features."""
    print("🚀 Launching Enhanced Avatar Customization Demo")
    print("=" * 60)
    print()
    print("✨ NEW FEATURES ADDED:")
    print("   🤖 Chatbot Name Customization")
    print("      - Set your AI assistant's name in the avatar settings")
    print("      - The window title will update to reflect the name")
    print()
    print("   🎭 Avatar Model Selection")
    print("      - Choose from any available Live2D models")
    print("      - Dropdown shows all models in assets/avatar/ folder")
    print("      - Model information displayed below selection")
    print()
    print("   🖱️ Enhanced View Controls (existing)")
    print("      - Drag and position your avatar")
    print("      - Zoom from 50% to 500%")
    print("      - Real-time preview")
    print()
    print("📋 HOW TO USE:")
    print("1. Launch the app - you'll see the Avatar Settings panel")
    print("2. Enter your preferred chatbot name (e.g., 'Stella', 'Nova', 'Echo')")
    print("3. Select an avatar model from the dropdown")
    print("4. Drag the avatar preview to position it")
    print("5. Use the zoom slider to scale the avatar")
    print("6. Click 'Continue to Chat' to apply your settings")
    print("7. The main chat window will use your customizations!")
    print()
    print("=" * 60)
    
    # Create and run the application
    app = QApplication(sys.argv)
    
    # Create the main chat window
    window = ChatApp()
    
    # Show the window
    window.show()
    
    print("🎊 Application launched! Enjoy your customized chatbot experience!")
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
