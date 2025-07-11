import subprocess
import os
import pygame
import time
import sys
from mute_streamer_overload.utils.config import get_config, auto_update_wpm_for_tts_speed
import requests
import shutil
import logging
import tempfile

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
    return os.path.join(os.path.dirname(__file__), relative_path)

logging.basicConfig(filename='tts_debug.log', level=logging.DEBUG)
def tts_log(msg):
    print(msg)
    logging.debug(msg)

def generate_tts(text, voice, speed, pitch, volume):
    """
    Calls the generate_tts.mjs script using bun to generate speech.mp3 from the given text and settings.
    Returns True if successful, False otherwise.
    """
    # Determine script path and log directory contents for debugging
    if hasattr(sys, '_MEIPASS'):
        tts_log(f"sys._MEIPASS: {sys._MEIPASS}")  # type: ignore[attr-defined]
        tts_log(f"Files in sys._MEIPASS: {os.listdir(sys._MEIPASS)}")  # type: ignore[attr-defined]
        tts_service_dir = os.path.join(sys._MEIPASS, 'tts_service')  # type: ignore[attr-defined]
        if os.path.exists(tts_service_dir):
            tts_log(f"Files in tts_service: {os.listdir(tts_service_dir)}")
            script_path = os.path.join(tts_service_dir, 'generate_tts.mjs')
            # Fallback: if script_path is a directory, look for generate_tts.mjs inside it
            if os.path.isdir(script_path):
                fallback_path = os.path.join(script_path, 'generate_tts.mjs')
                if os.path.isfile(fallback_path):
                    tts_log(f"Fallback: using nested generate_tts.mjs at {fallback_path}")
                    # Copy the file up one directory
                    fixed_path = os.path.join(tts_service_dir, 'generate_tts_fixed.mjs')
                    shutil.copy2(fallback_path, fixed_path)
                    tts_log(f"Copied {fallback_path} to {fixed_path}")
                    script_path = fixed_path
            cwd = tts_service_dir
        else:
            script_path = os.path.join(sys._MEIPASS, 'generate_tts.mjs')  # type: ignore[attr-defined]  # fallback
            cwd = sys._MEIPASS  # type: ignore[attr-defined]
        tts_log(f"cwd: {cwd}")
        tts_log(f"Files in cwd: {os.listdir(cwd)}")
    else:
        script_path = resource_path('generate_tts.mjs')
        tts_log(f"Files in tts_service: {os.listdir(os.path.dirname(__file__))}")
        cwd = os.path.dirname(__file__)
    tts_log(f"TTS call args: {text}, {voice}, {speed}, {pitch}, {volume}")
    if shutil.which('bun') is None:
        tts_log("Error: 'bun' is not installed or not in PATH.")
        return False
    # --- Removed temp directory logic. Run Bun in place. ---
    # script_path is always 'generate_tts.mjs' in cwd
    script_path = 'generate_tts.mjs'
    tts_log(f'Running Bun in {cwd}')
    subprocess_args = [
        'bun', script_path, text,
        '--voice', str(voice),
        '--speed', str(speed),
        '--pitch', str(pitch),
        '--volume', str(volume)
    ]
    kwargs = {
        'capture_output': True,
        'text': True,
        'cwd': cwd
    }
    if sys.platform == 'win32':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
    tts_log(f"Running command: {' '.join(subprocess_args)} in cwd: {cwd}")
    try:
        result = subprocess.run(subprocess_args, **kwargs, timeout=10)
    except subprocess.TimeoutExpired:
        tts_log('TTS subprocess timed out!')
        return False
    tts_log('TTS subprocess stdout:')
    tts_log(result.stdout)
    if result.returncode != 0:
        tts_log('TTS subprocess stderr:')
        tts_log(result.stderr)
        tts_log(f"TTS generation failed: {result.stderr}")
        return False
    return True

def notify_overlay_start(text, wpm):
    try:
        requests.post('http://127.0.0.1:5000/start_tts_animation', json={'text': text, 'wpm': wpm})
    except Exception as e:
        tts_log(f"Failed to notify overlay: {e}")

def play_tts(text, speed):
    """
    Plays the generated speech.mp3 file and notifies the overlay to start animation.
    """
    mp3_path = os.path.join(os.path.dirname(__file__), 'speech.mp3')
    if not os.path.exists(mp3_path):
        tts_log(f"MP3 file not found: {mp3_path}")
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