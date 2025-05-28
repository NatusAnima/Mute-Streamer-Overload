# Mute Streamer Overload

A professional streaming overlay application that helps streamers manage their audio and visual elements.

## Project Structure

```
mute_streamer_overload/
├── core/                 # Core application logic
│   ├── __init__.py
│   ├── input_handler.py
│   └── text_animator.py
├── ui/                   # User interface components
│   ├── __init__.py
│   ├── main_window.py
│   └── overlay_window.py
├── web/                  # Web server and templates
│   ├── __init__.py
│   ├── web_server.py
│   └── templates/
│       └── overlay.html
├── utils/               # Utility functions and constants
│   ├── __init__.py
│   └── constants.py
├── docs/                # Documentation
│   ├── design_document.pdf
│   └── design_document.docx
├── tests/              # Test files (to be added)
│   └── __init__.py
├── main.py             # Application entry point
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

To start the application, run:
```bash
python main.py
```

## Features

- Customizable overlay window for streaming
- Web-based control interface
- Text animation system
- Input handling for keyboard shortcuts
- Professional UI with modern design

## License

[Add your license information here] 