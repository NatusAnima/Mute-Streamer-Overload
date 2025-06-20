import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import sys

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages application configuration and user preferences."""
    
    def __init__(self):
        self.config_file = self._get_config_path()
        self.config = self._load_default_config()
        self.load_config()
    
    def _get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        if getattr(sys, 'frozen', False):
            # Running as a bundled app - store in user's app data
            config_dir = Path.home() / 'AppData' / 'Local' / 'MuteStreamerOverload'
        else:
            # Running from source - store in project directory
            config_dir = Path(__file__).parent.parent.parent
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / 'profile.json'
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values."""
        return {
            # Window and Overlay Settings
            "overlay": {
                "initial_width": 300,
                "initial_height": 200,
                "min_width": 200,
                "min_height": 100,
                "start_visible": False,
                "always_on_top": True,
                "opacity": 0.9
            },
            
            # Animation Settings
            "animation": {
                "words_per_minute": 200,
                "min_characters": 10,
                "max_characters": 50,
                "animation_delay_ms": 100
            },
            
            # Web Server Settings
            "web_server": {
                "host": "127.0.0.1",
                "port": 5000,
                "auto_start": True
            },
            
            # UI Settings
            "ui": {
                "theme": "dark",
                "window_width": 600,
                "window_height": 500,
                "window_x": None,  # Will be centered if None
                "window_y": None   # Will be centered if None
            },
            
            # Input Settings
            "input": {
                "start_hotkey": ["F4"],
                "submit_hotkey": ["F4"],
                "suppress_hotkey": False
            },
            
            # General Settings
            "general": {
                "auto_save_config": True,
                "log_level": "INFO",
                "check_for_updates": True
            },
            
            # Twitch Integration
            "twitch": {
                "client_id": None,
                "client_secret": None,
                "access_token": None,
                "refresh_token": None,
                "username": None,
                "channel": None
            },
        }
    
    def load_config(self) -> None:
        """Load configuration from file, merging with defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                
                # Merge file config with defaults (deep merge)
                self._merge_configs(self.config, file_config)
                logger.info(f"Configuration loaded from {self.config_file}")
            else:
                logger.info("No configuration file found, using defaults")
                self.save_config()  # Save default config
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in override.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_configs(default[key], value)
            else:
                default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation (e.g., 'overlay.initial_width')."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set a configuration value using dot notation."""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Auto-save if enabled
        if self.get('general.auto_save_config', True):
            self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = self._load_default_config()
        self.save_config()
        logger.info("Configuration reset to defaults")
    
    def get_config_file_path(self) -> Path:
        """Get the path to the configuration file."""
        return self.config_file
    
    def export_config(self, export_path: Path) -> None:
        """Export current configuration to a specified path."""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration exported to {export_path}")
        except Exception as e:
            logger.error(f"Failed to export configuration: {e}")
    
    def import_config(self, import_path: Path) -> None:
        """Import configuration from a specified path."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Validate the imported config structure
            if isinstance(imported_config, dict):
                self._merge_configs(self.config, imported_config)
                self.save_config()
                logger.info(f"Configuration imported from {import_path}")
            else:
                raise ValueError("Invalid configuration format")
        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")

# Global configuration instance
config_manager = ConfigManager()

# Convenience functions for common operations
def get_config(key_path: str, default: Any = None) -> Any:
    """Get a configuration value."""
    return config_manager.get(key_path, default)

def set_config(key_path: str, value: Any) -> None:
    """Set a configuration value."""
    config_manager.set(key_path, value)

def save_config() -> None:
    """Save the current configuration."""
    config_manager.save_config()

def reset_config() -> None:
    """Reset configuration to defaults."""
    config_manager.reset_to_defaults() 