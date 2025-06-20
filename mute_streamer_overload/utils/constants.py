# Window sizes
MIN_OVERLAY_WIDTH = 200
MIN_OVERLAY_HEIGHT = 100
INITIAL_OVERLAY_WIDTH = 400
INITIAL_OVERLAY_HEIGHT = 200

# Styles
DARK_THEME = """
    QMainWindow, QWidget {
        background-color: #2b2b2b;
        color: white;
    }
    QLabel {
        color: white;
    }
    QGroupBox {
        border: 1px solid #3f3f3f;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        color: white;
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
"""

MAIN_WINDOW_STYLE = """
    QMainWindow {
        background-color: #2b2b2b;
    }
    QGroupBox {
        border: 1px solid #3f3f3f;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
        background-color: #333333;
    }
    QGroupBox::title {
        color: white;
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
    QLabel {
        color: white;
    }
"""

INPUT_STYLE = """
    QTextEdit, QSpinBox {
        background-color: #3f3f3f;
        color: white;
        border: 1px solid #4f4f4f;
        border-radius: 3px;
        padding: 5px;
    }
    QTextEdit:focus, QSpinBox:focus {
        border: 1px solid #5f5f5f;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: #4f4f4f;
        border: none;
        border-radius: 2px;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #5f5f5f;
    }
"""

BUTTON_STYLE = """
    QPushButton {
        background-color: #4f4f4f;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 5px 15px;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #5f5f5f;
    }
    QPushButton:pressed {
        background-color: #3f3f3f;
    }
"""

OVERLAY_BUTTON_STYLE = """
    QPushButton {
        background-color: #2d5a88;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 5px 15px;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #3669a3;
    }
    QPushButton:pressed {
        background-color: #244b77;
    }
"""

GROUP_BOX_STYLE = """
    QGroupBox {
        background-color: #333333;
        border: 1px solid #3f3f3f;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        color: white;
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
"""

TITLE_BAR_STYLE = """
    QWidget {
        background-color: rgba(45, 45, 45, 120);
        border-top-left-radius: 5px;
        border-top-right-radius: 5px;
    }
"""

CLOSE_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: rgba(255, 0, 0, 100);
    }
    QPushButton:pressed {
        background-color: rgba(255, 0, 0, 150);
    }
"""

MESSAGE_LABEL_STYLE = """
    QLabel {
        color: white;
        font-size: 24px;
        font-weight: bold;
        background-color: transparent;
    }
"""

CONTENT_WIDGET_STYLE = """
    QWidget {
        background-color: transparent;
        border-bottom-left-radius: 5px;
        border-bottom-right-radius: 5px;
    }
"""

# Size control styles
SIZE_LABEL_STYLE = """
    QLabel {
        color: white;
        font-size: 12px;
        padding: 2px;
    }
"""

SIZE_CONTROL_STYLE = """
    QSpinBox {
        background-color: #2d2d2d;
        color: white;
        border: 1px solid #3d3d3d;
        border-radius: 4px;
        padding: 4px;
        min-width: 80px;
    }
    QSpinBox:hover {
        border: 1px solid #4d4d4d;
    }
    QSpinBox:focus {
        border: 1px solid #5d5d5d;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        width: 16px;
        border: none;
        background: #3d3d3d;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background: #4d4d4d;
    }
"""

SETTINGS_BUTTON_STYLE = """
    QPushButton {
        background-color: #4a4a4a;
        color: white;
        border: 1px solid #5a5a5a;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #5a5a5a;
        border: 1px solid #6a6a6a;
    }
    QPushButton:pressed {
        background-color: #3a3a3a;
    }
""" 