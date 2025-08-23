# Enhanced Avatar Customization Guide

## 🎉 New Features Overview

Your chatbot now includes enhanced customization options that allow you to personalize both the appearance and identity of your AI assistant!

## ✨ What's New

### 🤖 Chatbot Name Customization
- **Set a Custom Name**: Give your AI assistant a personal name like "Stella", "Nova", "Echo", or any name you prefer
- **Dynamic Window Title**: The application window title updates to show "Chat with [Your Chatbot Name]"
- **Personal Connection**: Makes your interaction feel more personal and engaging

### 🎭 Avatar Model Selection
- **Multiple Models Support**: Choose from any Live2D model in your `assets/avatar/` directory
- **Easy Selection**: Dropdown menu shows all available avatar models
- **File Upload**: Click "📁 Upload Avatar Model" to browse and select new models
- **Two Upload Methods**:
  - **Select Folder**: Browse and select an entire folder containing Live2D files
  - **Select File**: Choose a specific `.model3.json` file
- **Automatic Import**: Files are automatically copied to the correct location
- **Model Validation**: System validates that required files are present
- **Model Information**: See model file details and path information
- **Refresh Function**: "🔄 Refresh" button to reload avatar list
- **Help Guide**: "❓ Help" button with detailed instructions
- **Flexible System**: Add new models easily through the UI

### 🖱️ Enhanced View Controls (Improved)
- **Drag Positioning**: Click and drag the avatar preview to position it exactly where you want
- **Advanced Zoom**: Scale from 50% to 500% for precise size control
- **Live Preview**: See changes in real-time as you customize
- **Reset Options**: Easily reset position and zoom to defaults

## 🚀 How to Use

### Step 1: Launch the Application
```bash
cd "d:\project\peer-elpis"
env\Scripts\python.exe main.py
```
Or use the demo script:
```bash
env\Scripts\python.exe demo_avatar_customization.py
```

### Step 2: Customize Your Chatbot
1. **Set Chatbot Name**:
   - Enter your preferred name in the "Chatbot Name" field
   - Examples: "Stella", "Nova", "Echo", "Assistant", "Helper"
   - Leave blank to use default "AI Assistant"

2. **Choose Avatar Model**:
   - Select from the dropdown menu of available models
   - Click "📁 Upload Avatar Model" to add new Live2D models:
     - Choose "Select Folder" to browse for a folder containing Live2D files
     - Choose "Select File" to pick a specific .model3.json file
     - Files will be automatically copied to the correct location
   - Currently shows: ANIYA (with path and model info)
   - Use "🔄 Refresh" to reload the avatar list after manual changes
   - Click "❓ Help" for detailed upload instructions

3. **Position and Scale**:
   - Drag the avatar in the preview window
   - Use zoom slider (50% - 500%)
   - Click "Reset Position & Zoom" to return to defaults

### Step 3: Apply Settings
- Click "✓ Continue to Chat" to apply your customizations
- Your settings will be used in the main chat interface
- Window title updates to show your chatbot's name

## 🏗️ Adding New Avatar Models

### Method 1: Upload via UI (Recommended)

1. **Click Upload Button**: In the Avatar Settings panel, click "📁 Upload Avatar Model"
2. **Choose Upload Method**:
   - **Select Folder**: Browse to a folder containing your Live2D model files
   - **Select File**: Choose the main `.model3.json` file
3. **Automatic Import**: The system will:
   - Validate the model files
   - Copy all necessary files to `assets/avatar/`
   - Add the new model to the dropdown
   - Show success confirmation
4. **Select New Model**: Your new avatar will be immediately available in the dropdown

### Method 2: Manual Installation

To add new Live2D models manually:

1. **Create Model Folder**:
   ```
   assets/avatar/YourModelName/
   ```

2. **Add Required Files**:
   ```
   assets/avatar/YourModelName/
   ├── YourModelName.model3.json  (Required)
   ├── YourModelName.moc3
   ├── textures/
   └── other Live2D files...
   ```

3. **Restart Application**: The new model will appear in the dropdown automatically

## 🔧 Technical Details

### Settings Storage
Your customizations are stored in the view settings and include:
- `chatbot_name`: Your chosen chatbot name
- `avatar_name`: Selected avatar model ID
- `zoom`: Scale factor (0.5 to 5.0)
- `drag_offset_x`: X position offset
- `drag_offset_y`: Y position offset

### File Structure
The system uses:
- `config/avatar_config.py`: Avatar scanning and management
- `ui/avatar_view_control.py`: Customization interface
- `ui/chat_window.py`: Main application with settings integration
- `assets/avatar/`: Live2D model storage

## 🎊 Enjoy Your Customized Experience!

Your chatbot is now more personal and flexible than ever. Experiment with different names and models to create the perfect AI assistant for your needs!

## 🔄 Future Enhancements

Possible future additions:
- Voice personality selection
- Theme customization
- More avatar animation controls
- Import/export of custom settings
- Multiple chatbot profiles
