import keyboard
import logging
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTextEdit,
                            QPushButton, QLabel, QHBoxLayout, QSpinBox, QApplication,
                            QGroupBox, QGridLayout, QCheckBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from pathlib import Path
from functools import partial
import time
import threading
import requests

from mute_streamer_overload.core.input_handler import InputHandler
from mute_streamer_overload.ui.overlay_window import OverlayWindow
from mute_streamer_overload.ui.config_dialog import ConfigDialog
from mute_streamer_overload.web.web_server import update_message, update_animation_settings, stop_server, set_fade_out_callback
from mute_streamer_overload.utils.constants import (MIN_OVERLAY_WIDTH, MIN_OVERLAY_HEIGHT,
                                                  INITIAL_OVERLAY_WIDTH, INITIAL_OVERLAY_HEIGHT)
from mute_streamer_overload.utils.config import get_config, set_config, save_config
from mute_streamer_overload.twitch_oauth import send_message_to_twitch_chat
from tts_service.tts_integration import speak

logger = logging.getLogger(__name__)

def _normalize_hotkey(key):
    return key.strip().lower().replace(' ', '')

class MuteStreamerOverload(QMainWindow):
    def __init__(self):
        super().__init__()
        logger.debug("Initializing main window...")
        
        self.setWindowTitle("Mute Streamer Overload")
        # Use config defaults for minimum size
        min_width = get_config("ui.window_width", 600)
        min_height = get_config("ui.window_height", 500)
        self.setMinimumSize(min_width, min_height)
        self.current_start_hotkeys = get_config("input.start_hotkey", ["F4"])
        self.current_submit_hotkeys = get_config("input.submit_hotkey", ["F4"])
        self.center_window()
        self.setup_icon()
        self.setup_ui()
        self.setup_logic()
        self.load_config_values()
        
        # Flag to prevent duplicate Twitch message sends
        self.twitch_message_sent = False

    def setup_icon(self):
        """Find and set the window icon."""
        try:
            import sys
            from pathlib import Path
            icon_paths = []
            if getattr(sys, 'frozen', False):
                # PyInstaller: check _MEIPASS/assets
                meipass = getattr(sys, '_MEIPASS', None)
                if meipass:
                    icon_paths.append(Path(meipass) / 'assets' / 'icon_32x32.ico')
                # Also check project root assets (two up from exe)
                exe_dir = Path(sys.executable).resolve().parent
                icon_paths.append(exe_dir.parent.parent / 'assets' / 'icon_32x32.ico')
            else:
                # Dev: check project root assets
                icon_paths.append(Path(__file__).resolve().parent.parent.parent / 'assets' / 'icon_32x32.ico')
            for icon_path in icon_paths:
                if icon_path.exists():
                    self.setWindowIcon(QIcon(str(icon_path)))
                    return
            logger.warning(f"Icon not found at any of: {[str(p) for p in icon_paths]}, using default.")
        except Exception as e:
            logger.error(f"Failed to set window icon: {e}", exc_info=True)

    def setup_ui(self):
        """Create and arrange all UI widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # --- Title and Settings Button ---
        title_layout = QHBoxLayout()
        
        title_label = QLabel("Mute Streamer Overload")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("TitleLabel")
        title_layout.addWidget(title_label)
        
        self.settings_button = QPushButton("⚙ Settings")
        self.settings_button.setObjectName("SettingsButton")
        self.settings_button.clicked.connect(self.open_settings)
        self.settings_button.setMaximumWidth(100)
        title_layout.addWidget(self.settings_button)
        
        main_layout.addLayout(title_layout)

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

        # Sync overlay WPM with TTS
        self.sync_overlay_wpm_check = QCheckBox("Sync overlay speed with TTS")
        self.sync_overlay_wpm_check.setChecked(get_config("tts.sync_overlay_wpm_with_tts", True))
        self.sync_overlay_wpm_check.toggled.connect(self.on_sync_overlay_wpm_toggled)
        layout.addWidget(self.sync_overlay_wpm_check, 3, 0, 1, 2)
        
        return group

    def create_message_controls(self):
        """Create the 'Message Input' group box."""
        group = QGroupBox("Message Input")
        layout = QVBoxLayout(group)
        
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setMaximumHeight(100)
        layout.addWidget(self.message_input)
        
        # Add Twitch chat toggle
        self.send_to_twitch_checkbox = QCheckBox("Send to Twitch Chat")
        self.send_to_twitch_checkbox.setChecked(get_config("twitch.send_messages", True))
        self.send_to_twitch_checkbox.toggled.connect(self.on_twitch_toggle_changed)
        layout.addWidget(self.send_to_twitch_checkbox)
        
        button_layout = QHBoxLayout()
        self.submit_button = QPushButton("Submit (F4)")
        self.submit_button.clicked.connect(self.handle_submit)
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
        
        self.input_handler.start_typing_signal.connect(self.handle_start_typing)
        self.input_handler.submit_signal.connect(self.handle_submit)
        self.input_handler.text_updated.connect(self.update_text_display)
        self.input_handler.input_state_changed.connect(self.update_input_state)
        
        self.overlay_window.text_animator.fade_out.connect(self.on_fade_out)
        
        # Set up web server fade_out callback
        set_fade_out_callback(self.on_fade_out)
        self.qt_start_shortcuts = []
        self.qt_submit_shortcuts = []
        self.bind_hotkeys()
        self.update_input_state(False)

    def bind_hotkeys(self):
        # Unbind all previous
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        for shortcut in getattr(self, 'qt_start_shortcuts', []):
            shortcut.setKey(QKeySequence())
        for shortcut in getattr(self, 'qt_submit_shortcuts', []):
            shortcut.setKey(QKeySequence())
        self.qt_start_shortcuts = []
        self.qt_submit_shortcuts = []
        suppress = get_config("input.suppress_hotkey", False)
        self.start_hotkeys = get_config("input.start_hotkey", ["F4"])
        self.submit_hotkeys = get_config("input.submit_hotkey", ["F4"])
        # Register QShortcut and global hotkey for start hotkey
        for key in self.start_hotkeys:
            norm_key = _normalize_hotkey(key)
            print(f"[DEBUG] Registering start hotkey: {norm_key}")
            # QShortcut (window-focused)
            sc = QShortcut(QKeySequence(key), self)
            def start_typing_debug():
                logger.debug(f"[HOTKEY] QShortcut start_typing activated for key: {norm_key}")
                self.handle_start_typing()
            sc.activated.connect(start_typing_debug)
            self.qt_start_shortcuts.append(sc)
            # Global hotkey
            def global_start_hotkey(event, action='start', key=norm_key):
                logger.debug(f"[HOTKEY] keyboard.on_press_key start activated for key: {key}, event: {event}")
                return self.input_handler.on_hotkey_press(event, action, key)
            keyboard.on_press_key(norm_key, global_start_hotkey, suppress=suppress)
        logger.info(f"Start hotkeys: {self.start_hotkeys}, Submit hotkeys: {self.submit_hotkeys}, suppress={suppress}")

    def rebind_hotkey(self):
        self.bind_hotkeys()

    def on_config_changed(self):
        """Handle configuration changes."""
        self.load_config_values()
        self.rebind_hotkey()
        logger.info("Configuration updated and applied")

    def load_config_values(self):
        """Load configuration values into the UI."""
        # Load overlay size
        initial_width = get_config("overlay.initial_width", 300)
        initial_height = get_config("overlay.initial_height", 200)
        self.width_input.setValue(initial_width)
        self.height_input.setValue(initial_height)
        
        # Load animation settings
        wpm = get_config("animation.words_per_minute", 500)
        min_chars = get_config("animation.min_characters", 10)
        max_chars = get_config("animation.max_characters", 50)
        
        self.wpm_input.setValue(wpm)
        self.min_chars_input.setValue(min_chars)
        self.max_chars_input.setValue(max_chars)
        
        # Load Twitch settings
        send_to_twitch = get_config("twitch.send_messages", True)
        self.send_to_twitch_checkbox.setChecked(send_to_twitch)
        
        # Load window size
        window_width = get_config("ui.window_width", 600)
        window_height = get_config("ui.window_height", 500)
        self.resize(window_width, window_height)
        
        # Apply settings to overlay
        if self.overlay_window:
            self.overlay_window.resize(initial_width, initial_height)
            self.overlay_window.text_animator.set_words_per_minute(wpm)
            self.overlay_window.text_animator.set_character_limits(min_chars, max_chars)
        
        # Update web server settings
        update_animation_settings(wpm=wpm, min_chars=min_chars, max_chars=max_chars)
        
        # Show overlay on startup if configured
        if get_config("overlay.start_visible", False):
            self.toggle_overlay()

        # Reflect first start hotkey in status label and submit button
        start_hotkeys = get_config("input.start_hotkey", ["F4"])
        first_hotkey = start_hotkeys[0] if start_hotkeys else "F4"
        self.status_label.setText(f"Press {first_hotkey} to start typing")
        self.submit_button.setText(f"Submit ({first_hotkey})")

        # Load TTS sync settings
        self.sync_overlay_wpm_check.setChecked(get_config("tts.sync_overlay_wpm_with_tts", True))
        self.wpm_input.setEnabled(not self.sync_overlay_wpm_check.isChecked())

    def open_settings(self):
        """Open the configuration dialog."""
        dialog = ConfigDialog(self)
        dialog.config_changed.connect(self.on_config_changed)
        dialog.exec()

    def update_character_limits(self):
        min_chars = self.min_chars_input.value()
        max_chars = self.max_chars_input.value()
        if max_chars < min_chars:
            self.max_chars_input.setValue(min_chars)
            max_chars = min_chars
        
        # Save to config
        set_config("animation.min_characters", min_chars)
        set_config("animation.max_characters", max_chars)
        
        if self.overlay_window:
            self.overlay_window.text_animator.set_character_limits(min_chars, max_chars)
        update_animation_settings(min_chars=min_chars, max_chars=max_chars)
            
    def update_wpm(self):
        wpm = self.wpm_input.value()
        
        # Save to config
        set_config("animation.words_per_minute", wpm)
        
        if self.overlay_window:
            self.overlay_window.text_animator.set_words_per_minute(wpm)
        update_animation_settings(wpm=wpm)
        # If not syncing with TTS, update the web overlay immediately
        if not self.sync_overlay_wpm_check.isChecked():
            try:
                requests.post('http://127.0.0.1:5000/set_overlay_wpm', json={'wpm': wpm})
            except Exception as e:
                print(f"Failed to update overlay WPM: {e}")
            
    def update_overlay_size(self):
        width = self.width_input.value()
        height = self.height_input.value()
        
        # Save to config
        set_config("overlay.initial_width", width)
        set_config("overlay.initial_height", height)
        
        if self.overlay_window:
            self.overlay_window.resize(width, height)
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
    
    def handle_start_typing(self):
        if not self.input_handler.is_active:
            self.input_handler.toggle_input()
            if self.input_handler.is_active:
                self.activateWindow()
                self.raise_()
                # No need to register submit hotkey here; InputHandler handles it

    def handle_submit(self):
        logger.debug(f"[SUBMIT] handle_submit called. is_active={self.input_handler.is_active}")
        # Reset Twitch message sent flag for new submission
        self.twitch_message_sent = False
        
        # Accept submission from both button and hotkey
        if self.input_handler.is_active:
            current_text = self.input_handler.get_current_text()
            logger.debug(f"[SUBMIT] handle_submit (typing mode): current_text='{current_text}'")
            if current_text.strip():
                self.current_message = current_text
                logger.debug(f"[SUBMIT] handle_submit: set_message called with '{self.current_message}'")
                # Always start web server animation (for Twitch timing)
                self.overlay_window.trigger_web_animation(self.current_message)  # This triggers only web server animation
                self.message_input.setText(self.current_message)
                self.input_handler.clear_text()
                # TTS: Speak the submitted message in a background thread
                threading.Thread(target=speak, args=(current_text,), daemon=True).start()
                # Send to Twitch chat if enabled and timing is 'immediate'
                if self.send_to_twitch_checkbox.isChecked() and get_config("twitch.send_timing", "immediate") == "immediate":
                    logger.info(f"[TWITCH] Sending message immediately: {current_text}")
                    send_message_to_twitch_chat(current_text)
                    self.twitch_message_sent = True
                else:
                    logger.info(f"[TWITCH] Not sending immediately - checkbox: {self.send_to_twitch_checkbox.isChecked()}, timing: {get_config('twitch.send_timing', 'immediate')}")
            self.input_handler.is_active = False
            self.input_handler.f4_pressed = False
            self.input_handler.input_state_changed.emit(False)
            keyboard.unhook_all()  # Unregister submit hotkey after submission
            self.bind_hotkeys()  # Re-register start hotkey
        else:
            # Submission from button (not hotkey mode)
            message = self.message_input.toPlainText().strip()
            logger.debug(f"[SUBMIT] handle_submit (button mode): message='{message}'")
            if message:
                self.current_message = message
                logger.debug(f"[SUBMIT] handle_submit: set_message called with '{self.current_message}' (button mode)")
                # Always start web server animation (for Twitch timing)
                self.overlay_window.trigger_web_animation(self.current_message)  # This triggers only web server animation
                self.message_input.clear()
                self.input_handler.clear_text()
                # TTS: Speak the submitted message in a background thread
                threading.Thread(target=speak, args=(message,), daemon=True).start()
                if self.send_to_twitch_checkbox.isChecked() and get_config("twitch.send_timing", "immediate") == "immediate":
                    logger.info(f"[TWITCH] Sending message immediately (button mode): {message}")
                    send_message_to_twitch_chat(message)
                    self.twitch_message_sent = True
                else:
                    logger.info(f"[TWITCH] Not sending immediately (button mode) - checkbox: {self.send_to_twitch_checkbox.isChecked()}, timing: {get_config('twitch.send_timing', 'immediate')}")
    
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
    
    def closeEvent(self, event):
        # Save window position and size to config
        set_config("ui.window_width", self.width())
        set_config("ui.window_height", self.height())
        set_config("ui.window_x", self.x())
        set_config("ui.window_y", self.y())
        save_config()
        
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
        
        # Check if we have saved window position
        saved_x = get_config("ui.window_x")
        saved_y = get_config("ui.window_y")
        
        if saved_x is not None and saved_y is not None:
            # Use saved position
            self.move(saved_x, saved_y)
        else:
            # Center the window
            screen_geometry = screen.geometry()
            size = self.geometry()
            x = (screen_geometry.width() - size.width()) // 2
            y = (screen_geometry.height() - size.height()) // 2
            self.move(x, y)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
        self.raise_()

    def on_fade_out(self):
        message = self.current_message
        logger.info(f"[TWITCH] on_fade_out called with message: {message}")
        def send_after_delay():
            time.sleep(2)
            # Only send to Twitch chat if the toggle is enabled, timing is 'after_animation', and message hasn't been sent yet
            if (self.send_to_twitch_checkbox.isChecked() and 
                get_config("twitch.send_timing", "immediate") == "after_animation" and 
                not self.twitch_message_sent):
                logger.info(f"[TWITCH] Sending message after animation: {message}")
                send_message_to_twitch_chat(message)
                self.twitch_message_sent = True
            else:
                logger.info(f"[TWITCH] Not sending after animation - checkbox: {self.send_to_twitch_checkbox.isChecked()}, timing: {get_config('twitch.send_timing', 'immediate')}, already sent: {self.twitch_message_sent}")
        threading.Thread(target=send_after_delay, daemon=True).start()

    def on_twitch_toggle_changed(self, checked):
        """Handle Twitch chat toggle state change."""
        set_config("twitch.send_messages", checked)
        save_config()
        logger.info(f"Twitch chat sending {'enabled' if checked else 'disabled'}") 

    def on_sync_overlay_wpm_toggled(self, checked):
        set_config("tts.sync_overlay_wpm_with_tts", checked)
        self.wpm_input.setEnabled(not checked) 