import os
import sys
import subprocess
import shutil
import logging
import PyInstaller.__main__

# --- Configuration ---

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
            import time
            time.sleep(1)
    logger.error(f"Failed to remove directory '{path}' after multiple attempts.")
    return False

# --- Pre-Build Clean Step ---

def pre_build_cleanup():
    # Remove build and dist directories
    for folder in ['build', 'dist', os.path.join('tts_service', '__pycache__')]:
        if os.path.exists(folder):
            print(f"Removing folder: {folder}")
            shutil.rmtree(folder)

pre_build_cleanup()

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
    """Build a minimal launcher exe for Mute Streamer Overload."""
    logger.info("--- Starting Mute Streamer Overload Build (Minimal Launcher) ---")
    if not check_python_version():
        return False
    if not check_required_files():
        return False
    # Clean previous build artifacts
    logger.info("Cleaning previous build directories...")
    if not safe_remove_directory('dist') or not safe_remove_directory('build'):
        logger.error("Build failed: Could not clean old build directories.")
        return False
    # PyInstaller arguments for minimal launcher
    logger.info("Configuring PyInstaller for minimal launcher...")
    pyinstaller_args = [
        'main.py',
        '--name=MuteStreamerOverload',
        '--windowed',
        '--noconfirm',
        f'--icon={os.path.join("assets", "icon_256x256.ico")}',
    ]
    logger.info("PyInstaller arguments configured.")
    logger.debug(f"Arguments: {' '.join(pyinstaller_args)}")
    # Run PyInstaller
    logger.info("Running PyInstaller build...")
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
