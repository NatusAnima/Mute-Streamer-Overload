import keyboard
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit,
                            QPushButton, QLabel, QHBoxLayout, QSpinBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QApplication

from input_handler import InputHandler
from overlay_window import OverlayWindow
from constants import (DARK_THEME, SPINBOX_STYLE, MIN_OVERLAY_WIDTH, MIN_OVERLAY_HEIGHT,
                      INITIAL_OVERLAY_WIDTH, INITIAL_OVERLAY_HEIGHT)

class MuteStreamerOverload(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mute Streamer Overload")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create title label
        title_label = QLabel("Mute Streamer Overload")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # Create text input box
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here... (Press F4 to toggle input)")
        self.text_input.setMinimumHeight(200)
        self.text_input.setReadOnly(True)
        layout.addWidget(self.text_input)
        
        # Create size control section
        size_group = QWidget()
        size_layout = QHBoxLayout(size_group)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        # Width control
        width_label = QLabel("Width:")
        width_label.setStyleSheet("color: white;")
        size_layout.addWidget(width_label)
        
        self.width_input = QSpinBox()
        self.width_input.setRange(MIN_OVERLAY_WIDTH, 16777215)
        self.width_input.setValue(INITIAL_OVERLAY_WIDTH)
        self.width_input.setStyleSheet(SPINBOX_STYLE)
        self.width_input.valueChanged.connect(self.update_overlay_size)
        size_layout.addWidget(self.width_input)
        
        # Add px label after width input
        width_px_label = QLabel("px")
        width_px_label.setStyleSheet("color: white;")
        size_layout.addWidget(width_px_label)
        
        # Add some spacing
        size_layout.addSpacing(20)
        
        # Height control
        height_label = QLabel("Height:")
        height_label.setStyleSheet("color: white;")
        size_layout.addWidget(height_label)
        
        self.height_input = QSpinBox()
        self.height_input.setRange(MIN_OVERLAY_HEIGHT, 16777215)
        self.height_input.setValue(INITIAL_OVERLAY_HEIGHT)
        self.height_input.setStyleSheet(SPINBOX_STYLE)
        self.height_input.valueChanged.connect(self.update_overlay_size)
        size_layout.addWidget(self.height_input)
        
        # Add px label after height input
        height_px_label = QLabel("px")
        height_px_label.setStyleSheet("color: white;")
        size_layout.addWidget(height_px_label)
        
        size_layout.addStretch()
        layout.addWidget(size_group)
        
        # Create button layout
        button_layout = QHBoxLayout()
        
        # Create submit button
        submit_button = QPushButton("Submit (F4)")
        submit_button.clicked.connect(self.handle_submit)
        button_layout.addWidget(submit_button)
        
        # Create overlay toggle button
        self.overlay_button = QPushButton("Toggle Overlay")
        self.overlay_button.clicked.connect(self.toggle_overlay)
        button_layout.addWidget(self.overlay_button)
        
        layout.addLayout(button_layout)
        
        # Initialize message storage and input state
        self.current_message = ""
        
        # Create overlay window
        self.overlay = OverlayWindow()
        self.overlay_visible = False
        
        # Add status label
        self.status_label = QLabel("Press F4 to start typing")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: gray; margin: 5px;")
        layout.addWidget(self.status_label)
        
        # Set up input handler
        self.input_handler = InputHandler()
        self.input_handler.setParent(self)
        self.input_handler.text_updated.connect(self.update_text_display)
        self.input_handler.input_state_changed.connect(self.update_input_state)
        self.input_handler.f4_pressed_signal.connect(self.handle_f4_toggle)
        
        # Set up initial F4 hook
        keyboard.on_press_key("f4", self.input_handler.on_f4_press, suppress=True)
        
        # Set dark theme
        self.setStyleSheet(DARK_THEME)
    
    def update_overlay_size(self):
        """Update overlay window size based on input values"""
        if self.overlay_visible:
            self.overlay.resize(self.width_input.value(), self.height_input.value())
            self.overlay.adjust_font_size()
    
    def toggle_overlay(self):
        """Toggle the overlay window visibility"""
        if self.overlay_visible:
            self.overlay.hide()
            self.overlay_button.setText("Show Overlay")
        else:
            self.overlay.show()
            self.overlay_button.setText("Hide Overlay")
            self.center_overlay()
            # Ensure the current message is displayed
            if self.current_message:
                self.overlay.set_message(self.current_message)
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
                self.overlay.set_message(self.current_message)
                self.text_input.setText(self.current_message)
            
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
        self.text_input.setText(text)
        
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
        x = (screen_geometry.width() - self.overlay.width()) // 2
        y = (screen_geometry.height() - self.overlay.height()) // 2
        self.overlay.move(x, y)
    
    def handle_submit(self):
        """Handle the submit button click"""
        current_text = self.text_input.toPlainText().strip()
        if current_text:
            self.current_message = current_text
            print(f"Message stored: {self.current_message}")
            self.overlay.set_message(self.current_message)
            self.text_input.clear()
            self.input_handler.clear_text()
    
    def closeEvent(self, event):
        """Clean up when the application is closed"""
        keyboard.unhook_all()
        self.input_handler.timer.stop()
        # Close the overlay window
        self.overlay.close()
        super().closeEvent(event) 