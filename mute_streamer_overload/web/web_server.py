import sys
import logging
from pathlib import Path
import threading
import time
import re
from flask import Flask, render_template
from flask_socketio import SocketIO

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Global State ---
socketio = None
server_thread = None

# --- Path Configuration ---
def get_project_root():
    """
    Determines the project root path, which is crucial for finding data files
    in both development and bundled (PyInstaller) environments.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a PyInstaller bundle. The root is the temporary folder.
        return Path(sys._MEIPASS)
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
        self.settings = {'wpm': 200, 'min_chars': 10, 'max_chars': 50}

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
        if self.animation_thread and self.animation_thread.is_alive():
            self._stop_animation_flag = True
            self.animation_thread.join()
        self.current_message = message
        self._stop_animation_flag = False
        self.animation_thread = threading.Thread(target=self._animate_text, daemon=True)
        self.animation_thread.start()

    def _animate_text(self):
        global socketio
        if not self.current_message or not socketio: return
        words = re.findall(r'\S+|\s+', self.current_message)
        current_index = 0
        delay = 60.0 / self.settings['wpm']
        while not self._stop_animation_flag and current_index < len(words):
            next_words, current_index = self._get_next_words(words, current_index)
            if next_words:
                text = ''.join(next_words)
                socketio.emit('text_update', {'text': text})
                time.sleep(delay)
        if not self._stop_animation_flag:
            socketio.emit('text_update', {'text': self.current_message})

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

def update_message(text):
    if text:
        text_animator.start_animation(text)

def update_animation_settings(wpm=None, min_chars=None, max_chars=None):
    text_animator.update_settings(wpm, min_chars, max_chars)

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

        logger.info("SERVER THREAD: Attempting to run socketio.run() on port 5000")
        socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True, log_output=False)
        logger.info("SERVER THREAD: Server has shut down.")
    except Exception as e:
        logger.error(f"SERVER THREAD: A critical error occurred: {e}", exc_info=True)
    finally:
        logger.info("SERVER THREAD: Task finished.")

def run_server():
    """Creates and starts the server thread."""
    global server_thread
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