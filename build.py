import os
import sys
import shutil
import time
from cairosvg import svg2png
from PIL import Image
import PyInstaller.__main__
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_remove_directory(directory, max_retries=3, retry_delay=1):
    """Safely remove a directory with retries"""
    for attempt in range(max_retries):
        try:
            if os.path.exists(directory):
                shutil.rmtree(directory)
                logger.info(f"Successfully removed {directory}")
                return True
        except PermissionError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Permission denied when removing {directory}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to remove {directory} after {max_retries} attempts: {e}")
                return False
        except Exception as e:
            logger.error(f"Error removing {directory}: {e}")
            return False
    return True

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'mute_streamer_overload/web/templates/overlay.html',
        'assets/icon.svg'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error("Missing required files:")
        for file in missing_files:
            logger.error(f"  - {file}")
        return False
    return True

def convert_svg_to_ico():
    """Convert SVG icon to ICO format"""
    logger.info("Converting icon from SVG to ICO...")
    
    # Create assets directory if it doesn't exist
    os.makedirs('assets', exist_ok=True)
    
    # Convert SVG to PNG first
    png_path = 'assets/icon.png'
    svg_path = 'assets/icon.svg'
    
    if not os.path.exists(svg_path):
        logger.error(f"Icon SVG not found at {svg_path}")
        return None
        
    try:
        # Convert SVG to PNG
        svg2png(url=svg_path, write_to=png_path, output_width=256, output_height=256)
        
        # Convert PNG to ICO
        ico_path = 'assets/icon.ico'
        img = Image.open(png_path)
        
        # Create ICO with multiple sizes
        sizes = [(16,16), (32,32), (48,48), (64,64), (128,128), (256,256)]
        img.save(ico_path, format='ICO', sizes=sizes)
        
        # Clean up temporary PNG
        os.remove(png_path)
        
        logger.info("Icon conversion completed successfully!")
        return ico_path
    except Exception as e:
        logger.error(f"Error converting icon: {e}")
        return None

def build_exe():
    """Build the executable"""
    if not check_required_files():
        logger.error("Build aborted due to missing files")
        return False

    # Convert icon first
    icon_path = convert_svg_to_ico()
    
    # Clean previous build with retries
    logger.info("Cleaning previous build...")
    if not safe_remove_directory('dist'):
        logger.error("Failed to clean dist directory. Please ensure the executable is not running.")
        return False
    if not safe_remove_directory('build'):
        logger.error("Failed to clean build directory.")
        return False
    
    # Add templates and static files
    add_data = [
        '--add-data=mute_streamer_overload/web/templates;mute_streamer_overload/web/templates',
    ]
    
    # Add static files if they exist
    static_dir = 'mute_streamer_overload/web/static'
    if os.path.exists(static_dir):
        add_data.append('--add-data=mute_streamer_overload/web/static;mute_streamer_overload/web/static')
    
    # Define PyInstaller arguments
    args = [
        'main.py',
        '--name=MuteStreamerOverload',
        '--onefile',
        '--windowed',
        '--clean',
        '--noconfirm',
        *add_data,
        # Flask and dependencies
        '--hidden-import=flask',
        '--hidden-import=flask_socketio',
        '--hidden-import=engineio.async_drivers.threading',
        '--hidden-import=eventlet.hubs.epolls',
        '--hidden-import=eventlet.hubs.kqueue',
        '--hidden-import=eventlet.hubs.selects',
        '--hidden-import=dns',
        # Requests library for health checks
        '--hidden-import=requests',
        '--hidden-import=urllib3',
        '--hidden-import=idna',
        '--hidden-import=chardet',
        '--hidden-import=certifi',
        # Jinja2 and dependencies
        '--hidden-import=jinja2',
        '--hidden-import=jinja2.ext',
        '--hidden-import=jinja2.loaders',
        '--hidden-import=jinja2.environment',
        '--hidden-import=jinja2.utils',
        '--hidden-import=jinja2.filters',
        '--hidden-import=jinja2.runtime',
        '--hidden-import=jinja2.async_utils',
        '--hidden-import=jinja2.bccache',
        '--hidden-import=jinja2.debug',
        '--hidden-import=jinja2.exceptions',
        '--hidden-import=jinja2.nodes',
        '--hidden-import=jinja2.optimizer',
        '--hidden-import=jinja2.parser',
        '--hidden-import=jinja2.sandbox',
        '--hidden-import=jinja2.visitor',
        # Additional dependencies
        '--hidden-import=werkzeug',
        '--hidden-import=werkzeug.serving',
        '--hidden-import=werkzeug.middleware',
        '--hidden-import=werkzeug.debug',
        '--hidden-import=werkzeug.security',
        '--hidden-import=werkzeug.wsgi',
        '--hidden-import=werkzeug.http',
        '--hidden-import=werkzeug.datastructures',
        '--hidden-import=werkzeug.formparser',
        '--hidden-import=werkzeug.local',
        '--hidden-import=werkzeug.routing',
        '--hidden-import=werkzeug.test',
        '--hidden-import=werkzeug.urls',
        '--hidden-import=werkzeug.utils',
        '--hidden-import=werkzeug.wrappers',
        '--hidden-import=werkzeug.wrappers.json',
        '--hidden-import=werkzeug.wrappers.response',
        '--hidden-import=werkzeug.wrappers.request',
        '--hidden-import=werkzeug.wrappers.base_response',
        '--hidden-import=werkzeug.wrappers.base_request',
        '--hidden-import=werkzeug.wrappers.accept',
        '--hidden-import=werkzeug.wrappers.etag',
        '--hidden-import=werkzeug.wrappers.cors',
    ]
    
    # Add icon if conversion was successful
    if icon_path and os.path.exists(icon_path):
        args.append(f'--icon={icon_path}')
    
    # Add platform-specific options
    if sys.platform == 'win32':
        args.extend([
            '--uac-admin',  # Request admin privileges on Windows
        ])
    
    try:
        # Run PyInstaller
        logger.info("Starting PyInstaller build...")
        PyInstaller.__main__.run(args)
        logger.info("\nBuild completed! The executable can be found in the 'dist' directory.")
        logger.info("Note: You may need to run the executable as administrator on Windows.")
        return True
    except Exception as e:
        logger.error(f"Build failed: {e}")
        return False

if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1) 