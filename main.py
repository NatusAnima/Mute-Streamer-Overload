import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
import multiprocessing
import shutil
import webbrowser
import os
import subprocess
from PyQt6.QtWidgets import QProgressDialog
import requests, zipfile, io, os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("sys.path:", sys.path)
try:
    print("threading module:", __import__('threading'))
    print("queue module:", __import__('queue'))
except Exception as e:
    print("Error importing threading/queue:", e)

try:
    import pkg_resources
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'setuptools'])
    import pkg_resources

# --- Add: Set up bin path for bundled Node.js and ffmpeg ---
def prepend_bin_to_path():
    bin_dir = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', 'bin')
    if os.path.exists(bin_dir):
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')
        return bin_dir
    return None

prepend_bin_to_path()

# --- Dependency Auto-Installer ---
def ensure_python_dependencies():
    if getattr(sys, 'frozen', False):
        # Do not attempt to install packages in a frozen app
        return
    setup_marker = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', '.setup_complete')
    python_marker = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', '.python_deps_installed')
    if os.path.exists(setup_marker) or os.path.exists(python_marker):
        return
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
        except pkg_resources.DistributionNotFound:
            to_install.append(req)
    if to_install:
        print(f"Installing missing Python packages: {to_install}")
        print(f"Using Python executable: {sys.executable}")
        import subprocess
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *to_install])
        except Exception as e:
            print(f"Failed to install Python packages: {e}")
            sys.exit(1)
    # If we get here, all dependencies are installed
    with open(python_marker, 'w') as f:
        f.write('python deps installed')


def download_and_extract(url, extract_to, exe_name):
    print(f"Downloading {exe_name} (this may take a moment)...")
    try:
        r = requests.get(url)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        for f in z.namelist():
            if f.endswith(exe_name):
                z.extract(f, extract_to)
                # Move to bin root if needed
                src = os.path.join(extract_to, f)
                dst = os.path.join(extract_to, exe_name)
                os.rename(src, dst)
                break
        print(f"{exe_name} downloaded and ready.")
    except Exception as e:
        print(f"Failed to download {exe_name}: {e}")

# --- Add: Download bun.exe if missing ---
def download_bun(bin_dir):
    bun_path = os.path.join(bin_dir, 'bun.exe')
    if not os.path.exists(bun_path):
        print("Downloading bun.exe (this may take a moment)...")
        try:
            # Official bun Windows release (update version as needed)
            bun_url = "https://github.com/oven-sh/bun/releases/download/bun-v1.2.18/bun-windows-x64.zip"
            r = requests.get(bun_url)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            for f in z.namelist():
                if f.endswith('bun.exe'):
                    z.extract(f, bin_dir)
                    src = os.path.join(bin_dir, f)
                    dst = os.path.join(bin_dir, 'bun.exe')
                    os.rename(src, dst)
                    break
            print("bun.exe downloaded and ready.")
        except Exception as e:
            print(f"Failed to download bun.exe: {e}")

def ensure_node_modules():
    """Ensure tts_service/node_modules exists, otherwise run bun install or npm install using bundled binaries if available. This will be run automatically before any TTS subprocess is started."""
    setup_marker = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', '.setup_complete')
    if os.path.exists(setup_marker):
        return
    if getattr(sys, 'frozen', False):
        tts_dir = os.path.join(os.path.dirname(sys.executable), 'tts_service')
    else:
        tts_dir = os.path.join(os.path.dirname(__file__), 'tts_service')
    node_modules = os.path.join(tts_dir, 'node_modules')
    package_json = os.path.join(tts_dir, 'package.json')
    if not os.path.exists(package_json):
        print(f"No package.json found in {tts_dir}, skipping Node.js dependency check.")
        return
    if not os.path.exists(node_modules) or not os.listdir(node_modules):
        print("[AUTO] Installing Node.js dependencies for tts_service using bun install...")
        bin_dir = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', 'bin')
        bun_path = shutil.which('bun', path=bin_dir + os.pathsep + os.environ.get('PATH', ''))
        if not bun_path:
            bun_path = shutil.which('bun')
        if bun_path:
            cmd = [bun_path, 'install']
        else:
            npm_path = shutil.which('npm', path=bin_dir + os.pathsep + os.environ.get('PATH', ''))
            if not npm_path:
                npm_path = shutil.which('npm')
            if not npm_path:
                print("Neither 'bun' nor 'npm' is installed or bundled. Please install one to continue.")
                sys.exit(1)
            cmd = [npm_path, 'install']
        subprocess.check_call(cmd, cwd=tts_dir)
    # Ensure node_modules is present after install
    if not os.path.exists(node_modules) or not os.listdir(node_modules):
        print("Failed to install node_modules. Please check your internet connection and try again.")
        sys.exit(1)

# --- Add: Simple progress dialog for setup ---
def show_progress_dialog(message):
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = QProgressDialog(message, None, 0, 0)
    dlg.setWindowTitle("Mute Streamer Overload Setup")
    dlg.setCancelButton(None)
    dlg.setMinimumDuration(0)
    dlg.setValue(0)
    dlg.show()
    app.processEvents()
    return dlg

def is_frozen():
    return getattr(sys, 'frozen', False)

def ensure_binaries():
    setup_marker = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', '.setup_complete')
    if os.path.exists(setup_marker):
        return
    bin_dir = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    node_path = os.path.join(bin_dir, 'node.exe')
    ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
    bun_path = os.path.join(bin_dir, 'bun.exe')
    if not shutil.which('node') and not os.path.exists(node_path):
        print("Node.js (node.exe) is required and will be downloaded automatically.")
        download_and_extract(
            "https://nodejs.org/dist/v24.4.0/node-v24.4.0-win-x64.zip",
            bin_dir, "node.exe"
        )
    if not shutil.which('ffmpeg') and not os.path.exists(ffmpeg_path):
        print("FFmpeg (ffmpeg.exe) is required and will be downloaded automatically.")
        download_and_extract(
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            bin_dir, "ffmpeg.exe"
        )
    if not shutil.which('bun') and not os.path.exists(bun_path):
        print("Bun (bun.exe) is required and will be downloaded automatically.")
        download_bun(bin_dir)

# --- Call dependency checks before anything else ---
def run_dependency_setup():
    """Run all dependency checks and show progress dialog if needed."""
    need_setup = False
    req_path = os.path.join('mute_streamer_overload', 'requirements.txt')
    tts_dir = os.path.join(os.path.dirname(__file__), 'tts_service')
    node_modules = os.path.join(tts_dir, 'node_modules')
    if not os.path.exists(req_path) or not os.path.exists(node_modules) or not os.listdir(node_modules):
        need_setup = True
    dlg = None
    if need_setup:
        dlg = show_progress_dialog("Setting up dependencies, please wait...")
    ensure_binaries()
    ensure_python_dependencies()
    ensure_node_modules()
    if dlg:
        dlg.close()

def run_dependency_setup_with_dialog(app):
    setup_marker = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', '.setup_complete')
    if os.path.exists(setup_marker):
        return  # Setup already done

    dlg = QProgressDialog("Checking dependencies...", None, 0, 0)
    dlg.setWindowTitle("Mute Streamer Overload Setup")
    dlg.setCancelButton(None)
    dlg.setMinimumDuration(0)
    dlg.setValue(0)
    dlg.show()
    app.processEvents()

    def update_status(msg):
        dlg.setLabelText(msg)
        app.processEvents()

    # Download node.exe if not present in PATH or bin
    bin_dir = os.path.join(os.path.dirname(__file__), 'mute_streamer_overload', 'bin')
    os.makedirs(bin_dir, exist_ok=True)
    node_path = os.path.join(bin_dir, 'node.exe')
    if not shutil.which('node') and not os.path.exists(node_path):
        update_status("Downloading Node.js (node.exe)...")
        download_and_extract(
            "https://nodejs.org/dist/v24.4.0/node-v24.4.0-win-x64.zip",
            bin_dir, "node.exe"
        )

    # Download ffmpeg.exe if not present in PATH or bin
    ffmpeg_path = os.path.join(bin_dir, 'ffmpeg.exe')
    if not shutil.which('ffmpeg') and not os.path.exists(ffmpeg_path):
        update_status("Downloading FFmpeg (ffmpeg.exe)...")
        download_and_extract(
            "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip",
            bin_dir, "ffmpeg.exe"
        )

    # Download bun.exe if not present in PATH or bin
    bun_path = os.path.join(bin_dir, 'bun.exe')
    if not shutil.which('bun') and not os.path.exists(bun_path):
        update_status("Downloading Bun (bun.exe)...")
        download_bun(bin_dir)

    # Install Python dependencies (only in dev mode)
    if not getattr(sys, 'frozen', False):
        update_status("Checking Python dependencies...")
        ensure_python_dependencies()

    # Install Node.js dependencies
    update_status("Installing Node.js dependencies for TTS...")
    ensure_node_modules()

    dlg.close()
    # Mark setup as complete
    with open(setup_marker, 'w') as f:
        f.write('setup complete')

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
        print("[DEBUG] Attempting to start web server...")
        run_server()  # Just call it, don't check return value
        print("[DEBUG] Web server thread started successfully.")

        logger.info("Creating main window...")
        print("[DEBUG] Creating main window...")
        window = MuteStreamerOverload()
        window.show()

        app.aboutToQuit.connect(stop_server)

        logger.info("Starting application event loop...")
        print("[DEBUG] Entering application event loop...")
        return app.exec()

    except Exception as e:
        logger.exception("A fatal error occurred in the main application:")
        print(f"[DEBUG] Exception in run_app: {e}")
        return 1

if __name__ == '__main__':
    multiprocessing.freeze_support()
    if multiprocessing.current_process().name == 'MainProcess':
        app = QApplication(sys.argv)
        run_dependency_setup_with_dialog(app)
        check_runtime_dependencies()
        exit_code = run_app()  # This starts the web server and main window
        # Optionally, you can run a TTS test here after the app is running, or trigger from the UI
        # from tts_service.tts_integration import speak
        # speak("Text To Speech is up and running, this is a test message.")
        logging.info(f"Application exited with code: {exit_code}")
        sys.exit(exit_code) 