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
    # Always use the tts_service folder next to the executable or main.py
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__)
    return os.path.join(base_dir, 'tts_service', relative_path)

logging.basicConfig(filename='tts_debug.log', level=logging.DEBUG)
def tts_log(msg):
    print(msg)
    logging.debug(msg)

def generate_tts(text, voice, speed, pitch, volume):
    """
    Calls the generate_tts.mjs script using bun to generate speech.mp3 from the given text and settings.
    Returns True if successful, False otherwise.
    """
    # Handle paths for both development and PyInstaller bundle
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        print(f"[DEBUG] exe_dir: {exe_dir}")
        bun_path = os.path.abspath(os.path.join(exe_dir, '..', '..', 'mute_streamer_overload', 'bin', 'bun.exe'))
        print(f"[DEBUG] bun_path: {bun_path}")
        tts_service_dir = os.path.abspath(os.path.join(exe_dir, '..', '..', 'tts_service'))
        script_path = os.path.join(tts_service_dir, 'generate_tts.mjs')
    else:
        # Running from source
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level from tts_service to the project root
        base_dir = os.path.dirname(base_dir)
        bun_path = os.path.join(base_dir, 'mute_streamer_overload', 'bin', 'bun.exe')
        tts_service_dir = os.path.join(base_dir, 'tts_service')
        script_path = os.path.join(tts_service_dir, 'generate_tts.mjs')
    
    # Check if files exist
    if not os.path.exists(bun_path):
        tts_log(f'TTS ERROR: bun.exe not found at {bun_path}')
        return False
    if not os.path.exists(script_path):
        tts_log(f'TTS ERROR: generate_tts.mjs not found at {script_path}')
        return False
    if not os.path.exists(tts_service_dir):
        tts_log(f'TTS ERROR: tts_service directory not found at {tts_service_dir}')
        return False
    
    tts_log(f'Using bun at: {bun_path}')
    tts_log(f'Using tts_service_dir: {tts_service_dir}')
    
    # Build the command
    subprocess_args = [
        bun_path,
        script_path,
        text,
        '--voice', voice,
        '--speed', str(speed),
        '--pitch', str(pitch),
        '--volume', str(volume)
    ]
    
    tts_log(f'TTS call args: {text}, {voice}, {speed}, {pitch}, {volume}')
    
    # Set up subprocess kwargs
    kwargs = {
        'cwd': tts_service_dir,
        'capture_output': True,
        'text': True
        # Removed timeout from here since it's passed separately to subprocess.run()
    }
    # Prevent console window on Windows
    if os.name == 'nt':
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW

    tts_log(f"Running command: {' '.join(subprocess_args)} in cwd: {kwargs['cwd']}")
    try:
        result = subprocess.run(subprocess_args, **kwargs, timeout=60)  # Increased timeout to 60 seconds
    except subprocess.TimeoutExpired:
        tts_log('TTS subprocess timed out after 60 seconds!')
        return False
    except FileNotFoundError:
        tts_log(f'TTS subprocess failed: bun.exe not found at {bun_path}')
        return False
    except Exception as e:
        tts_log(f'TTS subprocess failed with exception: {e}')
        return False
        
    tts_log('TTS subprocess stdout:')
    tts_log(result.stdout)
    if result.returncode != 0:
        tts_log('TTS subprocess stderr:')
        tts_log(result.stderr)
        tts_log(f"TTS generation failed with return code {result.returncode}")
        return False
    
    # Check if the output file was created
    output_file = os.path.join(tts_service_dir, 'speech.mp3')
    if not os.path.exists(output_file):
        tts_log(f'TTS ERROR: Output file not found at {output_file}')
        return False
    
    tts_log(f'TTS generation successful: {output_file}')
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
    # Always use the tts_service folder next to the executable or main.py
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        # Go up two directories to project root, then to tts_service
        tts_service_dir = os.path.abspath(os.path.join(exe_dir, '..', '..', 'tts_service'))
    else:
        tts_service_dir = os.path.dirname(__file__)
    mp3_path = os.path.join(tts_service_dir, 'speech.mp3')
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