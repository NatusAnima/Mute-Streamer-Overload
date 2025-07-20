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
- Comprehensive configuration system with user-friendly settings dialog
- Persistent settings that are saved and restored between sessions

## Requirements

- **Python 3.8+** (Windows 10 or later recommended)
- **Bun**: [https://bun.sh/](https://bun.sh/) (must be in your PATH)
- **ffmpeg**: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) (must be in your PATH)
- (For development) Node.js for TTS service dependencies

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

3. Install Python dependencies:
   ```bash
   pip install -r mute_streamer_overload/requirements.txt
   # For development (includes testing tools):
   pip install -r requirements-dev.txt
   ```

4. (Optional) Install Node.js dependencies for TTS service:
   ```bash
   cd tts_service
   bun install
   cd ..
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

### Configuration and Settings

- Access the settings via the "⚙ Settings" button in the main window.
- All settings are saved automatically.
- For advanced configuration, see [CONFIGURATION.md](mute_streamer_overload/docs/CONFIGURATION.md).

### Using the Desktop Overlay

- Launch the application.
- Click "Show Overlay" to display the overlay window.
- Adjust the size and position as needed.
- Use F4 to start typing your message, and F4 again to submit.

### Using the Web Overlay in OBS

- The application starts a local web server automatically.
- In OBS, add a new Browser Source with the URL: `http://localhost:5000`
- Set the width and height to match your overlay.
- The overlay updates in real-time as you type messages.

### Customizing the Animation

- Use the main window or settings dialog to adjust:
  - Min/Max Characters
  - Words per Minute (WPM)
  - Overlay appearance

## Building the Executable

To create a standalone executable:

1. Ensure all dependencies are installed (see above).
2. Run the build script:
   ```bash
   python build.py
   ```
   - This will:
     - Clean previous builds
     - Bundle all required files, including web templates and static assets
     - Set the application icon
     - Output the executable to `dist/MuteStreamerOverload/MuteStreamerOverload.exe`

3. **Note:**  
   - The executable will work as long as the `mute_streamer_overload/bin/bun.exe` and `tts_service/` directories remain in their original locations relative to the project root.
   - The icon is set for both the window and the taskbar, with robust fallback logic for both dev and exe modes.

## Troubleshooting

- **Missing Bun or ffmpeg:**  
  Ensure both are installed and in your system PATH.
- **Web overlay not updating:**  
  Make sure the web server is running and accessible at `http://localhost:5000`.
- **Templates not found in exe:**  
  The build script now bundles templates and static files using `--add-data`. If you add new templates/static files, rebuild the exe.
- **Icon not showing:**  
  The app now checks both the bundled and project root assets for the icon.

## Project Structure

```
mute_streamer_overload/
├── core/              # Core functionality
├── ui/                # User interface components
├── utils/             # Utility functions and constants
├── web/               # Web server and templates
├── docs/              # Documentation
├── tests/             # Test files
├── bin/               # Bundled binaries (bun.exe, etc.)
tts_service/           # TTS service (Node.js/Bun)
assets/                # Icons and other assets
build.py               # Build script
main.py                # Main entry point
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Bun.exe Download

**bun.exe is not included in this repository due to GitHub file size limits.**

- Download the latest Windows release of Bun from the official site:
  - [https://bun.sh/](https://bun.sh/) (click "Download" and select Windows)
  - Or direct link to releases: [https://github.com/oven-sh/bun/releases](https://github.com/oven-sh/bun/releases)
- Extract or rename the downloaded `bun.exe` and place it in:
  - `mute_streamer_overload/bin/bun.exe`

The application expects `bun.exe` to be at this exact location. If you update Bun, simply replace the file in this folder.
