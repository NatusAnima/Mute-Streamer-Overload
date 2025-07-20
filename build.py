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

def safe_remove_directory_contents(path):
    """Safely remove all contents of a directory, but not the directory itself."""
    if not os.path.exists(path):
        logger.info(f"Directory '{path}' does not exist, skipping content removal.")
        return True
    for filename in os.listdir(path):
        file_path = os.path.join(path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete {file_path}. Reason: {e}")
    logger.info(f"Cleaned contents of directory: {path}")
    return True

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
    # Remove dist directory and tts_service/__pycache__, but only clean build/ contents
    for folder in ['dist', os.path.join('tts_service', '__pycache__')]:
        if os.path.exists(folder):
            print(f"Removing folder: {folder}")
            shutil.rmtree(folder)
    # Ensure build/ exists and clean its contents
    build_dir = 'build'
    if not os.path.exists(build_dir):
        os.makedirs(build_dir)
        logger.info(f"Created build directory: {build_dir}")
    else:
        safe_remove_directory_contents(build_dir)

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
    if not safe_remove_directory('dist'):
        logger.error("Build failed: Could not clean old dist directory.")
        return False
    # PyInstaller arguments for minimal launcher
    logger.info("Configuring PyInstaller for minimal launcher...")
    pyinstaller_args = ['MuteStreamerOverload.spec']
    logger.info("PyInstaller arguments configured.")
    logger.debug(f"Arguments: {' '.join(pyinstaller_args)}")
    # Run PyInstaller
    logger.info("Running PyInstaller build...")
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        logger.info("--- Build Completed Successfully! ---")
        exe_path = os.path.join('dist', 'MuteStreamerOverload', 'MuteStreamerOverload.exe')
        logger.info(f"Executable is located in: {exe_path}")
        return True
    except Exception as e:
        logger.error(f"An unexpected error occurred during the PyInstaller build: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    if build():
        sys.exit(0)
    else:
        sys.exit(1)
