# Mute Streamer Overload

A tool for creating animated text overlays for streamers, with both a desktop overlay and web-based display option.

## Features

- Desktop overlay window with customizable size and position
- Web-based overlay accessible via local web server
- Animated text display with customizable speed and character limits
- F4 hotkey for quick message input
- Dark theme UI
- Draggable overlay window
- Synchronized animation between desktop and web displays

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mute-streamer-overload.git
cd mute-streamer-overload
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Unix/MacOS:
source .venv/bin/activate
```

3. Install the package:
```bash
pip install -e .
```

## Usage

### Running the Application

You can run the application in two ways:

1. Using the installed command:
```bash
mute-streamer-overload
```

2. Running the main script directly:
```bash
   python main.py
   ```

### Using the Desktop Overlay

1. Launch the application
2. Click "Show Overlay" to display the overlay window
3. Adjust the size using the width and height controls
4. Drag the overlay window to position it where you want
5. Use F4 to start typing your message
6. Press F4 again to submit and display the message

### Adding the Web Overlay to OBS

The application includes a local web server that provides a web-based overlay. Here's how to add it to OBS:

1. Start the application (the web server starts automatically)
2. In OBS, add a new Browser Source:
   - Click the + button in the Sources panel
   - Select "Browser Source"
   - Name it (e.g., "Message Overlay")
   - Check "Local file" and click "Browse"
   - Enter the URL: `http://localhost:5000`
   - Set the width and height to match your desired overlay size
   - Check "Shutdown source when not visible" if you want to save resources
   - Click "OK"

3. Position and size the browser source in your scene:
   - The overlay will appear in your scene
   - You can resize and position it like any other source
   - The overlay will update in real-time as you type messages

### Customizing the Animation

You can customize the text animation using the controls in the main window:

- **Min Characters**: Minimum number of characters to display at once
- **Max Characters**: Maximum number of characters to display at once
- **Words per Minute**: Speed of the text animation

### Tips for OBS Setup

1. **Transparency**: The web overlay has a transparent background by default
2. **Performance**: 
   - If you experience performance issues, try reducing the browser source's width and height
   - You can also check "Shutdown source when not visible" in the browser source properties
3. **Positioning**:
   - Use the browser source's position and size controls in OBS for precise placement
   - The overlay will maintain its aspect ratio by default
4. **Multiple Displays**:
   - You can add multiple browser sources with different sizes/positions
   - Each will show the same content but can be styled differently

## Building the Executable

To create a standalone executable:

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run the build script:
```bash
python build.py
```

The executable will be created in the `dist` directory as `MuteStreamerOverload.exe`.

### Building Requirements

- Windows 10 or later
- Python 3.8 or later
- Administrator privileges (required for keyboard hooks)

### Project Structure

```
mute_streamer_overload/
├── core/              # Core functionality
│   ├── text_animator.py
│   └── input_handler.py
├── ui/                # User interface components
│   ├── main_window.py
│   └── overlay_window.py
├── utils/             # Utility functions and constants
│   └── constants.py
├── web/               # Web server and templates
│   ├── web_server.py
│   └── templates/
└── tests/             # Test files
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
