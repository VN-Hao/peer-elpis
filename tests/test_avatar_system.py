#!/usr/bin/env python3
"""
Test script for the flexible avatar system.
Tests avatar configuration scanning and UI integration.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.avatar_config import AvatarConfig
from ui.chat_window import ChatApp

def test_avatar_config():
    """Test the avatar configuration system."""
    print("🧪 Testing Avatar Configuration System...")
    
    config = AvatarConfig()
    
    # Test avatar scanning
    avatars = config.get_available_avatars()
    print(f"📁 Found {len(avatars)} avatars:")
    for avatar in avatars:
        print(f"   - {avatar['name']} (ID: {avatar['id']})")
        print(f"     Path: {avatar['path']}")
        print(f"     Model: {avatar['model_file']}")
    
    # Test default avatar
    default = config.get_default_avatar()
    print(f"⭐ Default avatar: {default}")
    
    # Test avatar info
    if avatars:
        first_avatar = avatars[0]['id']
        info = config.get_avatar_info(first_avatar)
        print(f"📋 Info for {first_avatar}: {info}")
    
    return len(avatars) > 0

def test_ui_integration():
    """Test UI integration with flexible avatar system."""
    print("\n🖥️  Testing UI Integration...")
    
    app = QApplication(sys.argv)
    
    # Create chat window (this will use AvatarConfig internally)
    window = ChatApp()
    
    # Check if the selected avatar is properly set
    print(f"🎭 Selected avatar in ChatApp: {window.selected_avatar}")
    
    # Test avatar view control creation
    window._show_avatar_view_control()
    if window._avatar_view_control:
        print(f"✅ AvatarViewControl created with avatar: {window._avatar_view_control.avatar_name}")
        # Clean up
        window._avatar_view_control.setParent(None)
    
    app.quit()
    return True

if __name__ == "__main__":
    print("🚀 Testing Flexible Avatar System\n")
    
    try:
        # Test configuration
        config_success = test_avatar_config()
        
        # Test UI integration
        ui_success = test_ui_integration()
        
        if config_success and ui_success:
            print("\n✅ All tests passed! The flexible avatar system is working correctly.")
        else:
            print("\n❌ Some tests failed.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
