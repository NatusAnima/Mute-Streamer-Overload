import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
import multiprocessing
import shutil
import webbrowser
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    import pkg_resources
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'setuptools'])
    import pkg_resources

# --- Dependency Auto-Installer ---
def ensure_python_dependencies():
    """Ensure all Python dependencies from requirements.txt are installed."""
    req_path = os.path.join('mute_streamer_overload', 'requirements.txt')
    if not os.path.exists(req_path):
        print(f"requirements.txt not found at {req_path}")
        return
    with open(req_path) as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.strip().startswith('#')
        ]
    to_install = []
    for req in requirements:
        if not req:
            continue
        try:
            dist = pkg_resources.get_distribution(req.split('==')[0])
            # Optionally, check version here if needed
        except pkg_resources.DistributionNotFound:
            to_install.append(req)
    if to_install:
        print(f"Installing missing Python packages: {to_install}")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', *to_install])


def ensure_node_modules():
    """Ensure tts_service/node_modules exists, otherwise run npm install or bun install."""
    tts_dir = os.path.join(os.path.dirname(__file__), 'tts_service')
    node_modules = os.path.join(tts_dir, 'node_modules')
    package_json = os.path.join(tts_dir, 'package.json')
    if not os.path.exists(package_json):
        print(f"No package.json found in {tts_dir}, skipping Node.js dependency check.")
        return
    if not os.path.exists(node_modules) or not os.listdir(node_modules):
        print("Installing Node.js dependencies for tts_service...")
        # Prefer bun if available, else fallback to npm
        bun_path = shutil.which('bun')
        if bun_path:
            cmd = [bun_path, 'install']
        else:
            npm_path = shutil.which('npm')
            if not npm_path:
                print("Neither 'bun' nor 'npm' is installed. Please install one to continue.")
                sys.exit(1)
            cmd = [npm_path, 'install']
        import subprocess
        subprocess.check_call(cmd, cwd=tts_dir)

# --- Call dependency checks before anything else ---
ensure_python_dependencies()
ensure_node_modules()

from mute_streamer_overload.ui.main_window import MuteStreamerOverload
from mute_streamer_overload.web.web_server import run_server, stop_server
from mute_streamer_overload.utils.styles import get_stylesheet


def setup_logging(is_frozen):
    """Configure logging for development and bundled environments."""
    if is_frozen:
        # In a bundled app, logs should go next to the executable.
        log_dir = Path(sys.executable).parent
    else:
        # In development, logs can be in the project root.
        log_dir = Path(__file__).parent
        
    log_file = log_dir / 'app.log'
    
    # Basic console logging for immediate feedback
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Add file handler to save logs
    try:
        file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
    except Exception as e:
        logging.error(f"Failed to create log file at {log_file}: {e}")

    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Logging Initialized")
    logger.info(f"Log file: {log_file}")
    logger.info("="*50)
    return logger

def check_runtime_dependencies():
    missing = []
    if shutil.which('bun') is None:
        missing.append('Bun')
    if shutil.which('ffmpeg') is None:
        missing.append('ffmpeg')
    if missing:
        msg = ("The following required dependencies are missing:\n" +
               "\n".join(f"- {dep}" for dep in missing) +
               "\n\nPlease install them before running this application.\n\n" +
               "Bun: https://bun.sh/\n" +
               "ffmpeg: https://ffmpeg.org/download.html\n\n" +
               "After installation, ensure they are added to your system PATH.\n\n" +
               "For help, see the README.md or contact support.")
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            import sys
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Missing Dependencies", msg)
        except Exception:
            print(msg)
        # Optionally open download pages in browser
        if 'Bun' in missing:
            webbrowser.open('https://bun.sh/')
        if 'ffmpeg' in missing:
            webbrowser.open('https://ffmpeg.org/download.html')
        sys.exit(1)

def run_app():
    """Create and run the main application components."""
    is_frozen = getattr(sys, 'frozen', False)
    logger = setup_logging(is_frozen)
    
    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(get_stylesheet())
        
        logger.info("Starting web server...")
        server_thread = run_server()
        if not server_thread:
            logger.error("Failed to start web server. Exiting.")
            return 1
        
        logger.info("Creating main window...")
        window = MuteStreamerOverload()
        window.show()
        
        app.aboutToQuit.connect(stop_server)
        
        logger.info("Starting application event loop...")
        return app.exec()
        
    except Exception as e:
        logger.exception("A fatal error occurred in the main application:")
        return 1

if __name__ == '__main__':
    check_runtime_dependencies()
    multiprocessing.freeze_support()
    # Only run the app in the main process
    if multiprocessing.current_process().name == 'MainProcess':
        try:
            from tts_service.tts_integration import speak
        except ImportError as e:
            print(f"TTS integration not available: {e}")
        else:
            if shutil.which('bun') is None:
                print("Error: 'bun' is not installed or not in PATH.")
                sys.exit(1)
            speak("Text To Speech is up and running, this is a test message.")
        exit_code = run_app()
        logging.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code) 