from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO
import threading
import time
import sys
import logging
from pathlib import Path
import requests

# Import the bridge and set its socketio instance at startup
from mute_streamer_overload.core import web_bridge

logger = logging.getLogger(__name__)

server_thread = None
shutdown_event = threading.Event()

def get_project_root() -> Path:
    """Gets the project root directory, whether running as script or frozen."""
    if getattr(sys, 'frozen', False):
        # The .exe file is in the 'dist' directory
        return Path(sys.executable).parent.parent
    else:
        # In development, __file__ is in .../mute_streamer_overload/web
        return Path(__file__).parent.parent.parent

def create_app():
    """Creates and configures the Flask application."""
    root = get_project_root()
    template_dir = root / 'mute_streamer_overload' / 'web' / 'templates'
    static_dir = root / 'mute_streamer_overload' / 'web' / 'static'
    
    logger.info(f"Template folder: {template_dir}")
    logger.info(f"Static folder: {static_dir}")

    app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
    
    # Configure Socket.IO and attach it to the app and the bridge
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=False, engineio_logger=False)
    web_bridge.socketio = socketio

    @app.route('/')
    def index():
        return render_template('overlay.html')

    @app.route('/health')
    def health_check():
        return jsonify({"status": "ok"})

    return app, socketio

def start_server_thread():
    """The target function for the server thread."""
    app, socketio = create_app()
    logger.info("Starting Flask-SocketIO server...")
    try:
        socketio.run(app, host='127.0.0.1', port=5000, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Server thread failed: {e}", exc_info=True)
    finally:
        logger.info("Server thread has shut down.")

def stop_server():
    """Stops the server thread."""
    if server_thread and server_thread.is_alive():
        logger.info("Attempting to shut down the web server...")
        try:
            # The 'requests' call is a reliable way to trigger shutdown on the server's thread
            requests.post('http://127.0.0.1:5000/socket.io/?EIO=3&transport=polling')
        except requests.ConnectionError:
            # This is expected if the server is already down
            logger.info("Server was not reachable for shutdown. It may already be down.")
        except Exception as e:
            logger.error(f"Error sending shutdown request: {e}")
        
        shutdown_event.set()
        server_thread.join(timeout=5)
        if server_thread.is_alive():
            logger.warning("Server thread did not shut down gracefully.")

def run_server():
    """Starts the server and performs a health check."""
    global server_thread
    if server_thread and server_thread.is_alive():
        logger.warning("Server is already running.")
        return server_thread

    shutdown_event.clear()
    server_thread = threading.Thread(target=start_server_thread, daemon=True)
    server_thread.start()
    
    # --- CRITICAL FIX FOR RACE CONDITION ---
    # Give the server thread a moment to initialize before health checking.
    logger.info("Waiting for server to initialize...")
    time.sleep(2) # 2 seconds should be plenty.

    # Health Check
    for i in range(5): # Retry a few times
        try:
            response = requests.get('http://127.0.0.1:5000/health', timeout=1)
            if response.status_code == 200:
                logger.info("Server health check passed.")
                return server_thread
        except requests.ConnectionError:
            logger.warning(f"Health check failed (attempt {i+1}/5). Retrying...")
            time.sleep(1)
            
    logger.error("Server failed to start after multiple attempts.")
    return None 