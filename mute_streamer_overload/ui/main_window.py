import keyboard
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit,
                            QPushButton, QLabel, QHBoxLayout, QSpinBox, QApplication,
                            QGroupBox, QGridLayout)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut, QFont

from mute_streamer_overload.core.input_handler import InputHandler
from mute_streamer_overload.ui.overlay_window import OverlayWindow
from mute_streamer_overload.web.web_server import update_message, update_animation_settings, stop_server
from mute_streamer_overload.utils.constants import (DARK_THEME, MIN_OVERLAY_WIDTH, MIN_OVERLAY_HEIGHT,
                      INITIAL_OVERLAY_WIDTH, INITIAL_OVERLAY_HEIGHT, MAIN_WINDOW_STYLE,
                      INPUT_STYLE, BUTTON_STYLE, GROUP_BOX_STYLE, OVERLAY_BUTTON_STYLE,
                      SIZE_LABEL_STYLE, SIZE_CONTROL_STYLE)

class MuteStreamerOverload(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mute Streamer Overload")
        self.setMinimumSize(800, 600)
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        
        # Create title label
        title_label = QLabel("Mute Streamer Overload")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Create size control section
        size_group = QGroupBox("Size Control")
        size_layout = QHBoxLayout()
        
        # Width input
        width_layout = QVBoxLayout()
        width_label = QLabel("Width:")
        width_label.setStyleSheet(SIZE_LABEL_STYLE)
        self.width_input = QSpinBox()
        self.width_input.setStyleSheet(SIZE_CONTROL_STYLE)
        self.width_input.setRange(MIN_OVERLAY_WIDTH, 16777215)
        self.width_input.setValue(INITIAL_OVERLAY_WIDTH)
        self.width_input.setSuffix(" px")
        self.width_input.valueChanged.connect(self.update_overlay_size)
        width_layout.addWidget(width_label)
        width_layout.addWidget(self.width_input)
        
        # Height input
        height_layout = QVBoxLayout()
        height_label = QLabel("Height:")
        height_label.setStyleSheet(SIZE_LABEL_STYLE)
        self.height_input = QSpinBox()
        self.height_input.setStyleSheet(SIZE_CONTROL_STYLE)
        self.height_input.setRange(MIN_OVERLAY_HEIGHT, 16777215)
        self.height_input.setValue(INITIAL_OVERLAY_HEIGHT)
        self.height_input.setSuffix(" px")
        self.height_input.valueChanged.connect(self.update_overlay_size)
        height_layout.addWidget(height_label)
        height_layout.addWidget(self.height_input)
        
        size_layout.addLayout(width_layout)
        size_layout.addLayout(height_layout)
        size_group.setLayout(size_layout)
        size_group.setStyleSheet(GROUP_BOX_STYLE)
        layout.addWidget(size_group)
        
        # Create animation control section
        animation_group = QGroupBox("Animation Control")
        animation_layout = QGridLayout()
        
        # Character limits
        min_chars_label = QLabel("Min Characters:")
        min_chars_label.setStyleSheet("color: white;")
        self.min_chars_input = QSpinBox()
        self.min_chars_input.setRange(1, 1000)
        self.min_chars_input.setValue(10)
        self.min_chars_input.setStyleSheet(INPUT_STYLE)
        self.min_chars_input.valueChanged.connect(self.update_character_limits)
        
        max_chars_label = QLabel("Max Characters:")
        max_chars_label.setStyleSheet("color: white;")
        self.max_chars_input = QSpinBox()
        self.max_chars_input.setRange(1, 1000)
        self.max_chars_input.setValue(50)
        self.max_chars_input.setStyleSheet(INPUT_STYLE)
        self.max_chars_input.valueChanged.connect(self.update_character_limits)
        
        # WPM control
        wpm_label = QLabel("Words per Minute:")
        wpm_label.setStyleSheet("color: white;")
        self.wpm_input = QSpinBox()
        self.wpm_input.setRange(1, 1000)
        self.wpm_input.setValue(200)
        self.wpm_input.setStyleSheet(INPUT_STYLE)
        self.wpm_input.valueChanged.connect(self.update_wpm)
        
        # Add widgets to grid
        animation_layout.addWidget(min_chars_label, 0, 0)
        animation_layout.addWidget(self.min_chars_input, 0, 1)
        animation_layout.addWidget(max_chars_label, 1, 0)
        animation_layout.addWidget(self.max_chars_input, 1, 1)
        animation_layout.addWidget(wpm_label, 2, 0)
        animation_layout.addWidget(self.wpm_input, 2, 1)
        
        animation_group.setLayout(animation_layout)
        animation_group.setStyleSheet(GROUP_BOX_STYLE)
        layout.addWidget(animation_group)
        
        # Create message input section
        input_group = QGroupBox("Message Input")
        input_layout = QVBoxLayout()
        
        self.message_input = QTextEdit()
        self.message_input.setStyleSheet(INPUT_STYLE)
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(100)
        input_layout.addWidget(self.message_input)
        
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit (F4)")
        self.submit_button.setStyleSheet(BUTTON_STYLE)
        self.submit_button.clicked.connect(self.submit_message)
        button_layout.addWidget(self.submit_button)
        
        self.toggle_overlay_button = QPushButton("Show Overlay")
        self.toggle_overlay_button.setStyleSheet(OVERLAY_BUTTON_STYLE)
        self.toggle_overlay_button.clicked.connect(self.toggle_overlay)
        button_layout.addWidget(self.toggle_overlay_button)
        
        input_layout.addLayout(button_layout)
        input_group.setLayout(input_layout)
        input_group.setStyleSheet(GROUP_BOX_STYLE)
        layout.addWidget(input_group)
        
        # Create overlay window
        self.overlay_window = OverlayWindow()
        
        # Create input handler
        self.input_handler = InputHandler()
        self.input_handler.f4_pressed_signal.connect(self.handle_f4_toggle)
        
        # Set up F4 shortcut
        self.f4_shortcut = QShortcut(QKeySequence("F4"), self)
        self.f4_shortcut.activated.connect(self.submit_message)
        
        # Set up input handler
        self.input_handler.setParent(self)
        self.input_handler.text_updated.connect(self.update_text_display)
        self.input_handler.input_state_changed.connect(self.update_input_state)
        
        # Set up initial F4 hook
        keyboard.on_press_key("f4", self.input_handler.on_f4_press, suppress=True)
        
        # Set dark theme
        self.setStyleSheet(DARK_THEME)
        
        # Initialize message storage and input state
        self.current_message = ""
        self.overlay_visible = False
        
        # Add status label
        self.status_label = QLabel("Press F4 to start typing")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray; margin: 5px;")
        layout.addWidget(self.status_label)
        
    def update_character_limits(self):
        """Update the character limits for text animation"""
        min_chars = self.min_chars_input.value()
        max_chars = self.max_chars_input.value()
        
        # Ensure max is not less than min
        if max_chars < min_chars:
            self.max_chars_input.setValue(min_chars)
            max_chars = min_chars
            
        # Update both animators
        if self.overlay_window:
            self.overlay_window.text_animator.set_character_limits(min_chars, max_chars)
        update_animation_settings(min_chars=min_chars, max_chars=max_chars)
            
    def update_wpm(self):
        """Update the words per minute for text animation"""
        wpm = self.wpm_input.value()
        if self.overlay_window:
            self.overlay_window.text_animator.set_words_per_minute(wpm)
        update_animation_settings(wpm=wpm)
            
    def update_overlay_size(self):
        """Update the overlay window size"""
        if self.overlay_window:
            self.overlay_window.resize(self.width_input.value(), self.height_input.value())
            self.overlay_window.adjust_font_size()
    
    def toggle_overlay(self):
        """Toggle the overlay window visibility"""
        if self.overlay_visible:
            self.overlay_window.hide()
            self.toggle_overlay_button.setText("Show Overlay")
        else:
            self.overlay_window.show()
            self.toggle_overlay_button.setText("Hide Overlay")
            self.center_overlay()
            # Ensure the current message is displayed
            if self.current_message:
                self.overlay_window.set_message(self.current_message)
            # Set initial size from input fields
            self.update_overlay_size()
        self.overlay_visible = not self.overlay_visible
    
    def handle_f4_toggle(self):
        """Handle F4 toggle signal from input handler"""
        if not self.input_handler.is_active:
            # Only toggle input mode if we're not active
            self.input_handler.toggle_input()
            if self.input_handler.is_active:
                # Bring window to front
                self.activateWindow()
                self.raise_()
        else:
            # If we're active and have text, submit it
            current_text = self.input_handler.get_current_text()
            if current_text.strip():
                self.current_message = current_text
                print(f"Message stored: {self.current_message}")
                self.overlay_window.set_message(self.current_message)
                self.message_input.setText(self.current_message)
            
            # Reset input state
            self.input_handler.clear_text()
            self.input_handler.is_active = False
            self.input_handler.f4_pressed = False  # Reset F4 state
            self.input_handler.input_state_changed.emit(False)
            
            # Reset keyboard hooks
            keyboard.unhook_all()
            keyboard.on_press_key("f4", self.input_handler.on_f4_press, suppress=True)
    
    def update_text_display(self, text):
        """Update the text display with new input"""
        self.message_input.setText(text)
        
    def update_input_state(self, is_active):
        """Update the UI based on input state"""
        if is_active:
            self.status_label.setText("Type your message (Press F4 to submit)")
            self.status_label.setStyleSheet("color: green; margin: 5px;")
        else:
            self.status_label.setText("Press F4 to start typing")
            self.status_label.setStyleSheet("color: gray; margin: 5px;")
    
    def resizeEvent(self, event):
        """Handle window resize to recenter overlay"""
        super().resizeEvent(event)
        if self.overlay_visible:
            self.center_overlay()
    
    def center_overlay(self):
        """Center the overlay window on the screen"""
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.overlay_window.width()) // 2
        y = (screen_geometry.height() - self.overlay_window.height()) // 2
        self.overlay_window.move(x, y)
    
    def submit_message(self):
        """Submit the current message to the overlay"""
        message = self.message_input.toPlainText().strip()
        if message:
            # Update both the overlay window and web display
            self.current_message = message
            print(f"Message stored: {self.current_message}")
            self.overlay_window.set_message(self.current_message)
            self.message_input.clear()
            self.input_handler.clear_text()
            update_message(self.current_message)
    
    def handle_character_input(self, char):
        """Handle character input from the input handler"""
        if self.message_input.hasFocus():
            current_text = self.message_input.toPlainText()
            cursor = self.message_input.textCursor()
            cursor.insertText(char)
    
    def closeEvent(self, event):
        """Clean up when the application is closed"""
        try:
            # Stop keyboard hooks
            keyboard.unhook_all()
            
            # Stop input handler
            if hasattr(self, 'input_handler'):
                self.input_handler.timer.stop()
                self.input_handler.is_active = False
            
            # Close the overlay window
            if hasattr(self, 'overlay_window'):
                self.overlay_window.close()
            
            # Stop the web server
            stop_server()
            
            # Accept the close event
            event.accept()
            
            # Force quit the application
            QApplication.quit()
        except Exception as e:
            print(f"Error during shutdown: {e}")
            # Force quit even if there's an error
            QApplication.quit() 