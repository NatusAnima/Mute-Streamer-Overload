import logging
from pathlib import Path
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QLabel, QSpinBox, QCheckBox, QComboBox,
                            QPushButton, QGroupBox, QGridLayout, QLineEdit,
                            QFileDialog, QMessageBox, QSlider, QDoubleSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from mute_streamer_overload.utils.config import get_config, set_config, save_config, reset_config
from mute_streamer_overload.utils.styles import get_stylesheet

logger = logging.getLogger(__name__)

class ConfigDialog(QDialog):
    """Configuration dialog for managing application settings."""
    
    config_changed = pyqtSignal()  # Signal emitted when config is changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_current_config()
        
    def setup_ui(self):
        """Create the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.tab_widget.addTab(self.create_overlay_tab(), "Overlay")
        self.tab_widget.addTab(self.create_animation_tab(), "Animation")
        self.tab_widget.addTab(self.create_web_server_tab(), "Web Server")
        self.tab_widget.addTab(self.create_ui_tab(), "Interface")
        self.tab_widget.addTab(self.create_input_tab(), "Input")
        self.tab_widget.addTab(self.create_general_tab(), "General")
        self.tab_widget.addTab(self.create_twitch_tab(), "Twitch")
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.export_button = QPushButton("Export Config")
        self.export_button.clicked.connect(self.export_config)
        button_layout.addWidget(self.export_button)
        
        self.import_button = QPushButton("Import Config")
        self.import_button.clicked.connect(self.import_config)
        button_layout.addWidget(self.import_button)
        
        button_layout.addStretch()
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
    def create_overlay_tab(self):
        """Create the overlay settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Size settings
        size_group = QGroupBox("Size Settings")
        size_layout = QGridLayout(size_group)
        
        self.initial_width_spin = QSpinBox()
        self.initial_width_spin.setRange(200, 2000)
        self.initial_width_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Initial Width:"), 0, 0)
        size_layout.addWidget(self.initial_width_spin, 0, 1)
        
        self.initial_height_spin = QSpinBox()
        self.initial_height_spin.setRange(100, 2000)
        self.initial_height_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Initial Height:"), 1, 0)
        size_layout.addWidget(self.initial_height_spin, 1, 1)
        
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(100, 1000)
        self.min_width_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Minimum Width:"), 2, 0)
        size_layout.addWidget(self.min_width_spin, 2, 1)
        
        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(50, 1000)
        self.min_height_spin.setSuffix(" px")
        size_layout.addWidget(QLabel("Minimum Height:"), 3, 0)
        size_layout.addWidget(self.min_height_spin, 3, 1)
        
        layout.addWidget(size_group)
        
        # Behavior settings
        behavior_group = QGroupBox("Behavior")
        behavior_layout = QVBoxLayout(behavior_group)
        
        self.start_visible_check = QCheckBox("Start with overlay visible")
        behavior_layout.addWidget(self.start_visible_check)
        
        self.always_on_top_check = QCheckBox("Always on top")
        behavior_layout.addWidget(self.always_on_top_check)
        
        # Opacity setting
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(90)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(10, 100)
        self.opacity_spin.setSuffix("%")
        self.opacity_spin.setValue(90)
        opacity_layout.addWidget(self.opacity_spin)
        
        # Connect opacity controls
        self.opacity_slider.valueChanged.connect(self.opacity_spin.setValue)
        self.opacity_spin.valueChanged.connect(self.opacity_slider.setValue)
        
        behavior_layout.addLayout(opacity_layout)
        layout.addWidget(behavior_group)
        
        layout.addStretch()
        return widget
    
    def create_animation_tab(self):
        """Create the animation settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Speed settings
        speed_group = QGroupBox("Speed Settings")
        speed_layout = QGridLayout(speed_group)
        
        self.wpm_spin = QSpinBox()
        self.wpm_spin.setRange(1, 1000)
        self.wpm_spin.setSuffix(" WPM")
        speed_layout.addWidget(QLabel("Words per Minute:"), 0, 0)
        speed_layout.addWidget(self.wpm_spin, 0, 1)
        
        self.animation_delay_spin = QSpinBox()
        self.animation_delay_spin.setRange(10, 1000)
        self.animation_delay_spin.setSuffix(" ms")
        speed_layout.addWidget(QLabel("Animation Delay:"), 1, 0)
        speed_layout.addWidget(self.animation_delay_spin, 1, 1)
        
        layout.addWidget(speed_group)
        
        # Character limits
        limits_group = QGroupBox("Character Limits")
        limits_layout = QGridLayout(limits_group)
        
        self.min_chars_spin = QSpinBox()
        self.min_chars_spin.setRange(1, 1000)
        limits_layout.addWidget(QLabel("Minimum Characters:"), 0, 0)
        limits_layout.addWidget(self.min_chars_spin, 0, 1)
        
        self.max_chars_spin = QSpinBox()
        self.max_chars_spin.setRange(1, 1000)
        limits_layout.addWidget(QLabel("Maximum Characters:"), 1, 0)
        limits_layout.addWidget(self.max_chars_spin, 1, 1)
        
        layout.addWidget(limits_group)
        layout.addStretch()
        return widget
    
    def create_web_server_tab(self):
        """Create the web server settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Server settings
        server_group = QGroupBox("Server Settings")
        server_layout = QGridLayout(server_group)
        
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("127.0.0.1")
        server_layout.addWidget(QLabel("Host:"), 0, 0)
        server_layout.addWidget(self.host_edit, 0, 1)
        
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        server_layout.addWidget(QLabel("Port:"), 1, 0)
        server_layout.addWidget(self.port_spin, 1, 1)
        
        self.auto_start_check = QCheckBox("Auto-start web server")
        server_layout.addWidget(self.auto_start_check, 2, 0, 1, 2)
        
        layout.addWidget(server_group)
        layout.addStretch()
        return widget
    
    def create_ui_tab(self):
        """Create the UI settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Theme settings
        theme_group = QGroupBox("Theme")
        theme_layout = QVBoxLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        theme_layout.addWidget(QLabel("Theme:"))
        theme_layout.addWidget(self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Window settings
        window_group = QGroupBox("Main Window")
        window_layout = QGridLayout(window_group)
        
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(400, 2000)
        self.window_width_spin.setSuffix(" px")
        window_layout.addWidget(QLabel("Width:"), 0, 0)
        window_layout.addWidget(self.window_width_spin, 0, 1)
        
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(300, 2000)
        self.window_height_spin.setSuffix(" px")
        window_layout.addWidget(QLabel("Height:"), 1, 0)
        window_layout.addWidget(self.window_height_spin, 1, 1)
        
        layout.addWidget(window_group)
        layout.addStretch()
        return widget
    
    def create_input_tab(self):
        """Create the input settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Hotkey settings
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QVBoxLayout(hotkey_group)
        
        self.start_hotkey_edit = QLineEdit()
        self.start_hotkey_edit.setPlaceholderText("F4 or F4, F5")
        hotkey_layout.addWidget(QLabel("Start Typing Hotkey(s):"))
        hotkey_layout.addWidget(self.start_hotkey_edit)
        
        self.submit_hotkey_edit = QLineEdit()
        self.submit_hotkey_edit.setPlaceholderText("F4 or F4, F5")
        hotkey_layout.addWidget(QLabel("Submit Text Hotkey(s):"))
        hotkey_layout.addWidget(self.submit_hotkey_edit)
        
        layout.addWidget(hotkey_group)
        layout.addStretch()
        return widget
    
    def create_general_tab(self):
        """Create the general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # General settings
        general_group = QGroupBox("General Settings")
        general_layout = QVBoxLayout(general_group)
        
        self.auto_save_check = QCheckBox("Auto-save configuration")
        general_layout.addWidget(self.auto_save_check)
        
        self.check_updates_check = QCheckBox("Check for updates")
        general_layout.addWidget(self.check_updates_check)
        
        # Log level
        log_layout = QHBoxLayout()
        log_layout.addWidget(QLabel("Log Level:"))
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addWidget(self.log_level_combo)
        
        general_layout.addLayout(log_layout)
        layout.addWidget(general_group)
        
        # Config file info
        info_group = QGroupBox("Configuration File")
        info_layout = QVBoxLayout(info_group)
        
        config_path = get_config("_config_file_path", "Unknown")
        info_label = QLabel(f"Location: {config_path}")
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        layout.addStretch()
        return widget
    
    def create_twitch_tab(self):
        """Create the Twitch integration tab."""
        from mute_streamer_overload.utils.config import get_config, set_config, save_config
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Client ID
        client_id_layout = QHBoxLayout()
        client_id_layout.addWidget(QLabel("Client ID:"))
        self.twitch_client_id_edit = QLineEdit()
        client_id_layout.addWidget(self.twitch_client_id_edit)
        layout.addLayout(client_id_layout)
        
        # Client Secret
        client_secret_layout = QHBoxLayout()
        client_secret_layout.addWidget(QLabel("Client Secret:"))
        self.twitch_client_secret_edit = QLineEdit()
        self.twitch_client_secret_edit.setEchoMode(QLineEdit.EchoMode.Password)
        client_secret_layout.addWidget(self.twitch_client_secret_edit)
        layout.addLayout(client_secret_layout)
        
        # Status
        self.twitch_status_label = QLabel()
        layout.addWidget(self.twitch_status_label)
        
        # Channel
        channel_layout = QHBoxLayout()
        channel_layout.addWidget(QLabel("Channel:"))
        self.twitch_channel_edit = QLineEdit()
        channel_layout.addWidget(self.twitch_channel_edit)
        layout.addLayout(channel_layout)
        
        # Login/Logout buttons
        self.twitch_login_button = QPushButton("Login with Twitch")
        self.twitch_login_button.clicked.connect(self.twitch_login)
        layout.addWidget(self.twitch_login_button)
        self.twitch_logout_button = QPushButton("Logout")
        self.twitch_logout_button.clicked.connect(self.twitch_logout)
        layout.addWidget(self.twitch_logout_button)
        
        layout.addStretch()
        return widget
    
    def load_current_config(self):
        """Load current configuration values into the UI."""
        # Overlay settings
        self.initial_width_spin.setValue(get_config("overlay.initial_width", 300))
        self.initial_height_spin.setValue(get_config("overlay.initial_height", 200))
        self.min_width_spin.setValue(get_config("overlay.min_width", 200))
        self.min_height_spin.setValue(get_config("overlay.min_height", 100))
        self.start_visible_check.setChecked(get_config("overlay.start_visible", False))
        self.always_on_top_check.setChecked(get_config("overlay.always_on_top", True))
        
        opacity = get_config("overlay.opacity", 0.9)
        self.opacity_slider.setValue(int(opacity * 100))
        self.opacity_spin.setValue(int(opacity * 100))
        
        # Animation settings
        self.wpm_spin.setValue(get_config("animation.words_per_minute", 200))
        self.min_chars_spin.setValue(get_config("animation.min_characters", 10))
        self.max_chars_spin.setValue(get_config("animation.max_characters", 50))
        self.animation_delay_spin.setValue(get_config("animation.animation_delay_ms", 100))
        
        # Web server settings
        self.host_edit.setText(get_config("web_server.host", "127.0.0.1"))
        self.port_spin.setValue(get_config("web_server.port", 5000))
        self.auto_start_check.setChecked(get_config("web_server.auto_start", True))
        
        # UI settings
        theme = get_config("ui.theme", "dark")
        index = self.theme_combo.findText(theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
        
        self.window_width_spin.setValue(get_config("ui.window_width", 600))
        self.window_height_spin.setValue(get_config("ui.window_height", 500))
        
        # Input settings
        start_hotkeys = get_config("input.start_hotkey", ["F4"])
        submit_hotkeys = get_config("input.submit_hotkey", ["F4"])
        self.start_hotkey_edit.setText(", ".join(start_hotkeys))
        self.submit_hotkey_edit.setText(", ".join(submit_hotkeys))
        
        # General settings
        self.auto_save_check.setChecked(get_config("general.auto_save_config", True))
        self.check_updates_check.setChecked(get_config("general.check_for_updates", True))
        
        log_level = get_config("general.log_level", "INFO")
        index = self.log_level_combo.findText(log_level)
        if index >= 0:
            self.log_level_combo.setCurrentIndex(index)
        
        # Twitch settings
        twitch = get_config("twitch", {})
        access_token = twitch.get("access_token")
        username = twitch.get("username")
        channel = twitch.get("channel")
        client_id = twitch.get("client_id")
        client_secret = twitch.get("client_secret")
        self.twitch_client_id_edit.setText(client_id or "")
        self.twitch_client_secret_edit.setText(client_secret or "")
        if access_token and username:
            self.twitch_status_label.setText(f"Logged in as <b>{username}</b>")
            self.twitch_login_button.setEnabled(False)
            self.twitch_logout_button.setEnabled(True)
        else:
            self.twitch_status_label.setText("Not logged in")
            self.twitch_login_button.setEnabled(True)
            self.twitch_logout_button.setEnabled(False)
        self.twitch_channel_edit.setText(channel or "")
    
    def save_current_config(self):
        """Save current UI values to configuration."""
        # Overlay settings
        set_config("overlay.initial_width", self.initial_width_spin.value())
        set_config("overlay.initial_height", self.initial_height_spin.value())
        set_config("overlay.min_width", self.min_width_spin.value())
        set_config("overlay.min_height", self.min_height_spin.value())
        set_config("overlay.start_visible", self.start_visible_check.isChecked())
        set_config("overlay.always_on_top", self.always_on_top_check.isChecked())
        set_config("overlay.opacity", self.opacity_spin.value() / 100.0)
        
        # Animation settings
        set_config("animation.words_per_minute", self.wpm_spin.value())
        set_config("animation.min_characters", self.min_chars_spin.value())
        set_config("animation.max_characters", self.max_chars_spin.value())
        set_config("animation.animation_delay_ms", self.animation_delay_spin.value())
        
        # Web server settings
        set_config("web_server.host", self.host_edit.text())
        set_config("web_server.port", self.port_spin.value())
        set_config("web_server.auto_start", self.auto_start_check.isChecked())
        
        # UI settings
        set_config("ui.theme", self.theme_combo.currentText())
        set_config("ui.window_width", self.window_width_spin.value())
        set_config("ui.window_height", self.window_height_spin.value())
        
        # Input settings
        start_hotkeys = [k.strip() for k in self.start_hotkey_edit.text().split(",") if k.strip()]
        submit_hotkeys = [k.strip() for k in self.submit_hotkey_edit.text().split(",") if k.strip()]
        set_config("input.start_hotkey", start_hotkeys)
        set_config("input.submit_hotkey", submit_hotkeys)
        
        # General settings
        set_config("general.auto_save_config", self.auto_save_check.isChecked())
        set_config("general.check_for_updates", self.check_updates_check.isChecked())
        set_config("general.log_level", self.log_level_combo.currentText())
        
        # Twitch settings
        set_config("twitch.client_id", self.twitch_client_id_edit.text().strip())
        set_config("twitch.client_secret", self.twitch_client_secret_edit.text().strip())
        set_config("twitch.channel", self.twitch_channel_edit.text().strip())
        
        # Save to file
        save_config()
        self.config_changed.emit()
    
    def save_and_close(self):
        """Save configuration and close dialog."""
        self.save_current_config()
        self.accept()
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            reset_config()
            self.load_current_config()
            self.config_changed.emit()
            QMessageBox.information(self, "Reset Complete", "Configuration has been reset to defaults.")
    
    def export_config(self):
        """Export configuration to a file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from mute_streamer_overload.utils.config import config_manager
                config_manager.export_config(Path(file_path))
                QMessageBox.information(self, "Export Complete", f"Configuration exported to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export configuration:\n{str(e)}")
    
    def import_config(self):
        """Import configuration from a file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                from mute_streamer_overload.utils.config import config_manager
                config_manager.import_config(Path(file_path))
                self.load_current_config()
                self.config_changed.emit()
                QMessageBox.information(self, "Import Complete", f"Configuration imported from:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import configuration:\n{str(e)}")
    
    def twitch_login(self):
        from mute_streamer_overload.twitch_oauth import start_twitch_oauth_flow
        start_twitch_oauth_flow(self)
    
    def twitch_logout(self):
        from mute_streamer_overload.utils.config import set_config, save_config
        set_config("twitch.access_token", None)
        set_config("twitch.refresh_token", None)
        set_config("twitch.username", None)
        set_config("twitch.channel", None)
        save_config()
        self.load_current_config() 