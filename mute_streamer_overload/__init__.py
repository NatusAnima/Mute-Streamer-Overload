"""
Mute Streamer Overload - A tool for creating animated text overlays for streamers
"""

__version__ = "0.1.0"

from mute_streamer_overload.ui.main_window import MuteStreamerOverload
from mute_streamer_overload.web.web_server import run_server, update_message, update_animation_settings

__all__ = [
    'MuteStreamerOverload',
    'run_server',
    'update_message',
    'update_animation_settings',
] 