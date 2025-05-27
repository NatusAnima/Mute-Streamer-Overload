# Window sizes
MIN_OVERLAY_WIDTH = 300
MIN_OVERLAY_HEIGHT = 150
INITIAL_OVERLAY_WIDTH = 400
INITIAL_OVERLAY_HEIGHT = 200

# Styles
DARK_THEME = """
    QMainWindow {
        background-color: #2b2b2b;
    }
    QWidget {
        background-color: #2b2b2b;
        color: white;
    }
    QTextEdit {
        background-color: rgba(0, 0, 0, 100);
        color: white;
        border: 1px solid rgba(255, 255, 255, 50);
        border-radius: 5px;
    }
    QPushButton {
        background-color: rgba(0, 0, 0, 100);
        color: white;
        border: 1px solid rgba(255, 255, 255, 50);
        border-radius: 5px;
        padding: 5px 15px;
    }
    QPushButton:hover {
        background-color: rgba(255, 255, 255, 30);
    }
    QLabel {
        color: white;
    }
"""

SPINBOX_STYLE = """
    QSpinBox {
        background-color: rgba(0, 0, 0, 100);
        color: white;
        border: 1px solid rgba(255, 255, 255, 50);
        border-radius: 5px;
        padding: 5px;
        min-width: 80px;
    }
    QSpinBox::up-button, QSpinBox::down-button {
        background-color: rgba(255, 255, 255, 30);
        border: none;
        border-radius: 2px;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: rgba(255, 255, 255, 50);
    }
"""

TITLE_BAR_STYLE = """
    QWidget {
        background-color: rgba(0, 0, 0, 120);
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
    }
"""

CLOSE_BUTTON_STYLE = """
    QPushButton {
        color: white;
        background-color: transparent;
        border: none;
        font-size: 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: rgba(255, 0, 0, 100);
        border-radius: 10px;
    }
"""

MESSAGE_LABEL_STYLE = """
    QLabel {
        color: white;
        background-color: transparent;
    }
"""

CONTENT_WIDGET_STYLE = """
    QWidget {
        background-color: transparent;
        border-bottom-left-radius: 10px;
        border-bottom-right-radius: 10px;
    }
""" 