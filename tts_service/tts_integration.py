import subprocess
import os
import pygame
import time
import sys
from mute_streamer_overload.utils.config import get_config, auto_update_wpm_for_tts_speed
import requests

def generate_tts(text, voice, speed, pitch, volume):
    """
    Calls the generate_tts.mjs script using bun to generate speech.mp3 from the given text and settings.
    Returns True if successful, False otherwise.
    """
    script_path = os.path.join(os.path.dirname(__file__), 'generate_tts.mjs')
    print("TTS call args:", text, voice, speed, pitch, volume)
    # Prepare subprocess arguments
    subprocess_args = [
        'bun', script_path, text,
        '--voice', str(voice),
        '--speed', str(speed),
        '--pitch', str(pitch),
        '--volume', str(volume)
    ]
    
    # Add creationflags to hide the window on Windows
    kwargs = {
        'capture_output': True,
        'text': True,
        'cwd': os.path.dirname(__file__)
    }
    
    # Hide the command prompt window on Windows
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    
    result = subprocess.run(subprocess_args, **kwargs)
    print('TTS subprocess stdout:')
    print(result.stdout)
    if result.returncode != 0:
        print('TTS subprocess stderr:')
        print(result.stderr)
        print("TTS generation failed:", result.stderr)
        return False
    return True

def notify_overlay_start(text, wpm):
    try:
        requests.post('http://127.0.0.1:5000/start_tts_animation', json={'text': text, 'wpm': wpm})
    except Exception as e:
        print(f"Failed to notify overlay: {e}")

def play_tts(text, speed):
    """
    Plays the generated speech.mp3 file and notifies the overlay to start animation.
    """
    mp3_path = os.path.join(os.path.dirname(__file__), 'speech.mp3')
    if not os.path.exists(mp3_path):
        print(f"MP3 file not found: {mp3_path}")
        return
    pygame.mixer.init()
    pygame.mixer.music.load(mp3_path)
    pygame.mixer.music.play()
    # Wait until playback actually starts
    while not pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    # Now notify overlay
    if get_config("tts.sync_overlay_wpm_with_tts", True):
        wpm = 500 * speed
    else:
        wpm = get_config("animation.words_per_minute", 500)
    notify_overlay_start(text, wpm)
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    # Unload the music to release the file lock (Windows)
    try:
        pygame.mixer.music.unload()  # Only available in pygame 2.0+
    except AttributeError:
        pass
    pygame.mixer.quit()

def speak(text):
    """
    Generates TTS for the given text and plays it if successful.
    """
    # Wait for any current playback to finish
    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    voice = get_config("tts.voice", "en-US-AvaMultilingualNeural")
    speed = get_config("tts.speed", 1.0)
    pitch = get_config("tts.pitch", 1.0)
    volume = get_config("tts.volume", 1.0)
    # Only auto-update WPM if sync is enabled
    if get_config("tts.sync_overlay_wpm_with_tts", True):
        auto_update_wpm_for_tts_speed(speed)
    if generate_tts(text, voice, speed, pitch, volume):
        play_tts(text, speed)