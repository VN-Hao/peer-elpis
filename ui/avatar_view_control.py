"""
Avatar View Control UI for adjusting avatar display settings.
Allows users to drag, zoom, and control how they view the avatar.
"""
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, 
    QGroupBox, QFrame, QSpinBox, QCheckBox, QComboBox, QGridLayout, QSplitter,
    QLineEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QUrl
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView
from config.avatar_config import AvatarConfig


class AvatarViewControl(QWidget):
    """
    Avatar view control interface for drag, zoom, and display se                     // Apply zoom to Live2D model scale
                const newScale = window.originalModelScale.x * {zoom};
                model.scale.set(newScale, newScale);
                
                console.log('Applied zoom to Live2D model:', newScale);
                return true;     # Apply zoom to Live2D model scale
                const newScale = window.originalModelScale.x * {zoom};
                model.scale.set(newScale, newScale);
                
                console.log('Applied zoom to Live2D model:', newScale, '({zoom * 100}%)');
                return true;.
    """
    
    # Signal emitted when avatar view setup is complete
    view_setup_complete = pyqtSignal()
    
    def __init__(self, avatar_name="ANIYA", parent=None):
        super().__init__(parent)
        
        # Avatar configuration
        self.avatar_name = avatar_name
        self.chatbot_name = "AI Assistant"  # Default chatbot name
        self.avatar_config = AvatarConfig()  # Load available avatars
        
        # Default view settings for interactive dragging
        self.zoom_level = 100  # percentage
        self.drag_offset_x = 0  # X offset from dragging (will be updated by JS)
        self.drag_offset_y = 0  # Y offset from dragging (will be updated by JS)
        self.view_mode = "full"  # Always use full body for draggable mode
        
        # Reference to avatar widget for live preview (will be set externally)
        self.avatar_widget = None
        
        self.setWindowTitle('Avatar View Settings - Customize Your View')
        self.setMinimumSize(1100, 700)  # Larger window for better preview
        self.resize(1400, 850)  # Increased size to better show all options
        self.setup_ui()
    
    def setup_ui(self):
        """Build the avatar view control UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title_label = QLabel("🎭 Avatar View Settings")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Subtitle
        subtitle = QLabel("Customize how you want to view your AI assistant")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 20px;")
        main_layout.addWidget(subtitle)
        
        # Main content area with splitter for preview
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Controls
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
                padding: 20px;
            }
        """)
        controls_layout = QVBoxLayout(controls_frame)
        
        # Right side - Preview
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
                padding: 20px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        
        # Preview title
        preview_title = QLabel("🔍 Live Preview")
        preview_title_font = QFont()
        preview_title_font.setPointSize(14)
        preview_title_font.setBold(True)
        preview_title.setFont(preview_title_font)
        preview_title.setAlignment(Qt.AlignCenter)
        preview_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        preview_layout.addWidget(preview_title)
        
        # Create preview avatar - much larger and centered
        self.preview_webview = QWebEngineView()
        self.preview_webview.setMinimumSize(400, 500)  # Larger minimum size
        self.preview_webview.setStyleSheet("""
            border: 2px solid #bdc3c7; 
            border-radius: 15px;
            background-color: white;
        """)
        
        # Note: Avatar will be loaded after dropdown is populated
        
        # Add some spacing and center the preview better
        preview_layout.addStretch(1)  # Add flexible space above
        preview_layout.addWidget(self.preview_webview, alignment=Qt.AlignCenter)
        preview_layout.addStretch(1)  # Add flexible space below
        
        # Add frames to splitter with better proportions
        content_splitter.addWidget(controls_frame)
        content_splitter.addWidget(preview_frame)
        content_splitter.setSizes([500, 600])  # Give preview more space
        
        main_layout.addWidget(content_splitter)
        
        # Define common group box stylesheet
        group_box_style = """
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #2c3e50;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                margin: 10px 0;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """
        
        # Chatbot Customization
        customization_group = QGroupBox("🤖 Chatbot Customization")
        customization_group.setStyleSheet(group_box_style)
        customization_layout = QGridLayout(customization_group)
        
        # Chatbot Name
        customization_layout.addWidget(QLabel("Chatbot Name:"), 0, 0)
        self.chatbot_name_input = QLineEdit(self.chatbot_name)
        self.chatbot_name_input.setPlaceholderText("Enter your AI assistant's name...")
        self.chatbot_name_input.textChanged.connect(self._on_chatbot_name_changed)
        self.chatbot_name_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3498db;
            }
        """)
        customization_layout.addWidget(self.chatbot_name_input, 0, 1)
        
        controls_layout.addWidget(customization_group)
        
        # Avatar Model Selection
        avatar_group = QGroupBox("🎭 Avatar Model")
        avatar_group.setStyleSheet(group_box_style)
        avatar_layout = QGridLayout(avatar_group)
        
        # Model dropdown
        avatar_layout.addWidget(QLabel("Select Avatar:"), 0, 0)
        self.avatar_dropdown = QComboBox()
        self.avatar_dropdown.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                font-size: 12px;
                background-color: white;
            }
            QComboBox:focus {
                border-color: #3498db;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)
        
        # Populate avatar dropdown
        self._populate_avatar_dropdown()
        self.avatar_dropdown.currentTextChanged.connect(self._on_avatar_changed)
        avatar_layout.addWidget(self.avatar_dropdown, 0, 1)
        
        # Avatar info
        self.avatar_info_label = QLabel()
        self.avatar_info_label.setWordWrap(True)
        self.avatar_info_label.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        self._update_avatar_info()
        avatar_layout.addWidget(self.avatar_info_label, 1, 0, 1, 2)
        
        # Add Avatar button
        add_avatar_btn = QPushButton("📁 Upload Avatar Model")
        add_avatar_btn.clicked.connect(self._upload_avatar_model)
        add_avatar_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        avatar_layout.addWidget(add_avatar_btn, 2, 0, 1, 1)
        
        # Refresh avatars button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_avatars)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        avatar_layout.addWidget(refresh_btn, 2, 1, 1, 1)
        
        # Help button (smaller, for instructions)
        help_btn = QPushButton("❓ Help")
        help_btn.clicked.connect(self._show_add_avatar_help)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        avatar_layout.addWidget(help_btn, 3, 0, 1, 2)
        
        controls_layout.addWidget(avatar_group)
        
        # Load initial avatar AFTER dropdown is populated
        self._load_initial_avatar()
        
        controls_layout.addWidget(avatar_group)
        
        # Instructions for drag and zoom
        instructions_group = QGroupBox("How to Use")
        instructions_group.setStyleSheet(group_box_style)
        instructions_layout = QVBoxLayout(instructions_group)
        
        instruction_text = QLabel("🖱️ <b>Drag:</b> Click and drag the avatar in the preview to position it exactly how you want<br>"
                                "🔍 <b>Zoom:</b> Use the zoom slider below to scale the avatar size<br>"
                                "🎯 This gives you complete control over what part of the avatar you see")
        instruction_text.setWordWrap(True)
        instruction_text.setStyleSheet("color: #34495e; font-size: 12px; padding: 10px;")
        instructions_layout.addWidget(instruction_text)
        
        controls_layout.addWidget(instructions_group)
        
        # Zoom Controls
        zoom_group = QGroupBox("Zoom & Scale")
        zoom_group.setStyleSheet(group_box_style)
        zoom_layout = QGridLayout(zoom_group)
        
        # Zoom slider
        zoom_layout.addWidget(QLabel("Zoom Level:"), 0, 0)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(50, 500)  # 50% to 500% for much more zoom
        self.zoom_slider.setValue(100)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(25)
        self.zoom_slider.valueChanged.connect(self._on_zoom_changed)
        zoom_layout.addWidget(self.zoom_slider, 0, 1)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self.zoom_label, 0, 2)
        
        # Reset zoom button
        reset_zoom_btn = QPushButton("Reset Zoom")
        reset_zoom_btn.clicked.connect(self._reset_zoom)
        zoom_layout.addWidget(reset_zoom_btn, 1, 0, 1, 3)
        
        controls_layout.addWidget(zoom_group)
        
        controls_layout.addWidget(zoom_group)
        
        # Advanced Settings
        advanced_group = QGroupBox("Settings")
        advanced_group.setStyleSheet(zoom_group.styleSheet())
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Current position display (read-only)
        position_info = QLabel("Position will be set by dragging the avatar in the preview")
        position_info.setWordWrap(True)
        position_info.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        advanced_layout.addWidget(position_info)
        
        # Reset position button
        reset_position_btn = QPushButton("🔄 Reset Position & Zoom")
        reset_position_btn.clicked.connect(self._reset_all_interactive)
        reset_position_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        advanced_layout.addWidget(reset_position_btn)
        
        controls_layout.addWidget(advanced_group)
        
        # Add content splitter to main layout instead of content_frame
        main_layout.addWidget(content_splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        # Continue button
        continue_btn = QPushButton("✓ Continue to Chat")
        continue_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        continue_btn.clicked.connect(self._continue_to_chat)
        
        button_layout.addStretch()
        button_layout.addWidget(continue_btn)
        
        main_layout.addLayout(button_layout)
    
    def _on_zoom_changed(self, value):
        """Handle zoom level change."""
        self.zoom_level = value
        self.zoom_label.setText(f"{value}%")
        self._update_preview()
        self._apply_changes()
    
    def _reset_zoom(self):
        """Reset zoom to 100%."""
        self.zoom_slider.setValue(100)
    
    def _on_chatbot_name_changed(self, name):
        """Handle chatbot name change."""
        self.chatbot_name = name.strip() if name.strip() else "AI Assistant"
        print(f"🤖 Chatbot name changed to: {self.chatbot_name}")
    
    def _on_avatar_changed(self, avatar_display_name):
        """Handle avatar model change."""
        # Find the avatar ID from display name
        avatars = self.avatar_config.get_available_avatars()
        for avatar in avatars:
            if avatar['name'] == avatar_display_name:
                old_avatar = self.avatar_name
                self.avatar_name = avatar['id']
                print(f"🎭 Avatar changed from {old_avatar} to {self.avatar_name}")
                
                # Update avatar info
                self._update_avatar_info()
                
                # Reload preview with new avatar
                self._load_preview_avatar()
                break
    
    def _populate_avatar_dropdown(self):
        """Populate the avatar dropdown with available avatars."""
        avatars = self.avatar_config.get_available_avatars()
        
        print(f"🔍 DEBUG: Found {len(avatars)} avatars for dropdown")
        for avatar in avatars:
            print(f"   - {avatar}")
        
        # Clear existing items
        self.avatar_dropdown.clear()
        
        if not avatars:
            # Show message when no avatars available
            self.avatar_dropdown.addItem("❌ No avatar models found")
            self.avatar_dropdown.setEnabled(False)
            print("❌ No avatars found to populate dropdown")
            return
        
        # Enable dropdown if it was disabled
        self.avatar_dropdown.setEnabled(True)
        
        # Add each avatar
        current_index = 0
        for i, avatar in enumerate(avatars):
            display_name = avatar['name']
            print(f"📋 Adding avatar to dropdown: {display_name}")
            self.avatar_dropdown.addItem(display_name)
            
            # Select current avatar
            if avatar['id'] == self.avatar_name:
                current_index = i
                print(f"🎯 Setting current index to {i} for avatar {self.avatar_name}")
        
        # Set current selection
        self.avatar_dropdown.setCurrentIndex(current_index)
        print(f"✅ Dropdown populated with {len(avatars)} items, current index: {current_index}")
    
    def _update_avatar_info(self):
        """Update the avatar information label."""
        avatar_info = self.avatar_config.get_avatar_info(self.avatar_name)
        if avatar_info:
            info_text = f"📁 Model: {avatar_info['model_file']}\n📂 Path: {avatar_info['path']}"
        else:
            info_text = "❌ Avatar information not available"
        
        if hasattr(self, 'avatar_info_label'):
            self.avatar_info_label.setText(info_text)
    
    def _load_initial_avatar(self):
        """Load the initial avatar after ensuring dropdown is properly populated."""
        # Ensure we have valid avatars
        avatars = self.avatar_config.get_available_avatars()
        if not avatars:
            print("❌ No avatars available, cannot load preview")
            self._show_no_avatars_message()
            return
        
        # Validate current avatar name
        current_avatar_valid = any(avatar['id'] == self.avatar_name for avatar in avatars)
        if not current_avatar_valid:
            # Use first available avatar as fallback
            self.avatar_name = avatars[0]['id']
            print(f"🔄 Avatar '{self.avatar_name}' not valid, using fallback: {avatars[0]['id']}")
            
            # Update dropdown selection
            self.avatar_dropdown.setCurrentText(avatars[0]['name'])
        
        # Now load the preview
        self._load_preview_avatar()
    
    def _show_no_avatars_message(self):
        """Show a message when no avatars are available."""
        # Load a simple HTML page showing no avatars message
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 20px; 
                    background-color: #f8f9fa;
                }
                .message { 
                    color: #6c757d; 
                    font-size: 14px; 
                    margin-top: 30px;
                }
                .icon { font-size: 24px; margin-bottom: 10px; }
            </style>
        </head>
        <body>
            <div class="icon">🎭</div>
            <div class="message">
                No avatar models found<br>
                Add Live2D models to<br>
                <code>assets/avatar/</code>
            </div>
        </body>
        </html>
        """
        self.preview_webview.setHtml(html_content)
    
    def _upload_avatar_model(self):
        """Open file dialog to select and import a Live2D avatar model folder."""
        # Directly open folder selection dialog
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Live2D Avatar Model Folder",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        
        if folder_path:
            self._import_avatar_from_folder(folder_path)
    
    def _import_avatar_from_folder(self, source_folder):
        """Import avatar model from a selected folder."""
        import shutil
        import os
        
        try:
            # Get folder name for avatar ID
            folder_name = os.path.basename(source_folder.rstrip('/\\'))
            if not folder_name:
                QMessageBox.warning(self, "Error", "Invalid folder selected.")
                return
            
            # Check if folder contains a .model3.json file
            model_files = [f for f in os.listdir(source_folder) if f.endswith('.model3.json')]
            if not model_files:
                QMessageBox.warning(
                    self, 
                    "Invalid Avatar Model", 
                    f"No .model3.json file found in the selected folder.\n\n"
                    f"Please select a folder containing Live2D model files."
                )
                return
            
            # Destination folder
            assets_avatar_dir = os.path.join(os.getcwd(), 'assets', 'avatar')
            dest_folder = os.path.join(assets_avatar_dir, folder_name)
            
            # Check if avatar already exists
            if os.path.exists(dest_folder):
                reply = QMessageBox.question(
                    self,
                    "Avatar Exists",
                    f"An avatar named '{folder_name}' already exists.\n\n"
                    f"Do you want to replace it?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
                    
                # Remove existing folder
                shutil.rmtree(dest_folder)
            
            # Copy the entire folder
            shutil.copytree(source_folder, dest_folder)
            
            QMessageBox.information(
                self,
                "Avatar Added Successfully",
                f"Avatar '{folder_name}' has been added successfully!\n\n"
                f"Location: assets/avatar/{folder_name}/\n"
                f"Model files: {len(model_files)} found"
            )
            
            # Refresh the avatar list
            self._refresh_avatars()
            
            # Select the newly added avatar
            self.avatar_dropdown.setCurrentText(folder_name)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Import Error",
                f"Failed to import avatar model:\n\n{str(e)}"
            )
    
    def _show_add_avatar_help(self):
        """Show instructions for adding new avatar models."""
        help_text = """<h3>🎭 How to Add Live2D Avatar Models</h3>
        
<p><b>Method 1: Use the Upload Button (Recommended)</b></p>
<ul>
<li>Click "📁 Upload Avatar Model" above</li>
<li>Browse and select a folder containing your Live2D model files</li>
<li>The system will automatically copy all files to the correct location</li>
</ul>

<p><b>Method 2: Manual Installation</b></p>
<p>Create a folder: <code>assets/avatar/YourAvatarName/</code></p>
<p>Add your Live2D model files:</p>
<ul>
<li>📄 <code>YourAvatarName.model3.json</code> (Required)</li>
<li>📦 <code>YourAvatarName.moc3</code></li>
<li>🖼️ Texture files (PNG)</li>
<li>⚡ Physics and other files</li>
</ul>

<p><b>After Adding:</b> Click "🔄 Refresh" to reload the avatar list</p>

<hr>
<p><b>💡 Tip:</b> Look at the <code>assets/avatar/ANIYA/</code> folder structure for reference.</p>

<p><b>📁 What to Upload:</b> Select the entire folder containing your Live2D Cubism model files. The system will automatically detect and copy all necessary components.</p>
        """
        
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Avatar Import Help")
        msg_box.setTextFormat(1)  # Rich text
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()
    
    def _refresh_avatars(self):
        """Refresh the avatar list and dropdown."""
        print("🔄 Refreshing avatar list...")
        
        # Reload avatar configuration
        self.avatar_config = AvatarConfig()
        
        # Remember current selection if possible
        current_selection = None
        if self.avatar_dropdown.isEnabled() and self.avatar_dropdown.currentText():
            current_selection = self.avatar_dropdown.currentText()
        
        # Repopulate dropdown
        self._populate_avatar_dropdown()
        
        # Update info
        self._update_avatar_info()
        
        # Reload preview if we have a valid avatar
        self._load_initial_avatar()
        
        print("✅ Avatar list refreshed")
    
    def _reset_all_interactive(self):
        """Reset zoom and position for interactive mode."""
        self.zoom_slider.setValue(100)
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        # Reset the avatar position in preview
        self._reset_preview_position()
    
    def _reset_preview_position(self):
        """Reset the Live2D model position and scale in the preview."""
        try:
            if hasattr(self, 'preview_webview'):
                js_reset = """
                (function() {
                    if (!window.avatarModel || !window.originalModelPosition || !window.originalModelScale) {
                        console.log('Cannot reset - model or original values not available');
                        return false;
                    }
                    
                    const model = window.avatarModel;
                    
                    // Reset position to original
                    model.position.set(
                        window.originalModelPosition.x,
                        window.originalModelPosition.y
                    );
                    
                    // Reset scale to original
                    model.scale.set(
                        window.originalModelScale.x,
                        window.originalModelScale.y
                    );
                    
                    console.log('Reset Live2D model to original position and scale');
                    return true;
                })()
                """
                self.preview_webview.page().runJavaScript(js_reset)
                
                # Also update the zoom display
                self.zoom_slider.setValue(100)
        except Exception as e:
            print(f"Error resetting preview position: {e}")
    
    def _apply_changes(self):
        """Apply current settings to avatar (to be connected to avatar widget)."""
        settings = {
            'view_mode': self.view_mode,
            'zoom': self.zoom_level / 100.0,  # Convert percentage to decimal
            'drag_offset_x': self.drag_offset_x,
            'drag_offset_y': self.drag_offset_y,
            'enable_interactive_drag': True
        }
        
        # Apply to avatar widget if available for live preview
        if self.avatar_widget:
            self.avatar_widget.update_view_settings(settings)
        
        print(f"Avatar settings updated: {settings}")  # Debug output
    
    def _continue_to_chat(self):
        """Continue to the main chat interface."""
        # Capture current model position before transitioning
        self._capture_current_position()
        # Don't emit signal immediately - wait for position capture callback
        
    def _capture_current_position(self):
        """Capture the current Live2D model position before transitioning to chat."""
        try:
            # Wait for the page's avatarModel to initialize and return a full layout debug object
            js_code = """
            (async function(){
                try{
                    const wait = (ms)=>new Promise(r=>setTimeout(r,ms));
                    let tries = 0;
                    while((!window.avatarModel || !window.avatarModel.position || !window.avatarModel.scale) && tries < 30){
                        if(typeof window._layoutModel === 'function') try{ window._layoutModel(); }catch(e){}
                        await wait(100);
                        tries++;
                    }
                    const model = window.avatarModel || null;
                    const original = window.originalModelPosition || null;
                    const root = document.getElementById('avatar-root');
                    let rootW = null, rootH = null;
                    try{ if(root){ const b = root.getBoundingClientRect(); rootW = Math.round(b.width); rootH = Math.round(b.height);} }catch(e){}

                    // Try to compute preview center similar to layoutModel
                    let previewCenterX = null, previewCenterY = null;
                    try{
                        if(model && model.parent){
                            const app = model.parent;
                            const isSmallCanvas = Math.min(app.renderer.width, app.renderer.height) < 420;
                            const viewMode = (new URLSearchParams(window.location.search).get('view')) || '';
                            const yNudgeFactor = (viewMode === 'upper') ? (isSmallCanvas ? 0.56 : 0.60) : 0.48;
                            const basePosX = app.renderer.width / 2;
                            const basePosY = app.renderer.height * yNudgeFactor;
                            if(original){
                                previewCenterX = Math.round(basePosX + (model.position.x - original.x));
                                previewCenterY = Math.round(basePosY + (model.position.y - original.y));
                            }
                        }
                    }catch(e){}

                    const dbg = (function(){
                        try{
                            const d = window.__lastLayoutDebug || null;
                            return {
                                x: (model && original)? (model.position.x - original.x) : 0,
                                y: (model && original)? (model.position.y - original.y) : 0,
                                previewCenterX: previewCenterX,
                                previewCenterY: previewCenterY,
                                previewScaleX: model? (model.scale? model.scale.x : null) : null,
                                previewScaleY: model? (model.scale? model.scale.y : null) : null,
                                previewRootWidth: rootW,
                                previewRootHeight: rootH,
                                layoutDebug: d
                            };
                        }catch(e){ return { x:0,y:0, previewCenterX:null, previewCenterY:null, previewScaleX:null, previewScaleY:null, previewRootWidth:rootW, previewRootHeight:rootH, layoutDebug:null }; }
                    })();

                    return dbg;
                }catch(e){ return { x:0,y:0, previewCenterX:null, previewCenterY:null, previewScaleX:null, previewScaleY:null, previewRootWidth:null, previewRootHeight:null, layoutDebug:null }; }
            })()
            """
            self.preview_webview.page().runJavaScript(js_code, self._on_position_captured)
            
        except Exception as e:
            print(f"Error capturing position: {e}")
            # If capture fails, proceed anyway
            self.view_setup_complete.emit()
    
    def _on_position_captured(self, result):
        """Handle the captured position result and proceed to chat."""
        try:
            if result and isinstance(result, dict):
                self.drag_offset_x = result.get('x', 0)
                self.drag_offset_y = result.get('y', 0)
                # Also capture the preview's effective model scale and root size so we can
                # transform pan offsets into the chat model's coordinate system
                self.preview_original_scale_x = result.get('previewScaleX', result.get('originalScaleX', None))
                self.preview_original_scale_y = result.get('previewScaleY', result.get('originalScaleY', None))
                self.preview_root_width = result.get('previewRootWidth', None)
                self.preview_root_height = result.get('previewRootHeight', None)
                # Store preview center in pixel coords if provided
                self.preview_center_x = result.get('previewCenterX', None)
                self.preview_center_y = result.get('previewCenterY', None)
                print(f"🎯 Captured model position offset: x={self.drag_offset_x:.1f}, y={self.drag_offset_y:.1f} | preview root: {self.preview_root_width}x{self.preview_root_height}")
                # If the page returned a layoutDebug object, persist it so the preview log exists
                try:
                    layout_debug = result.get('layoutDebug')
                    if layout_debug:
                        import os, time, json
                        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                        logs_dir = os.path.abspath(os.path.join(project_root, 'logs'))
                        os.makedirs(logs_dir, exist_ok=True)
                        ts = int(time.time())
                        fname = os.path.join(logs_dir, f'avatar_layout_{ts}.json')
                        record = {
                            'timestamp': ts,
                            'view_settings': {
                                'view_mode': self.view_mode,
                                'zoom': self.zoom_level/100.0,
                                'drag_offset_x': self.drag_offset_x,
                                'drag_offset_y': self.drag_offset_y,
                                'preview_original_scale_x': self.preview_original_scale_x,
                                'preview_original_scale_y': self.preview_original_scale_y,
                                'preview_root_width': self.preview_root_width,
                                'preview_root_height': self.preview_root_height,
                                'enable_interactive_drag': True,
                                'avatar_name': self.avatar_name,
                                'chatbot_name': self.chatbot_name
                            },
                            'page_layout_debug': layout_debug
                        }
                        with open(fname, 'w', encoding='utf-8') as f:
                            json.dump(record, f, ensure_ascii=False, indent=2)
                        print(f'ℹ️ Saved preview layout debug to {fname}')
                except Exception as e:
                    print('Error saving preview layout debug:', e)
            else:
                print("⚠ Could not capture model position")
        except Exception as e:
            print(f"Error processing captured position: {e}")
        
        # Now emit the signal to proceed to chat
        self.view_setup_complete.emit()
    
    def get_view_settings(self):
        """Get current view settings as a dictionary for interactive mode."""
        # Always fetch the latest drag offsets and preview values before returning
        drag_x, drag_y = self.drag_offset_x, self.drag_offset_y
        scale_x = getattr(self, 'preview_original_scale_x', None)
        scale_y = getattr(self, 'preview_original_scale_y', None)
        root_w = getattr(self, 'preview_root_width', None)
        root_h = getattr(self, 'preview_root_height', None)
        center_x = getattr(self, 'preview_center_x', None)
        center_y = getattr(self, 'preview_center_y', None)
        return {
            'view_mode': self.view_mode,
            'zoom': self.zoom_level / 100.0,
            'drag_offset_x': drag_x,
            'drag_offset_y': drag_y,
            'enable_interactive_drag': True,
            'chatbot_name': self.chatbot_name,
            'avatar_name': self.avatar_name,
            'preview_original_scale_x': scale_x,
            'preview_original_scale_y': scale_y,
            'preview_root_width': root_w,
            'preview_root_height': root_h,
            'preview_center_x': center_x,
            'preview_center_y': center_y
        }
    
    def _get_current_drag_offsets(self):
        """Get current drag offsets from the preview webview."""
        try:
            # JavaScript to get current Live2D model position relative to original
            js_code = """
            (function() {
                if (!window.avatarModel || !window.originalModelPosition) {
                    return {x: 0, y: 0};
                }
                
                const model = window.avatarModel;
                const original = window.originalModelPosition;
                
                return {
                    x: model.position.x - original.x,
                    y: model.position.y - original.y
                };
            })()
            """
            
            # Use callback to get the result asynchronously
            def handle_offsets(result):
                if result and isinstance(result, dict):
                    self.drag_offset_x = result.get('x', 0)
                    self.drag_offset_y = result.get('y', 0)
            
            self.preview_webview.page().runJavaScript(js_code, handle_offsets)
        except Exception as e:
            print(f"Error getting current drag offsets: {e}")
        
        # Return current stored offsets (will be updated by callback)
        return self.drag_offset_x, self.drag_offset_y
    
    def apply_view_settings(self, settings):
        """Apply view settings to the controls (for loading saved settings)."""        
        if 'zoom' in settings:
            self.zoom_slider.setValue(int(settings['zoom'] * 100))
        
        if 'drag_offset_x' in settings:
            self.drag_offset_x = settings['drag_offset_x']
        
        if 'drag_offset_y' in settings:
            self.drag_offset_y = settings['drag_offset_y']
            
        # Update preview with loaded settings
        self._update_preview()
    
    def set_avatar_widget(self, avatar_widget):
        """Set the avatar widget for live preview."""
        self.avatar_widget = avatar_widget
    
    def _load_preview_avatar(self):
        """Load the preview avatar with full body view for dragging."""
        try:
            # Validate that we have a valid avatar
            if not self.avatar_name:
                print("❌ No avatar name specified, cannot load preview")
                return
                
            # Check if the avatar is valid
            avatar_info = self.avatar_config.get_avatar_info(self.avatar_name)
            if not avatar_info:
                print(f"❌ Avatar '{self.avatar_name}' not found, cannot load preview")
                return
            
            print(f"🎭 Loading preview for avatar: {self.avatar_name}")
            # Always load full body view for interactive dragging
            # Enable debug overlay in preview (temporary diagnostic) so we can compare layout values
            url = f"http://localhost:8080/index.html?avatar={self.avatar_name}&view=full&debug=1"
            self.preview_webview.load(QUrl(url))
            self.preview_webview.loadFinished.connect(self._on_preview_loaded)
        except Exception as e:
            print(f"Error loading preview avatar: {e}")
    
    def _on_preview_loaded(self, ok):
        """Called when preview avatar is loaded."""
        if ok:
            # Enable interactive dragging on the preview
            self._setup_interactive_preview()
            # Apply current zoom settings
            self._update_preview()
    
    def _setup_interactive_preview(self):
        """Setup interactive dragging for the preview avatar's Live2D model."""
        js_setup = """
        (function() {
            console.log('Setting up interactive preview for Live2D model...');
            
            // Wait for the Live2D model to be ready
            function waitForModel() {
                if (!window.avatarModel || !window.avatarModel.position) {
                    console.log('Live2D model not ready, retrying...');
                    setTimeout(waitForModel, 300);
                    return;
                }
                
                const model = window.avatarModel;
                console.log('Live2D model found:', model);
                console.log('Model parent:', model.parent);
                console.log('Model position:', model.position);
                console.log('Model scale:', model.scale);
                
                // Check if parent exists and has the expected properties
                if (!model.parent) {
                    console.error('Model parent is null or undefined');
                    return;
                }
                
                const app = model.parent;
                console.log('PIXI App:', app);
                console.log('App stage:', app.stage);
                
                // Try to enable interaction safely
                try {
                    if (app.stage && typeof app.stage === 'object') {
                        app.stage.interactive = true;
                        if (app.screen) {
                            app.stage.hitArea = app.screen;
                        }
                        console.log('Stage interaction enabled');
                    }
                } catch (e) {
                    console.warn('Could not enable stage interaction:', e);
                }
                
                try {
                    model.interactive = true;
                    model.buttonMode = true;
                    console.log('Model interaction enabled');
                } catch (e) {
                    console.error('Could not enable model interaction:', e);
                    return;
                }
                
                // Store original position and scale for reference
                if (!window.originalModelPosition) {
                    window.originalModelPosition = {
                        x: model.position.x,
                        y: model.position.y
                    };
                    console.log('Stored original position:', window.originalModelPosition);
                }
                if (!window.originalModelScale) {
                    window.originalModelScale = {
                        x: model.scale.x,
                        y: model.scale.y
                    };
                    console.log('Stored original model scale:', window.originalModelScale);
                }
                
                // Clear any existing event listeners
                try {
                    model.removeAllListeners();
                    console.log('Cleared existing listeners');
                } catch (e) {
                    console.warn('Could not clear listeners:', e);
                }
                
                let dragData = null;
                let isDragging = false;
                
                function onDragStart(event) {
                    console.log('Live2D model drag started', event);
                    isDragging = true;
                    dragData = event.data;
                    
                    try {
                        // Get starting position
                        dragData.startPoint = dragData.getLocalPosition(model.parent);
                        dragData.startModelPos = { x: model.position.x, y: model.position.y };
                        
                        console.log('Drag start point:', dragData.startPoint);
                        console.log('Model start position:', dragData.startModelPos);
                        
                        // Update cursor
                        if (app.view && app.view.style) {
                            app.view.style.cursor = 'grabbing';
                        }
                        
                        event.stopPropagation();
                    } catch (e) {
                        console.error('Error in drag start:', e);
                        isDragging = false;
                        dragData = null;
                    }
                }
                
                function onDragMove(event) {
                    if (!isDragging || !dragData) return;
                    
                    try {
                        // Get current position
                        const currentPoint = dragData.getLocalPosition(model.parent);
                        
                        // Calculate delta
                        const deltaX = currentPoint.x - dragData.startPoint.x;
                        const deltaY = currentPoint.y - dragData.startPoint.y;
                        
                        // Update model position
                        model.position.set(
                            dragData.startModelPos.x + deltaX,
                            dragData.startModelPos.y + deltaY
                        );
                        
                        // console.log('Model dragged to:', model.position.x, model.position.y);
                    } catch (e) {
                        console.error('Error in drag move:', e);
                    }
                }
                
                function onDragEnd(event) {
                    if (!isDragging) return;
                    
                    console.log('Live2D model drag ended');
                    isDragging = false;
                    
                    try {
                        if (app.view && app.view.style) {
                            app.view.style.cursor = 'grab';
                        }
                    } catch (e) {
                        console.warn('Could not reset cursor:', e);
                    }
                    
                    dragData = null;
                }
                
                // Bind interaction events with error handling
                try {
                    model.on('pointerdown', onDragStart);
                    model.on('mousedown', onDragStart);
                    console.log('Bound drag start events');
                    
                    model.on('pointermove', onDragMove);
                    model.on('mousemove', onDragMove);
                    console.log('Bound drag move events');
                    
                    model.on('pointerup', onDragEnd);
                    model.on('pointerupoutside', onDragEnd);
                    model.on('mouseup', onDragEnd);
                    model.on('mouseupoutside', onDragEnd);
                    console.log('Bound drag end events');
                    
                    // Set initial cursor
                    if (app.view && app.view.style) {
                        app.view.style.cursor = 'grab';
                    }
                    
                    console.log('✓ Live2D model dragging enabled successfully');
                } catch (e) {
                    console.error('Error binding events:', e);
                    return;
                }
            }
            
            // Start waiting for the model
            waitForModel();
            
            // Add preview indicator
            try {
                const indicator = document.createElement('div');
                indicator.style.position = 'absolute';
                indicator.style.top = '5px';
                indicator.style.right = '5px';
                indicator.style.background = '#27ae60';
                indicator.style.color = 'white';
                indicator.style.padding = '2px 6px';
                indicator.style.fontSize = '10px';
                indicator.style.borderRadius = '3px';
                indicator.style.zIndex = '1000';
                indicator.textContent = 'DRAG MODEL';
                document.body.appendChild(indicator);
            } catch (e) {
                console.warn('Could not add preview indicator:', e);
            }
            
            return true;
        })()
        """
        
        self.preview_webview.page().runJavaScript(js_setup, self._on_interactive_setup)
    
    def _on_interactive_setup(self, result):
        """Handle the result of setting up interactive preview."""
        if result:
            print("✓ Interactive Live2D model dragging enabled in preview")
        else:
            print("⚠ Failed to setup interactive dragging")
    
    def _update_preview(self):
        """Update the preview avatar Live2D model with current zoom level."""
        try:
            zoom = self.zoom_level / 100.0
            
            # JavaScript to apply zoom directly to the Live2D model
            js_code = f"""
            (function() {{
                // Wait for Live2D model to be available
                if (!window.avatarModel || !window.avatarModel.scale) {{
                    console.log('Live2D model not ready for zoom update');
                    return false;
                }}
                
                const model = window.avatarModel;
                
                // Store original scale if not already stored
                if (!window.originalModelScale) {{
                    window.originalModelScale = {{
                        x: model.scale.x,
                        y: model.scale.y
                    }};
                    console.log('Stored original model scale:', window.originalModelScale);
                }}
                
                // Apply zoom to Live2D model scale
                const newScale = window.originalModelScale.x * {zoom};
                model.scale.set(newScale, newScale);
                
                console.log('Applied zoom to Live2D model:', newScale);
                return true;
            }})()
            """
            
            self.preview_webview.page().runJavaScript(js_code, self._on_zoom_applied)
            
        except Exception as e:
            print(f"Error updating preview zoom: {e}")
    
    def _on_zoom_applied(self, result):
        """Handle zoom application result."""
        if not result:
            # If model isn't ready, retry after a short delay
            QTimer.singleShot(200, self._update_preview)
    
    def _reload_preview_with_view_mode(self):
        """Reload preview with new view mode."""
        try:
            url = f"http://localhost:8080/index.html?avatar={self.avatar_name}&view={self.view_mode}"
            self.preview_webview.load(QUrl(url))
        except Exception as e:
            print(f"Error reloading preview: {e}")
