from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import threading
import queue
import time
import re
import os
import sys
import logging
import atexit
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('mute_streamer_overload.log')
    ]
)
logger = logging.getLogger(__name__)

# Global variables for server control
server_thread = None
server_running = False
socketio = None  # Will be set in start_server
shutdown_event = threading.Event()

# Get the base directory for templates
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (PyInstaller)
    base_dir = Path(sys._MEIPASS)
    template_dir = base_dir / 'mute_streamer_overload' / 'web' / 'templates'
    static_dir = base_dir / 'mute_streamer_overload' / 'web' / 'static'
else:
    # If the application is run from a Python interpreter
    base_dir = Path(__file__).parent.parent.parent  # Go up to mute_streamer_overload root
    template_dir = base_dir / 'web' / 'templates'
    static_dir = base_dir / 'web' / 'static'

logger.info(f"Base directory: {base_dir}")
logger.info(f"Template directory: {template_dir}")
logger.info(f"Static directory: {static_dir}")

app = Flask(__name__, 
           template_folder=str(template_dir),
           static_folder=str(static_dir))
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

class WebTextAnimator:
    def __init__(self):
        self.current_message = ""
        self.animation_thread = None
        self.is_animating = False
        self.stop_animation = False
        self.settings = {
            'wpm': 200,
            'min_chars': 10,
            'max_chars': 50
        }

    def update_settings(self, wpm=None, min_chars=None, max_chars=None):
        """Update animation settings"""
        if wpm is not None:
            self.settings['wpm'] = wpm
        if min_chars is not None:
            self.settings['min_chars'] = min_chars
        if max_chars is not None:
            self.settings['max_chars'] = max_chars

    def _get_next_words(self, words, current_index):
        """Get the next set of words based on character limits"""
        if current_index >= len(words):
            return [], current_index

        result = []
        char_count = 0
        i = current_index

        while i < len(words):
            word = words[i]
            if char_count + len(word) + (len(result) if result else 0) > self.settings['max_chars']:
                if not result:  # If we can't even fit one word, force it
                    result.append(word)
                    i += 1
                break
            if char_count + len(word) + (len(result) if result else 0) >= self.settings['min_chars'] and result:
                break
            result.append(word)
            char_count += len(word)
            i += 1

        return result, i

    def start_animation(self, message, words_per_chunk=None, delay=None):
        """Start animating the text with exact timing from overlay"""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation = True
            self.animation_thread.join()

        self.current_message = message
        self.stop_animation = False
        self.is_animating = True
        
        # If timing parameters are provided, use them for exact sync
        if words_per_chunk is not None and delay is not None:
            self.animation_thread = threading.Thread(
                target=self._animate_text_sync,
                args=(message, words_per_chunk, delay)
            )
        else:
            self.animation_thread = threading.Thread(target=self._animate_text)
        
        self.animation_thread.daemon = True
        self.animation_thread.start()

    def _animate_text_sync(self, message, words_per_chunk, delay):
        """Animate text with exact timing from overlay"""
        if not message:
            return

        words = re.findall(r'\S+|\s+', message)
        current_index = 0

        while not self.stop_animation and current_index < len(words):
            next_words, current_index = self._get_next_words(words, current_index)
            if next_words:
                text = ' '.join(next_words)
                socketio.emit('text_update', {'text': text})
                time.sleep(delay)

        if not self.stop_animation:
            socketio.emit('text_update', {'text': self.current_message})
        self.is_animating = False

    def _animate_text(self):
        """Default animation with calculated timing"""
        if not self.current_message:
            return

        words = re.findall(r'\S+|\s+', self.current_message)
        current_index = 0
        delay = 60.0 / self.settings['wpm']

        while not self.stop_animation and current_index < len(words):
            next_words, current_index = self._get_next_words(words, current_index)
            if next_words:
                text = ' '.join(next_words)
                socketio.emit('text_update', {'text': text})
                time.sleep(delay)

        if not self.stop_animation:
            socketio.emit('text_update', {'text': self.current_message})
        self.is_animating = False

    def stop_animation(self):
        """Stop the current animation"""
        self.stop_animation = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()
        self.is_animating = False

# Create the animator instance
text_animator = WebTextAnimator()

@app.route('/')
def index():
    if shutdown_event.is_set():
        return "Server is shutting down", 503
    return render_template('overlay.html')

@socketio.on('connect')
def handle_connect():
    if shutdown_event.is_set():
        return False  # Reject new connections during shutdown
    if text_animator.current_message:
        socketio.emit('text_update', {'text': text_animator.current_message})

def update_message(text, words_per_chunk=None, delay=None):
    """Update the current message and start animation with optional sync parameters"""
    if text:
        text_animator.start_animation(text, words_per_chunk, delay)

def update_animation_settings(wpm=None, min_chars=None, max_chars=None):
    """Update animation settings"""
    text_animator.update_settings(wpm, min_chars, max_chars)

def start_server():
    """Start the Flask server in a separate thread"""
    global server_running, app, socketio
    try:
        logger.info("Starting Flask server...")
        # Ensure the template directory exists
        if not template_dir.exists():
            logger.error(f"Template directory not found: {template_dir}")
            return False

        # Check if template exists
        template_file = template_dir / 'overlay.html'
        if not template_file.exists():
            logger.error(f"Template file not found: {template_file}")
            return False

        logger.info("Starting server on http://127.0.0.1:5000")
        server_running = True
        shutdown_event.clear()
        
        # Create a new Flask app instance for this thread
        app = Flask(__name__, 
                   template_folder=str(template_dir),
                   static_folder=str(static_dir))
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        
        # Register routes and event handlers
        @app.route('/')
        def index():
            if shutdown_event.is_set():
                return "Server is shutting down", 503
            return render_template('overlay.html')
            
        @app.route('/health')
        def health_check():
            if shutdown_event.is_set():
                return jsonify({"status": "shutting_down", "message": "Server is shutting down"}), 503
            return jsonify({"status": "ok", "message": "Server is running"})
            
        @app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Endpoint to trigger server shutdown"""
            try:
                logger.info("Received shutdown request")
                shutdown_event.set()
                return 'Server shutting down...'
            except Exception as e:
                logger.error(f"Error during shutdown: {str(e)}")
                return str(e), 500
                
        @socketio.on('connect')
        def handle_connect():
            if shutdown_event.is_set():
                return False  # Reject new connections during shutdown
            if text_animator.current_message:
                socketio.emit('text_update', {'text': text_animator.current_message})
        
        try:
            # Run the server with shutdown support
            while not shutdown_event.is_set():
                try:
                    # Start the server in a way that can be interrupted
                    socketio.run(app, 
                               host='127.0.0.1', 
                               port=5000, 
                               debug=False, 
                               use_reloader=False,
                               log_output=True,
                               allow_unsafe_werkzeug=True)
                    break  # Exit if server stops normally
                except Exception as e:
                    if not shutdown_event.is_set():
                        logger.error(f"Server error: {str(e)}")
                        time.sleep(1)  # Wait before retrying
                    else:
                        break  # Exit if shutdown was requested
            
            logger.info("Server loop ended")
            server_running = False
            return True
        except Exception as e:
            logger.error(f"Failed to start socketio server: {str(e)}", exc_info=True)
            server_running = False
            return False
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        server_running = False
        return False

def stop_server():
    """Stop the Flask server"""
    global server_running, server_thread
    try:
        if not server_running:
            logger.info("Server is not running")
            return
            
        logger.info("Stopping Flask server...")
        server_running = False
        shutdown_event.set()
        
        # Try to stop the server gracefully
        try:
            import requests
            # First check if server is still responding
            try:
                response = requests.get('http://127.0.0.1:5000/health', timeout=1)
                if response.status_code == 200:
                    # Server is still running, send shutdown request
                    requests.post('http://127.0.0.1:5000/shutdown', timeout=1)
            except:
                pass  # Server might already be down
        except:
            pass  # Ignore errors during shutdown request
        
        # Wait for the server thread to finish
        if server_thread and server_thread.is_alive():
            server_thread.join(timeout=5)
            if server_thread.is_alive():
                logger.warning("Server thread did not stop gracefully")
                # Force stop the thread if it's still running
                import ctypes
                thread_id = server_thread.ident
                if thread_id:
                    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(thread_id),
                        ctypes.py_object(SystemExit)
                    )
                    if res == 0:
                        logger.error("Failed to force stop server thread")
                    elif res != 1:
                        ctypes.pythonapi.PyThreadState_SetAsyncExc(
                            ctypes.c_long(thread_id),
                            None
                        )
                        logger.error("Failed to force stop server thread")
        
        logger.info("Flask server stopped")
    except Exception as e:
        logger.error(f"Error stopping server: {str(e)}", exc_info=True)
    finally:
        server_running = False
        shutdown_event.clear()

def run_server():
    """Start the server in a background thread"""
    global server_thread
    try:
        # Create a non-daemon thread to keep the server running
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = False  # Make it a non-daemon thread
        server_thread.start()
        
        # Wait a bit to check if server starts successfully
        time.sleep(2)  # Increased wait time
        if not server_thread.is_alive():
            logger.error("Server thread died immediately")
            return None
            
        # Try to connect to the server to verify it's running
        try:
            import requests
            response = requests.get('http://127.0.0.1:5000/health', timeout=5)
            if response.status_code == 200:
                logger.info("Server health check passed")
            else:
                logger.error(f"Server health check failed with status code: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Server health check failed: {str(e)}")
            return None
            
        logger.info("Server thread started successfully")
        return server_thread
    except Exception as e:
        logger.error(f"Failed to create server thread: {str(e)}", exc_info=True)
        return None

# Register shutdown handler
atexit.register(stop_server) 