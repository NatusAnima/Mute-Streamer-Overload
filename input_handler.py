import keyboard
import time
from PyQt6.QtCore import QObject, QTimer, pyqtSignal

class InputHandler(QObject):
    """Class to handle input in a separate thread"""
    text_updated = pyqtSignal(str)
    input_state_changed = pyqtSignal(bool)
    f4_pressed_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.is_active = False
        self.temp_input = ""
        self.last_key_time = 0
        self.f4_pressed = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_input)
        self.timer.start(1)  # Process input every 1ms for maximum responsiveness
        
    def toggle_input(self):
        """Toggle input state"""
        try:
            # Toggle state
            self.is_active = not self.is_active
            self.f4_pressed = True  # Mark F4 as pressed to prevent immediate toggle
            
            if not self.is_active:
                self.temp_input = ""
                # Only hook F4 when inactive
                keyboard.unhook_all()
                keyboard.on_press_key("f4", self.on_f4_press, suppress=True)
            else:
                # Hook all keys when active
                keyboard.unhook_all()
                keyboard.on_press_key("f4", self.on_f4_press, suppress=True)
                keyboard.hook(self.on_key_event, suppress=True)
                
            self.input_state_changed.emit(self.is_active)
        except Exception as e:
            print(f"Error toggling input: {e}")
            self.is_active = False
            self.f4_pressed = False  # Reset F4 state
            keyboard.unhook_all()
            keyboard.on_press_key("f4", self.on_f4_press, suppress=True)
            self.input_state_changed.emit(False)
        
    def on_f4_press(self, event):
        """Handle F4 press and emit signal"""
        if not self.f4_pressed:
            self.f4_pressed = True
            if self.is_active and self.temp_input.strip():
                # If active and has text, submit
                self.f4_pressed_signal.emit()
            elif not self.is_active:
                # If inactive, toggle input mode
                self.f4_pressed_signal.emit()
        return False
        
    def process_input(self):
        """Process input state and handle F4 release"""
        if self.f4_pressed and not keyboard.is_pressed('f4'):
            self.f4_pressed = False
        
    def on_key_event(self, event):
        """Handle key events"""
        if not self.is_active:
            return True
            
        try:
            # Handle F4 specially - use it for both toggling and submitting
            if event.name == 'f4' and event.event_type == keyboard.KEY_DOWN and not self.f4_pressed:
                self.f4_pressed = True
                if self.temp_input.strip():  # If there's text, submit it
                    self.f4_pressed_signal.emit()
                else:  # If no text, just toggle input mode
                    self.input_state_changed.emit(False)
                    self.is_active = False
                return False
                
            if event.event_type == keyboard.KEY_DOWN:
                # Handle special keys
                if event.name == 'backspace':
                    self.temp_input = self.temp_input[:-1]
                    self.text_updated.emit(self.temp_input)
                    return False
                    
                elif event.name == 'enter' or event.name == 'f4':
                    # Submit on Enter key if there's text
                    if self.temp_input.strip():
                        self.f4_pressed_signal.emit()
                    return False
                    
                elif event.name == 'space':
                    self.temp_input += ' '
                    self.text_updated.emit(self.temp_input)
                    return False
                    
                # Handle regular characters
                elif len(event.name) == 1:
                    # Check if shift is pressed for proper capitalization
                    is_shift = keyboard.is_pressed('shift')
                    char = event.name.upper() if is_shift else event.name.lower()
                    
                    # Reduced debounce time to 10ms for faster input
                    current_time = time.time()
                    if current_time - self.last_key_time < 0.01:
                        return False
                        
                    self.last_key_time = current_time
                    self.temp_input += char
                    self.text_updated.emit(self.temp_input)
                    return False
                    
            return False  # Consume all other keys when active
        except Exception as e:
            print(f"Error handling key event: {e}")
            return False
        
    def get_current_text(self):
        """Get the current input text"""
        return self.temp_input
        
    def clear_text(self):
        """Clear the current input text"""
        self.temp_input = ""
        self.text_updated.emit(self.temp_input) 