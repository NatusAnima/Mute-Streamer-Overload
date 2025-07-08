from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMainWindow
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QWindow, QIcon
from pathlib import Path
import re
import logging

from mute_streamer_overload.core.text_animator import TextAnimator
from mute_streamer_overload.utils.constants import (TITLE_BAR_STYLE, CLOSE_BUTTON_STYLE, 
                      MESSAGE_LABEL_STYLE, CONTENT_WIDGET_STYLE)
from mute_streamer_overload.web.web_server import update_message
from mute_streamer_overload.utils.config import get_config

class OverlayWindow(QMainWindow):
    def __init__(self):
        super().__init__(None)  # No parent window
        
        # Set window flags for proper window behavior
        window_flags = (
            Qt.WindowType.Window |  # Make it a proper window
            Qt.WindowType.FramelessWindowHint |  # Remove window frame
            Qt.WindowType.NoDropShadowWindowHint  # Remove drop shadow
        )
        
        # Add always on top if configured
        if get_config("overlay.always_on_top", True):
            window_flags |= Qt.WindowType.WindowStaysOnTopHint
            
        self.setWindowFlags(window_flags)
        
        # Set window icon (16x16 is appropriate for overlay)
        assets_dir = Path(__file__).parent.parent.parent / 'assets'
        icon_path = assets_dir / 'icon_16x16.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # Set window attributes for proper capture
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_QuitOnClose, False)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet(TITLE_BAR_STYLE)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        
        # Add title label
        title_label = QLabel("Message Overlay")
        title_label.setStyleSheet("color: white; font-size: 12px;")
        title_layout.addWidget(title_label)
        
        # Add spacer to push close button to the right
        title_layout.addStretch()
        
        # Add close button
        close_button = QPushButton("×")
        close_button.setFixedSize(20, 20)
        close_button.setStyleSheet(CLOSE_BUTTON_STYLE)
        close_button.clicked.connect(self.hide)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(self.title_bar)
        
        # Create content widget with rounded bottom corners
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(CONTENT_WIDGET_STYLE)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create message label
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet(MESSAGE_LABEL_STYLE)
        self.message_label.setWordWrap(True)
        content_layout.addWidget(self.message_label)
        
        main_layout.addWidget(self.content_widget)
        
        # Initialize position tracking
        self.old_pos = None
        
        # Set initial size from config
        initial_width = get_config("overlay.initial_width", 400)
        initial_height = get_config("overlay.initial_height", 200)
        self.resize(initial_width, initial_height)
        
        # Set opacity from config
        opacity = get_config("overlay.opacity", 0.9)
        self.setWindowOpacity(opacity)
        
        # Store the current message for font size calculations
        self.current_message = ""
        
        # Create text animator with config values
        wpm = get_config("animation.words_per_minute", 200)
        min_chars = get_config("animation.min_characters", 10)
        max_chars = get_config("animation.max_characters", 50)
        
        self.text_animator = TextAnimator(
            words_per_minute=wpm,
            min_chars=min_chars,
            max_chars=max_chars
        )
        self.text_animator.text_updated.connect(self._update_animated_text)
        self.text_animator.animation_finished.connect(self._on_animation_finished)
        
        # Set window title and properties for better capture
        self.setWindowTitle("Message Overlay")
        
    def showEvent(self, event):
        """Handle window show event to ensure proper window state"""
        super().showEvent(event)
        # Ensure the window is properly layered and visible to capture software
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()
        
        # Force window to be a proper window for capture
        window_handle = self.windowHandle()
        if window_handle:
            window_handle.setFlags(
                Qt.WindowType.Window |
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
        
    def set_message(self, message):
        """Update the displayed message and start animation"""
        logger = logging.getLogger(__name__)
        logger.debug(f"[ANIMATION] set_message called with: '{message}'")
        if message:  # Only update if there's a message
            self.current_message = message
            # Start animation in the overlay window
            logger.debug(f"[ANIMATION] text_animator.start_animation called with: '{message}'")
            self.text_animator.start_animation(message)
            # Update the web overlay (now simplified)
            update_message(message)
            
    def _update_animated_text(self, text):
        """Update the label with animated text"""
        self.message_label.setText(text)
        self.adjust_font_size()
            
    def _on_animation_finished(self):
        """Handle animation completion"""
        # Show the full message when animation is done
        self.message_label.setText(self.current_message)
        self.adjust_font_size()
            
    def adjust_font_size(self):
        """Dynamically adjust font size to fit the text in the window"""
        if not self.message_label.text():
            return
            
        # Get the available space (accounting for padding and title bar)
        available_width = self.width() - 40  # 20px padding on each side
        available_height = self.height() - 70  # Title bar + padding
        
        # Start with a large font size
        font_size = 100
        font = self.message_label.font()
        
        while font_size > 8:  # Don't go smaller than 8pt
            font.setPointSize(font_size)
            self.message_label.setFont(font)
            
            # Get the size the text would need with word wrapping
            text_rect = self.message_label.fontMetrics().boundingRect(
                0, 0, available_width, available_height,
                Qt.TextFlag.TextWordWrap,
                self.message_label.text()
            )
            
            # If the text fits, we're done
            if text_rect.width() <= available_width and text_rect.height() <= available_height:
                break
                
            # Otherwise, try a smaller font size
            font_size -= 1
            
    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        self.adjust_font_size()
        
    def mousePressEvent(self, event):
        """Handle mouse press for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only allow dragging from title bar
            if event.position().y() <= self.title_bar.height():
                self.old_pos = event.globalPosition().toPoint()
                
    def mouseMoveEvent(self, event):
        """Handle mouse move for window dragging"""
        if self.old_pos:
            # Handle dragging
            delta = QPoint(event.globalPosition().toPoint() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        self.old_pos = None
        
    def hideEvent(self, event):
        """Stop animation when window is hidden"""
        self.text_animator.stop_current_animation()
        super().hideEvent(event)
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.text_animator.stop_current_animation()
        event.accept()
        
    def paintEvent(self, event):
        """Ensure proper painting for capture"""
        super().paintEvent(event)
        # Force a repaint to ensure the window is properly rendered
        self.update() 