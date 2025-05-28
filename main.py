import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from mute_streamer_overload.ui.main_window import MuteStreamerOverload
from mute_streamer_overload.web.web_server import run_server, stop_server

def main():
    app = QApplication(sys.argv)
    
    # Start the web server
    server_thread = run_server()
    if not server_thread:
        sys.exit(1)
    
    # Create and show the main window
    window = MuteStreamerOverload()
    window.show()
    
    # Set up application shutdown
    def cleanup():
        # The window's closeEvent will handle server shutdown
        # We just need to ensure the application quits
        app.quit()
    
    # Connect the aboutToQuit signal to our cleanup function
    app.aboutToQuit.connect(cleanup)
    
    # Start the application event loop
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 