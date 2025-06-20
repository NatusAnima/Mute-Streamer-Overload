def get_stylesheet():
    """
    Returns the complete, consolidated stylesheet for the entire application.
    This approach is recommended for consistency and easier maintenance.
    """
    return """
        /* --- Global --- */
        QMainWindow, QWidget {
            background-color: #2b2b2b;
            color: #e0e0e0;
            font-family: "Segoe UI", "Helvetica", "Arial", sans-serif;
        }

        /* --- GroupBox --- */
        QGroupBox {
            background-color: #333333;
            border: 1px solid #3f3f3f;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            color: #e0e0e0;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }

        /* --- Labels --- */
        QLabel {
            color: #e0e0e0;
            font-size: 12px;
        }
        #TitleLabel {
            font-size: 24px;
            font-weight: bold;
            margin: 10px;
        }

        /* --- Buttons --- */
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
        #OverlayButton {
            background-color: #2d5a88;
        }
        #OverlayButton:hover {
            background-color: #3669a3;
        }
        #OverlayButton:pressed {
            background-color: #244b77;
        }

        /* --- Input Fields --- */
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
        QSpinBox {
            min-width: 80px;
        }
        QSpinBox::up-button, QSpinBox::down-button {
            width: 16px;
            border: none;
            background: #3d3d3d;
        }
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {
            background: #4d4d4d;
        }

        /* --- Dynamic Status Label --- */
        #StatusLabel[active="true"] {
            color: #4CAF50; /* Green */
            font-weight: bold;
        }
        #StatusLabel[active="false"] {
            color: #9E9E9E; /* Gray */
        }
    """ 