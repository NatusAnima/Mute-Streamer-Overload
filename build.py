import os
import sys
import shutil
import time
import logging
import PyInstaller.__main__
import PyQt6
import subprocess

# --- Configuration ---

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def safe_remove_directory(path):
    """Safely remove a directory with retries to handle file locks."""
    for attempt in range(3):
        if not os.path.exists(path):
            logger.info(f"Directory '{path}' does not exist, skipping removal.")
            return True
        try:
            shutil.rmtree(path)
            logger.info(f"Successfully removed directory: {path}")
            return True
        except OSError as e:
            logger.warning(f"Error removing '{path}' on attempt {attempt + 1}: {e}. Retrying...")
            time.sleep(1)
    logger.error(f"Failed to remove directory '{path}' after multiple attempts.")
    return False

def get_data_files():
    """Get all data files that need to be bundled with the executable."""
    data_files = []
    
    # Helper to create platform-independent data tuples
    def add_data_tuple(source, destination):
        return (os.path.join(*source.split('/')), os.path.join(*destination.split('/')))

    # Add web templates and static files
    data_files.append(add_data_tuple('mute_streamer_overload/web/templates', 'mute_streamer_overload/web/templates'))
    static_dir = 'mute_streamer_overload/web/static'
    if os.path.exists(static_dir):
        data_files.append(add_data_tuple(static_dir, static_dir))

    # Add PyQt6 plugins (crucial for styles, platform support, etc.)
    pyqt_plugins_path = os.path.join(os.path.dirname(PyQt6.__file__), "Qt6", "plugins")
    if os.path.exists(pyqt_plugins_path):
        data_files.append((pyqt_plugins_path, 'PyQt6/Qt6/plugins'))
    else:
        logger.warning(f"PyQt6 plugins directory not found at: {pyqt_plugins_path}")
        
    # Add assets directory
    if os.path.exists('assets'):
        data_files.append(('assets', 'assets'))
    
    # Add TTS service directory
    if os.path.exists('tts_service'):
        data_files.append(('tts_service', 'tts_service'))

    return [f"--add-data={src}{os.pathsep}{dest}" for src, dest in data_files]

def get_hidden_imports():
    """Get all hidden imports that PyInstaller might miss."""
    imports = [
        # PyQt6 essentials
        'PyQt6', 'PyQt6.sip', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtSvg',
        # Flask & Web Server
        'flask', 'flask_socketio', 'engineio.async_drivers.threading', 'werkzeug', 'jinja2',
        # Common dependencies
        'requests', 'keyboard', 'pygame',
        # Required for freeze_support
        'multiprocessing',
        # TTS Service
        'tts_service', 'tts_service.tts_integration',
        # Additional PyQt6 modules
        'PyQt6.QtNetwork', 'PyQt6.QtMultimedia'
    ]
    return [f"--hidden-import={imp}" for imp in imports]

# --- Main Build Function ---

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required.")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def check_required_files():
    """Check if all required files exist."""
    required_files = [
        'main.py',
        'mute_streamer_overload/requirements.txt',
        'assets/icon_256x256.ico',
        'mute_streamer_overload/web/templates/overlay.html',
        'mute_streamer_overload/web/static'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    logger.info("All required files found.")
    return True

def build():
    """Orchestrate the entire build process."""
    logger.info("--- Starting Mute Streamer Overload Build ---")
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check required files
    if not check_required_files():
        return False

    # 0. Ensure all dependencies are installed
    logger.info("Step 0: Installing Python dependencies from requirements.txt...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', os.path.join('mute_streamer_overload', 'requirements.txt')])
        logger.info("All dependencies installed successfully.")
    except Exception as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

    # 1. Clean previous build artifacts
    logger.info("Step 1: Cleaning previous build directories...")
    if not safe_remove_directory('dist') or not safe_remove_directory('build'):
        logger.error("Build failed: Could not clean old build directories.")
        return False
    
    # 2. Define PyInstaller arguments
    logger.info("Step 2: Configuring PyInstaller...")
    
    # Start with console mode for debugging. Change to '--windowed' for release.
    mode = '--windowed'
    
    pyinstaller_args = [
        'main.py',
        '--name=MuteStreamerOverload',
        '--onefile',
        mode,
        '--clean',
        '--noconfirm',
        '--collect-all=pygame',
        '--collect-all=flask',
        '--collect-all=flask_socketio',
        f'--icon={os.path.join("assets", "icon_256x256.ico")}'
    ]
    
    pyinstaller_args.extend(get_data_files())
    pyinstaller_args.extend(get_hidden_imports())
    
    if sys.platform == 'win32':
        pyinstaller_args.append('--uac-admin')

    logger.info("PyInstaller arguments configured.")
    logger.debug(f"Arguments: {' '.join(pyinstaller_args)}")

    # 3. Run PyInstaller
    logger.info("Step 3: Running PyInstaller build...")
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        logger.info("--- Build Completed Successfully! ---")
        logger.info(f"Executable is located in: {os.path.join(os.getcwd(), 'dist')}")
        return True
    except Exception as e:
        logger.error(f"An unexpected error occurred during the PyInstaller build: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    if build():
        sys.exit(0)
    else:
        sys.exit(1)
