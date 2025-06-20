import keyboard
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit,
                            QPushButton, QLabel, QHBoxLayout, QSpinBox, QApplication,
                            QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from pathlib import Path

from mute_streamer_overload.core.input_handler import InputHandler
from mute_streamer_overload.ui.overlay_window import OverlayWindow
from mute_streamer_overload.web.web_server import update_message, update_animation_settings, stop_server
from mute_streamer_overload.utils.constants import (MIN_OVERLAY_WIDTH, MIN_OVERLAY_HEIGHT,
                                                  INITIAL_OVERLAY_WIDTH, INITIAL_OVERLAY_HEIGHT)

logger = logging.getLogger(__name__)

class MuteStreamerOverload(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.debug("Initializing main window...")
        
        self.setWindowTitle("Mute Streamer Overload")
        self.setMinimumSize(800, 600)
        self.center_window()
        self.setup_icon()
        self.setup_ui()
        self.setup_logic()

    def setup_icon(self):
        """Find and set the window icon."""
        try:
            assets_dir = Path(__file__).resolve().parent.parent.parent / 'assets'
            icon_path = assets_dir / 'icon_32x32.ico'
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
            else:
                logger.warning(f"Icon not found at '{icon_path}', using default.")
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}", exc_info=True)

    def setup_ui(self):
        """Create and arrange all UI widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # --- Title ---
        title_label = QLabel("Mute Streamer Overload")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("TitleLabel")
        main_layout.addWidget(title_label)

        # --- Size Control ---
        size_group = self.create_size_controls()
        main_layout.addWidget(size_group)

        # --- Animation Control ---
        animation_group = self.create_animation_controls()
        main_layout.addWidget(animation_group)
        
        # --- Message Input ---
        input_group = self.create_message_controls()
        main_layout.addWidget(input_group)
        
        # --- Status Label ---
        self.status_label = QLabel("Press F4 to start typing")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("StatusLabel")
        main_layout.addWidget(self.status_label)
        
    def create_size_controls(self):
        """Create the 'Size Control' group box."""
        group = QGroupBox("Size Control")
        layout = QHBoxLayout(group)
        
        self.width_input = QSpinBox()
        self.width_input.setRange(MIN_OVERLAY_WIDTH, 16777215)
        self.width_input.setValue(INITIAL_OVERLAY_WIDTH)
        self.width_input.setSuffix(" px")
        self.width_input.valueChanged.connect(self.update_overlay_size)
        layout.addWidget(QLabel("Width:"))
        layout.addWidget(self.width_input)
        
        self.height_input = QSpinBox()
        self.height_input.setRange(MIN_OVERLAY_HEIGHT, 16777215)
        self.height_input.setValue(INITIAL_OVERLAY_HEIGHT)
        self.height_input.setSuffix(" px")
        self.height_input.valueChanged.connect(self.update_overlay_size)
        layout.addWidget(QLabel("Height:"))
        layout.addWidget(self.height_input)
        
        return group

    def create_animation_controls(self):
        """Create the 'Animation Control' group box."""
        group = QGroupBox("Animation Control")
        layout = QGridLayout(group)
        
        self.min_chars_input = QSpinBox()
        self.min_chars_input.setRange(1, 1000)
        self.min_chars_input.setValue(10)
        self.min_chars_input.valueChanged.connect(self.update_character_limits)
        layout.addWidget(QLabel("Min Characters:"), 0, 0)
        layout.addWidget(self.min_chars_input, 0, 1)
        
        self.max_chars_input = QSpinBox()
        self.max_chars_input.setRange(1, 1000)
        self.max_chars_input.setValue(50)
        self.max_chars_input.valueChanged.connect(self.update_character_limits)
        layout.addWidget(QLabel("Max Characters:"), 1, 0)
        layout.addWidget(self.max_chars_input, 1, 1)
        
        self.wpm_input = QSpinBox()
        self.wpm_input.setRange(1, 1000)
        self.wpm_input.setValue(200)
        self.wpm_input.valueChanged.connect(self.update_wpm)
        layout.addWidget(QLabel("Words per Minute:"), 2, 0)
        layout.addWidget(self.wpm_input, 2, 1)
        
        return group

    def create_message_controls(self):
        """Create the 'Message Input' group box."""
        group = QGroupBox("Message Input")
        layout = QVBoxLayout(group)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(100)
        layout.addWidget(self.message_input)
        
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit (F4)")
        self.submit_button.clicked.connect(self.submit_message)
        button_layout.addWidget(self.submit_button)
        
        self.toggle_overlay_button = QPushButton("Show Overlay")
        self.toggle_overlay_button.setObjectName("OverlayButton")
        self.toggle_overlay_button.clicked.connect(self.toggle_overlay)
        button_layout.addWidget(self.toggle_overlay_button)
        layout.addLayout(button_layout)
        
        return group

    def setup_logic(self):
        """Set up application logic, state, and event connections."""
        self.overlay_window = OverlayWindow()
        self.input_handler = InputHandler()
        self.current_message = ""
        self.overlay_visible = False
        
        self.input_handler.f4_pressed_signal.connect(self.handle_f4_toggle)
        self.input_handler.text_updated.connect(self.update_text_display)
        self.input_handler.input_state_changed.connect(self.update_input_state)
        
        self.f4_shortcut = QShortcut(QKeySequence("F4"), self)
        self.f4_shortcut.activated.connect(self.submit_message)
        
        keyboard.on_press_key("f4", self.input_handler.on_f4_press, suppress=True)
        self.update_input_state(False)

    def update_character_limits(self):
        min_chars = self.min_chars_input.value()
        max_chars = self.max_chars_input.value()
        if max_chars < min_chars:
            self.max_chars_input.setValue(min_chars)
            max_chars = min_chars
        if self.overlay_window:
            self.overlay_window.text_animator.set_character_limits(min_chars, max_chars)
        update_animation_settings(min_chars=min_chars, max_chars=max_chars)
            
    def update_wpm(self):
        wpm = self.wpm_input.value()
        if self.overlay_window:
            self.overlay_window.text_animator.set_words_per_minute(wpm)
        update_animation_settings(wpm=wpm)
            
    def update_overlay_size(self):
        if self.overlay_window:
            self.overlay_window.resize(self.width_input.value(), self.height_input.value())
            self.overlay_window.adjust_font_size()
    
    def toggle_overlay(self):
        if self.overlay_visible:
            self.overlay_window.hide()
            self.toggle_overlay_button.setText("Show Overlay")
        else:
            self.overlay_window.show()
            self.toggle_overlay_button.setText("Hide Overlay")
            self.center_overlay()
            if self.current_message:
                self.overlay_window.set_message(self.current_message)
            self.update_overlay_size()
        self.overlay_visible = not self.overlay_visible
    
    def handle_f4_toggle(self):
        if not self.input_handler.is_active:
            self.input_handler.toggle_input()
            if self.input_handler.is_active:
                self.activateWindow()
                self.raise_()
        else:
            current_text = self.input_handler.get_current_text()
            if current_text.strip():
                self.current_message = current_text
                self.overlay_window.set_message(self.current_message)
                self.message_input.setText(self.current_message)
            
            self.input_handler.clear_text()
            self.input_handler.is_active = False
            self.input_handler.f4_pressed = False
            self.input_handler.input_state_changed.emit(False)
            
            keyboard.unhook_all()
            keyboard.on_press_key("f4", self.input_handler.on_f4_press, suppress=True)
    
    def update_text_display(self, text):
        self.message_input.setText(text)
        
    def update_input_state(self, is_active):
        if is_active:
            self.status_label.setText("Type your message (Press F4 to submit)")
            self.status_label.setProperty("active", True)
        else:
            self.status_label.setText("Press F4 to start typing")
            self.status_label.setProperty("active", False)
        
        style = self.status_label.style()
        if style:
            style.unpolish(self.status_label)
            style.polish(self.status_label)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'overlay_visible') and self.overlay_visible:
            self.center_overlay()
    
    def center_overlay(self):
        screen = QApplication.primaryScreen()
        if not screen or not hasattr(self, 'overlay_window'):
            return
        screen_geometry = screen.geometry()
        x = (screen_geometry.width() - self.overlay_window.width()) // 2
        y = (screen_geometry.height() - self.overlay_window.height()) // 2
        self.overlay_window.move(x, y)
    
    def submit_message(self):
        message = self.message_input.toPlainText().strip()
        if message:
            self.current_message = message
            self.overlay_window.set_message(self.current_message)
            self.message_input.clear()
            self.input_handler.clear_text()
            update_message(self.current_message)
    
    def closeEvent(self, event):
        keyboard.unhook_all()
        if hasattr(self, 'input_handler'):
            self.input_handler.timer.stop()
        if hasattr(self, 'overlay_window'):
            self.overlay_window.close()
        stop_server()
        event.accept()
    
    def center_window(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        screen_geometry = screen.geometry()
        size = self.geometry()
        x = (screen_geometry.width() - size.width()) // 2
        y = (screen_geometry.height() - size.height()) // 2
        self.move(x, y)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_() 