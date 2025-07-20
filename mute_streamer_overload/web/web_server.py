import sys
import logging
from pathlib import Path
import threading
import time
import re
from flask import Flask, render_template, request, jsonify
# Remove Flask-SocketIO import
import multiprocessing

from mute_streamer_overload.utils.config import get_config

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Global State ---
# Remove socketio global
server_thread = None
fade_out_callback = None
animation_in_progress = False

# Add simple state management for HTTP polling
current_display_text = ""
last_update_time = 0
animation_active = False

# --- Path Configuration ---
def get_project_root():
    """
    Determines the project root path, which is crucial for finding data files
    in both development and bundled (PyInstaller) environments.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):  # type: ignore
        # Running as a PyInstaller bundle. The root is the temporary folder.
        return Path(sys._MEIPASS)  # type: ignore
    # Running from source. The root is the project's top-level directory.
    return Path(__file__).resolve().parent.parent.parent

# Resolve paths at startup
project_root = get_project_root()
template_dir = project_root / 'mute_streamer_overload' / 'web' / 'templates'
static_dir = project_root / 'mute_streamer_overload' / 'web' / 'static'

# --- Web Text Animator ---
class WebTextAnimator:
    def __init__(self):
        self.current_message = ""
        self.animation_thread = None
        self._stop_animation_flag = False
        self.settings = {
            'wpm': get_config("animation.words_per_minute", 500),
            'min_chars': get_config("animation.min_characters", 10),
            'max_chars': get_config("animation.max_characters", 50)
        }

    def update_settings(self, wpm=None, min_chars=None, max_chars=None):
        if wpm is not None: self.settings['wpm'] = wpm
        if min_chars is not None: self.settings['min_chars'] = min_chars
        if max_chars is not None: self.settings['max_chars'] = max_chars

    def _get_next_words(self, words, current_index):
        if current_index >= len(words):
            return [], current_index
        result, char_count, i = [], 0, current_index
        while i < len(words):
            word = words[i]
            if char_count + len(word) + len(result) > self.settings['max_chars'] and result:
                break
            result.append(word)
            char_count += len(word)
            i += 1
            if char_count >= self.settings['min_chars']:
                break
        return result, i

    def start_animation(self, message):
        global animation_in_progress, current_display_text, last_update_time, animation_active
        print(f"[WEB ANIMATOR] start_animation called with: '{message}'")
        
        # Prevent duplicate animations
        if animation_in_progress:
            print(f"[WEB ANIMATOR] Animation already in progress, skipping")
            return
            
        animation_in_progress = True
        animation_active = True
        print(f"[WEB ANIMATOR] Starting new animation")
        
        if self.animation_thread and self.animation_thread.is_alive():
            print(f"[WEB ANIMATOR] Stopping existing animation")
            self._stop_animation_flag = True
            self.animation_thread.join()
        self.current_message = message
        self._stop_animation_flag = False
        self.animation_thread = threading.Thread(target=self._animate_text, daemon=True)
        self.animation_thread.start()
        print(f"[WEB ANIMATOR] Animation thread started")

    def _animate_text(self):
        global current_display_text, last_update_time, animation_active
        if not self.current_message: 
            print(f"[WEB ANIMATOR] No message available")
            return
        words = re.findall(r'\S+|\s+', self.current_message)
        i = 0
        n = len(words)
        delay = 60.0 / self.settings['wpm']
        print(f'[DEBUG] Starting animation with WPM: {self.settings["wpm"]}, delay: {delay}')
        last_sentence = ''
        while i < n and not self._stop_animation_flag:
            # Start a new sentence
            sentence_words = []
            char_count = 0
            # Build up the sentence word by word, additive
            while i < n:
                word = words[i]
                next_count = char_count + len(word) + (1 if sentence_words else 0)
                if next_count > self.settings['max_chars']:
                    break
                if sentence_words:
                    char_count += 1  # space
                sentence_words.append(word.strip())
                char_count += len(word.strip())
                # Update the global state for HTTP polling
                last_sentence = ' '.join(sentence_words)
                current_display_text = last_sentence
                last_update_time = time.time()
                print(f"[WEB ANIMATOR] Updated text: '{last_sentence}'")
                time.sleep(delay)
                i += 1
            # After reaching max_chars, pause before next sentence
            if i < n:
                time.sleep(delay)
        # At the end, keep the last sentence and then fade out
        if not self._stop_animation_flag:
            time.sleep(1.0)  # Show the final sentence for 1 second
            animation_active = False
            print(f"[WEB ANIMATOR] Animation finished")
            # Notify main window if callback is set
            if fade_out_callback:
                fade_out_callback()
            # Clear the display text after fade out
            current_display_text = ""
            last_update_time = time.time()
        
        # Reset animation progress flag
        global animation_in_progress
        animation_in_progress = False
        print(f"[WEB ANIMATOR] Animation finished, flag reset")

    def stop_animation(self):
        self._stop_animation_flag = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()

text_animator = WebTextAnimator()

# --- Flask Setup (No SocketIO) ---
app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))

@app.route('/')
def index():
    return render_template('overlay.html')

@app.route('/health')
def health_check():
    """Health check endpoint for the web overlay."""
    return jsonify({'status': 'ok', 'timestamp': time.time()})

@app.route('/api/current_text')
def get_current_text():
    """API endpoint for getting current display text (for polling)."""
    global current_display_text, last_update_time, animation_active
    return jsonify({
        'text': current_display_text,
        'timestamp': last_update_time,
        'active': animation_active
    })

@app.route('/start_tts_animation', methods=['POST'])
def start_tts_animation():
    data = request.get_json()
    text = data.get('text', '')
    wpm = data.get('wpm', 180)
    update_animation_settings(wpm=wpm)
    update_message(text)
    return jsonify({'status': 'ok'})

@app.route('/set_overlay_wpm', methods=['POST'])
def set_overlay_wpm():
    data = request.get_json()
    wpm = data.get('wpm', 500)
    update_animation_settings(wpm=wpm)
    # Don't restart animation - just update the settings for future animations
    return jsonify({'status': 'ok'})

def update_message(text):
    if multiprocessing.current_process().name != 'MainProcess':
        return
    logger.info(f"[SERVER] update_message called with: {text!r}")
    if text:
        text_animator.start_animation(text)

def update_animation_settings(wpm=None, min_chars=None, max_chars=None):
    text_animator.update_settings(wpm, min_chars, max_chars)

def set_fade_out_callback(callback):
    """Set a callback function to be called when fade_out occurs."""
    global fade_out_callback
    fade_out_callback = callback

def start_server_task():
    logger.info("SERVER THREAD: Starting Flask server...")
    try:
        # Get server settings from config
        host = get_config("web_server.host", "127.0.0.1")
        port = get_config("web_server.port", 5000)
        
        logger.info(f"SERVER THREAD: Starting server on {host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
        
    except Exception as e:
        logger.error(f"SERVER THREAD: A critical error occurred: {e}")
        import traceback
        logger.error(f"SERVER THREAD: Traceback: {traceback.format_exc()}")
    finally:
        logger.info("SERVER THREAD: Task finished.")

def run_server():
    """Start the web server in a separate thread."""
    global server_thread
    logger.info("[SERVER] run_server called")
    
    if server_thread and server_thread.is_alive():
        logger.info("Server thread already running.")
        return
    
    logger.info("Creating and starting server thread...")
    server_thread = threading.Thread(target=start_server_task, daemon=True)
    server_thread.start()
    logger.info("Server thread started successfully.")

def stop_server():
    """Stop the web server."""
    global server_thread
    if server_thread and server_thread.is_alive():
        logger.info("Stopping server thread...")
        # Flask doesn't have a clean shutdown method, so we'll let it run as daemon
        # The thread will be terminated when the main process exits
        logger.info("Server thread marked for termination.") 