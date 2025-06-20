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
import requests
import signal

# Configure logging with a simpler format to avoid recursion
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Simplified format without timestamps
)
logger = logging.getLogger(__name__)

# Global variables for server control
server_thread = None
server_running = False
socketio = None  # Will be set in start_server
shutdown_event = threading.Event()
_shutdown_in_progress = False  # Flag to prevent recursive shutdown
_app_context = None  # Store app context for shutdown

# Get the base directory for templates
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle (PyInstaller)
    base_dir = Path(sys._MEIPASS)
    template_dir = base_dir / 'mute_streamer_overload' / 'web' / 'templates'
    static_dir = base_dir / 'mute_streamer_overload' / 'web' / 'static'
else:
    # If the application is run from a Python interpreter
    base_dir = Path(__file__).parent  # This is the web directory
    template_dir = base_dir / 'templates'
    static_dir = base_dir / 'static'

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
    global server_running, app, socketio, _app_context
    try:
        print("Starting Flask server...")
        
        # Ensure the template directory exists
        if not template_dir.exists():
            print(f"Template directory not found: {template_dir}")
            return False

        # Check if template exists
        template_file = template_dir / 'overlay.html'
        if not template_file.exists():
            print(f"Template file not found: {template_file}")
            return False

        print("Starting server on http://127.0.0.1:5000")
        server_running = True
        shutdown_event.clear()
        
        # Create a new Flask app instance for this thread
        print("Creating Flask application...")
        app = Flask(__name__, 
                   template_folder=str(template_dir),
                   static_folder=str(static_dir))
        
        # Store app context for shutdown
        _app_context = app.app_context()
        _app_context.push()
        
        # Configure SocketIO with threading
        print("Configuring SocketIO with threading...")
        try:
            socketio = SocketIO(app, 
                              cors_allowed_origins="*", 
                              async_mode='threading',
                              logger=False,  # Disable logging
                              engineio_logger=False)  # Disable engineio logging
            print("SocketIO configured successfully")
        except Exception as e:
            print(f"Failed to configure SocketIO: {str(e)}")
            return False
        
        # Register routes and event handlers
        @app.route('/')
        def index():
            if shutdown_event.is_set():
                return "Server is shutting down", 503
            return render_template('overlay.html')
            
        @app.route('/health')
        def health_check():
            if shutdown_event.is_set():
                return jsonify({"status": "shutting_down"}), 503
            return jsonify({"status": "ok"})
            
        @app.route('/shutdown', methods=['POST'])
        def shutdown():
            """Endpoint to trigger server shutdown"""
            if not shutdown_event.is_set():
                print("Received shutdown request")
                shutdown_event.set()
            return 'Server shutting down...'
        
        try:
            # Run the server with shutdown support
            while not shutdown_event.is_set():
                try:
                    # Check if port is already in use
                    import socket
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    try:
                        sock.bind(('127.0.0.1', 5000))
                        sock.close()
                    except socket.error:
                        print("Port 5000 is already in use")
                        return False

                    # Use Flask development server with threading
                    print("Starting Flask development server")
                    socketio.run(app, 
                               host='127.0.0.1', 
                               port=5000, 
                               debug=False, 
                               use_reloader=False,
                               log_output=False)  # Disable logging
                    break
                except Exception as e:
                    if not shutdown_event.is_set():
                        print(f"Server error: {str(e)}")
                        time.sleep(1)
                    else:
                        break
            
            print("Server loop ended")
            server_running = False
            return True
        except Exception as e:
            print(f"Failed to start socketio server: {str(e)}")
            server_running = False
            return False
    except Exception as e:
        print(f"Failed to start server: {str(e)}")
        server_running = False
        return False
    finally:
        if _app_context:
            _app_context.pop()

def stop_server():
    """Stop the web server"""
    global server_thread, socketio, _shutdown_in_progress, _app_context
    
    # Prevent recursive shutdown
    if _shutdown_in_progress:
        print("Server shutdown already in progress")
        return
    
    _shutdown_in_progress = True
    
    try:
        if not server_thread or not server_thread.is_alive():
            print("Server is not running")
            return
            
        print("Stopping server...")
        
        # Set shutdown event first
        shutdown_event.set()
        
        # Try to send shutdown request
        try:
            requests.post('http://127.0.0.1:5000/shutdown', timeout=1)
        except requests.RequestException:
            pass  # Ignore connection errors
        
        # Wait for the server to stop
        server_thread.join(timeout=5)
        
        # Force stop if still running
        if server_thread.is_alive():
            print("Server did not stop gracefully, forcing shutdown")
            if socketio:
                try:
                    socketio.stop()
                except Exception:
                    pass  # Ignore any errors during force stop
        else:
            print("Server stopped successfully")
            
    except Exception as e:
        print(f"Error stopping server: {str(e)}")
        if socketio:
            try:
                socketio.stop()
            except Exception:
                pass
    finally:
        # Clean up resources
        try:
            if _app_context:
                _app_context.pop()
        except Exception:
            pass
        _app_context = None
        server_thread = None
        socketio = None
        _shutdown_in_progress = False
        print("Server cleanup complete")

def run_server():
    """Start the server in a background thread"""
    global server_thread
    try:
        logger.info("Creating server thread...")
        # Create a non-daemon thread to keep the server running
        server_thread = threading.Thread(target=start_server)
        server_thread.daemon = False  # Make it a non-daemon thread
        
        logger.info("Starting server thread...")
        server_thread.start()
        
        # Wait a bit to check if server starts successfully
        logger.info("Waiting for server to initialize...")
        time.sleep(2)  # Increased wait time
        
        if not server_thread.is_alive():
            logger.error("Server thread died immediately")
            # Get the exception that caused the thread to die
            import traceback
            logger.error("Server thread exception:", exc_info=True)
            return None
            
        # Try to connect to the server to verify it's running
        logger.info("Performing server health check...")
        try:
            import requests
            logger.info("Attempting to connect to http://127.0.0.1:5000/health")
            response = requests.get('http://127.0.0.1:5000/health', timeout=5)
            logger.info(f"Health check response: {response.status_code} - {response.text}")
            if response.status_code == 200:
                logger.info("Server health check passed")
            else:
                logger.error(f"Server health check failed with status code: {response.status_code}")
                logger.error(f"Response content: {response.text}")
                return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Failed to connect to server: {str(e)}")
            logger.error("Connection error details:", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Server health check failed: {str(e)}")
            logger.error("Health check error details:", exc_info=True)
            return None
            
        logger.info("Server thread started successfully")
        return server_thread
    except Exception as e:
        logger.error(f"Failed to create server thread: {str(e)}")
        logger.error("Thread creation error details:", exc_info=True)
        return None

# Remove the atexit handler since we handle shutdown in the main window's closeEvent
# atexit.register(stop_server)  # Comment out or remove this line 