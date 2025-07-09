import sys
import logging
from pathlib import Path
import threading
import time
import re
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import multiprocessing

from mute_streamer_overload.utils.config import get_config

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Global State ---
socketio = None
server_thread = None
fade_out_callback = None
animation_in_progress = False

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
        global animation_in_progress
        print(f"[WEB ANIMATOR] start_animation called with: '{message}'")
        
        # Prevent duplicate animations
        if animation_in_progress:
            print(f"[WEB ANIMATOR] Animation already in progress, skipping")
            return
            
        animation_in_progress = True
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
        global socketio
        if not self.current_message or not socketio: return
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
                # Emit the additive build-up
                last_sentence = ' '.join(sentence_words)
                socketio.emit('text_update', {'text': last_sentence})
                time.sleep(delay)
                i += 1
            # After reaching max_chars, pause before next sentence
            if i < n:
                time.sleep(delay)
        # At the end, keep the last sentence and then fade out
        if not self._stop_animation_flag:
            time.sleep(1.0)  # Show the final sentence for 1 second
            socketio.emit('fade_out', {})
            # Notify main window if callback is set
            if fade_out_callback:
                fade_out_callback()
        
        # Reset animation progress flag
        global animation_in_progress
        animation_in_progress = False
        print(f"[WEB ANIMATOR] Animation finished, flag reset")

    def stop_animation(self):
        self._stop_animation_flag = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()

text_animator = WebTextAnimator()

# --- Flask & SocketIO Setup ---
app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))

@app.route('/')
def index():
    return render_template('overlay.html')

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
    """The target function for the server thread."""
    global socketio
    logger.info("SERVER THREAD: Starting Flask-SocketIO server...")
    try:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        
        @socketio.on('connect')
        def handle_connect():
            global socketio
            logger.info("Client connected to web overlay.")
            if text_animator.current_message and socketio:
                socketio.emit('text_update', {'text': text_animator.current_message})

        # Get server settings from config
        host = get_config("web_server.host", "127.0.0.1")
        port = get_config("web_server.port", 5000)
        
        logger.info(f"SERVER THREAD: Attempting to run socketio.run() on {host}:{port}")
        socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True, log_output=False)
        logger.info("SERVER THREAD: Server has shut down.")
    except Exception as e:
        logger.error(f"SERVER THREAD: A critical error occurred: {e}", exc_info=True)
    finally:
        logger.info("SERVER THREAD: Task finished.")

def run_server():
    logger.info("[SERVER] run_server called")
    """Creates and starts the server thread."""
    global server_thread
    
    # Check if auto-start is enabled
    if not get_config("web_server.auto_start", True):
        logger.info("Web server auto-start is disabled in configuration.")
        return None
    
    if server_thread and server_thread.is_alive():
        logger.warning("Server thread is already running.")
        return server_thread
        
    logger.info("Creating and starting server thread...")
    server_thread = threading.Thread(target=start_server_task, daemon=True)
    server_thread.start()
    time.sleep(2) # Give the server a moment to initialize
    return server_thread

def stop_server():
    """
    No explicit stop is needed for a daemon thread. It will be terminated
    when the main application exits. This avoids the request context error.
    """
    logger.info("Main application is shutting down. Server daemon thread will exit automatically.")
    pass

if __name__ == '__main__':
    if multiprocessing.current_process().name == 'MainProcess':
        logger.info("Starting web server...")
        server_thread = run_server()
        ... 