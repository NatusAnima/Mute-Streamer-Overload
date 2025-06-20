import keyboard
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from mute_streamer_overload.utils.config import get_config

class InputHandler(QObject):
    """Class to handle input in a separate thread"""
    text_updated = pyqtSignal(str)
    input_state_changed = pyqtSignal(bool)
    start_typing_signal = pyqtSignal()
    submit_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_active = False
        self.temp_input = ""
        self.last_key_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_input)
        self.timer.start(1)  # Process input every 1ms for maximum responsiveness
        self.f4_pressed = False
        self.update_submit_hotkeys()
    
    def update_submit_hotkeys(self):
        # Normalize submit hotkeys to lowercase, no spaces
        self.submit_hotkeys = set(k.strip().lower().replace(' ', '') for k in get_config("input.submit_hotkey", ["F4"]))
    
    def toggle_input(self):
        """Toggle input state"""
        try:
            self.is_active = not self.is_active
            if not self.is_active:
                self.temp_input = ""
                keyboard.unhook_all()
            else:
                keyboard.unhook_all()
                keyboard.hook(self.on_key_event, suppress=True)
                self.update_submit_hotkeys()
            self.input_state_changed.emit(self.is_active)
        except Exception as e:
            print(f"Error toggling input: {e}")
            self.is_active = False
            keyboard.unhook_all()
            self.input_state_changed.emit(False)
    
    def on_hotkey_press(self, event, action, key):
        print(f"[DEBUG] on_hotkey_press called: event={event}, action={action}, key={key}")
        if action == 'start':
            if not self.is_active:
                self.start_typing_signal.emit()
        elif action == 'submit':
            if self.is_active:
                self.submit_signal.emit()
        return False
    
    def process_input(self):
        pass  # No longer needed for hotkey debounce
    
    def on_key_event(self, event):
        if not self.is_active:
            return True
        try:
            # Check for submit hotkey
            if event.event_type == keyboard.KEY_DOWN:
                key_name = event.name.lower().replace(' ', '')
                if key_name in self.submit_hotkeys:
                    self.submit_signal.emit()
                    return False
                if event.name == 'backspace':
                    self.temp_input = self.temp_input[:-1]
                    self.text_updated.emit(self.temp_input)
                    return False
                elif event.name == 'enter':
                    if self.temp_input.strip():
                        self.submit_signal.emit()
                    return False
                elif event.name == 'space':
                    self.temp_input += ' '
                    self.text_updated.emit(self.temp_input)
                    return False
                elif len(event.name) == 1:
                    is_shift = keyboard.is_pressed('shift')
                    char = event.name.upper() if is_shift else event.name.lower()
                    current_time = time.time()
                    if current_time - self.last_key_time < 0.01:
                        return False
                    self.last_key_time = current_time
                    self.temp_input += char
                    self.text_updated.emit(self.temp_input)
                    return False
            return False
        except Exception as e:
            print(f"Error handling key event: {e}")
            return False
    
    def get_current_text(self):
        return self.temp_input
    
    def clear_text(self):
        self.temp_input = ""
        self.text_updated.emit(self.temp_input) 