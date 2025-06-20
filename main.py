import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

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

def main():
    """Application entry point."""
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
    exit_code = main()
    logging.info(f"Application exited with code: {exit_code}")
    sys.exit(exit_code) 