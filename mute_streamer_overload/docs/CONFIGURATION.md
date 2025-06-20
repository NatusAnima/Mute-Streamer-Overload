# Configuration System

The Mute Streamer Overload application includes a comprehensive configuration system that allows users to customize various aspects of the application behavior.

## Overview

The configuration system stores user preferences in a JSON file and provides both programmatic access and a user-friendly settings dialog. All settings are automatically saved and restored between application sessions.

## Configuration File Location

- **Development**: `profile.json` in the project root directory
- **Bundled App**: `%LOCALAPPDATA%\MuteStreamerOverload\profile.json`

## Available Settings

### Overlay Settings
- `overlay.initial_width`: Initial width of the overlay window (default: 400px)
- `overlay.initial_height`: Initial height of the overlay window (default: 200px)
- `overlay.min_width`: Minimum width of the overlay window (default: 200px)
- `overlay.min_height`: Minimum height of the overlay window (default: 100px)
- `overlay.start_visible`: Whether to show the overlay on startup (default: false)
- `overlay.always_on_top`: Whether the overlay should stay on top (default: true)
- `overlay.opacity`: Overlay opacity from 0.0 to 1.0 (default: 0.9)

### Animation Settings
- `animation.words_per_minute`: Speed of text animation (default: 200 WPM)
- `animation.min_characters`: Minimum characters per animation step (default: 10)
- `animation.max_characters`: Maximum characters per animation step (default: 50)
- `animation.animation_delay_ms`: Delay between animation steps (default: 100ms)

### Web Server Settings
- `web_server.host`: Host address for the web server (default: "127.0.0.1")
- `web_server.port`: Port for the web server (default: 5000)
- `web_server.auto_start`: Whether to start the web server automatically (default: true)

### UI Settings
- `ui.theme`: Application theme (default: "dark")
- `ui.window_width`: Main window width (default: 800px)
- `ui.window_height`: Main window height (default: 600px)
- `ui.window_x`: Main window X position (default: null, centers window)
- `ui.window_y`: Main window Y position (default: null, centers window)

### Input Settings
- `input.hotkey`: Keyboard shortcut for text input (default: "F4")
- `input.suppress_hotkey`: Whether to suppress the hotkey in other applications (default: false)

### General Settings
- `general.auto_save_config`: Whether to auto-save configuration changes (default: true)
- `general.log_level`: Logging level (default: "INFO")
- `general.check_for_updates`: Whether to check for updates (default: true)

## Using the Settings Dialog

1. Click the "⚙ Settings" button in the main window
2. Navigate through the different tabs to modify settings
3. Click "Save" to apply changes, or "Cancel" to discard them
4. Use "Reset to Defaults" to restore all settings to their default values
5. Use "Export Config" and "Import Config" to backup/restore settings

## Programmatic Access

### Getting Configuration Values
```python
from mute_streamer_overload.utils.config import get_config

# Get a value with default fallback
wpm = get_config("animation.words_per_minute", 200)

# Get a value without default (returns None if not found)
theme = get_config("ui.theme")
```

### Setting Configuration Values
```python
from mute_streamer_overload.utils.config import set_config, save_config

# Set a value (auto-saves if auto_save_config is enabled)
set_config("animation.words_per_minute", 300)

# Manually save configuration
save_config()
```

### Resetting Configuration
```python
from mute_streamer_overload.utils.config import reset_config

# Reset all settings to defaults
reset_config()
```

## Configuration File Format

The configuration file uses JSON format with nested objects for organization:

```json
{
  "overlay": {
    "initial_width": 400,
    "initial_height": 200,
    "always_on_top": true
  },
  "animation": {
    "words_per_minute": 200,
    "min_characters": 10,
    "max_characters": 50
  }
}
```

## Migration and Compatibility

- The configuration system automatically merges new default values with existing configurations
- Missing settings are automatically added with default values
- The system is backward compatible and will preserve user settings during updates

## Troubleshooting

### Configuration File Issues
- If the configuration file becomes corrupted, delete it and restart the application
- The application will recreate the file with default values
- Check file permissions if the application cannot write to the configuration directory

### Settings Not Applied
- Ensure you clicked "Save" in the settings dialog
- Check that auto-save is enabled in general settings
- Restart the application to ensure all settings are properly loaded

### Web Server Configuration
- If the web server fails to start, check the host and port settings
- Ensure the port is not already in use by another application
- Try changing the port number if there are conflicts 