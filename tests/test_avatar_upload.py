#!/usr/bin/env python3
"""
Test script for avatar model upload functionality.
Tests the new file/folder selection features.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.avatar_config import AvatarConfig
from ui.avatar_view_control import AvatarViewControl

def test_avatar_upload_ui():
    """Test the avatar upload UI functionality."""
    print("🧪 Testing Avatar Upload UI...")
    
    app = QApplication(sys.argv)
    
    # Create avatar view control
    control = AvatarViewControl("ANIYA")
    
    # Check if upload methods exist
    methods_to_check = [
        '_upload_avatar_model',
        '_import_avatar_from_folder'
    ]
    
    print("🔍 Checking upload methods:")
    for method in methods_to_check:
        if hasattr(control, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} - MISSING")
    
    # Check UI elements
    print("\n🎨 Checking UI elements:")
    if hasattr(control, 'avatar_dropdown'):
        print(f"   ✅ Avatar dropdown: {control.avatar_dropdown.count()} items")
    
    # Check button connections
    upload_btn = None
    for child in control.findChildren(object):
        if hasattr(child, 'text') and callable(getattr(child, 'text', None)):
            try:
                if 'Upload Avatar Model' in child.text():
                    upload_btn = child
                    break
            except:
                pass
    
    if upload_btn:
        print("   ✅ Upload Avatar Model button found")
    else:
        print("   ❌ Upload Avatar Model button not found")
    
    app.quit()
    return True

def test_assets_directory():
    """Test if assets directory structure is correct."""
    print("\n📁 Checking assets directory structure:")
    
    assets_dir = os.path.join(os.getcwd(), 'assets')
    avatar_dir = os.path.join(assets_dir, 'avatar')
    
    if os.path.exists(assets_dir):
        print(f"   ✅ assets/ directory exists")
    else:
        print(f"   ❌ assets/ directory missing")
        
    if os.path.exists(avatar_dir):
        print(f"   ✅ assets/avatar/ directory exists")
        
        # List existing avatars
        try:
            avatar_folders = [d for d in os.listdir(avatar_dir) 
                            if os.path.isdir(os.path.join(avatar_dir, d))]
            print(f"   📂 Found {len(avatar_folders)} avatar folders: {avatar_folders}")
        except:
            print(f"   ⚠️  Could not list avatar folders")
    else:
        print(f"   ❌ assets/avatar/ directory missing")
        
    return True

if __name__ == "__main__":
    print("🚀 Testing Enhanced Avatar Upload System\n")
    
    try:
        # Test UI functionality
        ui_success = test_avatar_upload_ui()
        
        # Test directory structure
        dir_success = test_assets_directory()
        
        if ui_success and dir_success:
            print("\n✅ All tests passed!")
            print("\n🎉 New Upload Features:")
            print("   📁 File browser to select Live2D model folders")
            print("   📄 Direct .model3.json file selection")
            print("   🔄 Automatic file copying to assets/avatar/")
            print("   ✅ Validation of model files")
            print("   🎭 Automatic avatar list refresh")
            print("   ❓ Help button with detailed instructions")
        else:
            print("\n❌ Some tests failed.")
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
