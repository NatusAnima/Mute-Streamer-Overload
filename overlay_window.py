from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QPoint

class OverlayWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumSize(300, 150)  # Set reasonable minimum size
        self.setMaximumSize(16777215, 16777215)  # Keep maximum size unlimited
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create title bar
        self.title_bar = QWidget()
        self.title_bar.setFixedHeight(30)
        self.title_bar.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 120);
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
        """)
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
        close_button.setStyleSheet("""
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
        """)
        close_button.clicked.connect(self.hide)
        title_layout.addWidget(close_button)
        
        main_layout.addWidget(self.title_bar)
        
        # Create content widget with rounded bottom corners
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }
        """)
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create message label
        self.message_label = QLabel()
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: transparent;
            }
        """)
        self.message_label.setWordWrap(True)
        content_layout.addWidget(self.message_label)
        
        main_layout.addWidget(self.content_widget)
        
        # Initialize position tracking
        self.old_pos = None
        
        # Set initial size
        self.resize(400, 200)
        
        # Store the current message for font size calculations
        self.current_message = ""
        
    def set_message(self, message):
        """Update the displayed message and adjust font size"""
        if message:  # Only update if there's a message
            self.current_message = message
            self.message_label.setText(message)
            self.adjust_font_size()
            
    def adjust_font_size(self):
        """Dynamically adjust font size to fit the text in the window"""
        if not self.current_message:
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
                self.current_message
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