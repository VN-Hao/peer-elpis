"""
Avatar Configuration Module
Manages available Live2D avatars and provides selection functionality.
"""
import os
import json
from typing import List, Dict, Optional

class AvatarConfig:
    """Manages avatar configuration and selection."""
    
    def __init__(self, avatar_dir: str = "assets/avatar"):
        self.avatar_dir = avatar_dir
        self.default_avatar = "ANIYA"
        self._available_avatars = None
        
    def get_available_avatars(self) -> List[Dict[str, str]]:
        """Get list of available avatars with their metadata."""
        if self._available_avatars is None:
            self._scan_avatars()
        return self._available_avatars
    
    def _scan_avatars(self):
        """Scan avatar directory for available Live2D models."""
        self._available_avatars = []
        
        if not os.path.exists(self.avatar_dir):
            print(f"Warning: Avatar directory {self.avatar_dir} not found")
            return
            
        for item in os.listdir(self.avatar_dir):
            avatar_path = os.path.join(self.avatar_dir, item)
            
            # Check if it's a directory
            if os.path.isdir(avatar_path):
                # Look for .model3.json file
                model_file = None
                for file in os.listdir(avatar_path):
                    if file.endswith('.model3.json'):
                        model_file = file
                        break
                
                if model_file:
                    avatar_info = {
                        'id': item,
                        'name': item,
                        'path': avatar_path,
                        'model_file': model_file
                    }
                    
                    # Try to get display name from vtube.json if available
                    vtube_file = os.path.join(avatar_path, f"{item}.vtube.json")
                    if os.path.exists(vtube_file):
                        try:
                            with open(vtube_file, 'r', encoding='utf-8') as f:
                                vtube_data = json.load(f)
                                if 'Name' in vtube_data:
                                    avatar_info['name'] = vtube_data['Name']
                        except:
                            pass  # Use folder name as fallback
                    
                    self._available_avatars.append(avatar_info)
                    print(f"✓ Found avatar: {avatar_info['name']} ({avatar_info['id']})")
    
    def get_avatar_info(self, avatar_id: str) -> Optional[Dict[str, str]]:
        """Get information about a specific avatar."""
        avatars = self.get_available_avatars()
        for avatar in avatars:
            if avatar['id'] == avatar_id:
                return avatar
        return None
    
    def is_avatar_valid(self, avatar_id: str) -> bool:
        """Check if an avatar ID is valid."""
        return self.get_avatar_info(avatar_id) is not None
    
    def get_default_avatar(self) -> str:
        """Get the default avatar ID."""
        avatars = self.get_available_avatars()
        
        # Try to use configured default
        if any(a['id'] == self.default_avatar for a in avatars):
            return self.default_avatar
            
        # Fallback to first available
        if avatars:
            return avatars[0]['id']
            
        print("Warning: No avatars found!")
        return self.default_avatar

# Global avatar config instance
avatar_config = AvatarConfig()
