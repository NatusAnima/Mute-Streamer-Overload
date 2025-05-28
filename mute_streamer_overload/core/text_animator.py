from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import re
import time
import threading

class TextAnimator(QObject):
    """Class to handle text animation with character-based display"""
    text_updated = pyqtSignal(str)  # Signal to update the displayed text
    animation_finished = pyqtSignal()  # Signal when animation is complete
    
    def __init__(self, words_per_minute=200, min_chars=10, max_chars=50):
        super().__init__()
        self.words_per_minute = words_per_minute
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_text)
        
        # Calculate interval based on words per minute
        self.interval = int((60 * 1000) / self.words_per_minute)
        self.timer.setInterval(self.interval)
        
        # Animation state
        self.words = []
        self.current_index = 0
        self.is_animating = False
        self.current_message = ""
        self.animation_thread = None
        self.stop_animation = False
        
    def set_character_limits(self, min_chars, max_chars):
        """Update the minimum and maximum character limits"""
        self.min_chars = min_chars
        self.max_chars = max_chars
        
    def start_animation(self, message):
        """Start animating the text"""
        if self.animation_thread and self.animation_thread.is_alive():
            self.stop_animation = True
            self.animation_thread.join()
            
        self.current_message = message
        self.stop_animation = False
        self.is_animating = True
        self.animation_thread = threading.Thread(target=self._animate_text)
        self.animation_thread.daemon = True
        self.animation_thread.start()
        
    def stop_current_animation(self):
        """Stop the current animation"""
        self.stop_animation = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()
        self.is_animating = False
        
    def _get_next_words(self, words, current_index):
        """Get the next set of words based on character limits"""
        if current_index >= len(words):
            return [], current_index

        result = []
        char_count = 0
        i = current_index

        while i < len(words):
            word = words[i]
            if char_count + len(word) + (len(result) if result else 0) > self.max_chars:
                if not result:  # If we can't even fit one word, force it
                    result.append(word)
                    i += 1
                break
            if char_count + len(word) + (len(result) if result else 0) >= self.min_chars and result:
                break
            result.append(word)
            char_count += len(word)
            i += 1

        return result, i
        
    def _update_text(self):
        """Update the displayed text with the next set of words"""
        if not self.is_animating or self.current_index >= len(self.words):
            self.timer.stop()
            self.is_animating = False
            self.animation_finished.emit()
            return
            
        # Get next set of words based on character limits
        current_words, self.current_index = self._get_next_words(self.words, self.current_index)
        
        # Update the display
        self.text_updated.emit(' '.join(current_words))
        
        # If we've shown all words, stop the animation
        if self.current_index >= len(self.words):
            self.timer.stop()
            self.is_animating = False
            self.animation_finished.emit()
            
    def set_words_per_minute(self, wpm):
        """Update the animation speed"""
        self.words_per_minute = wpm
        self.interval = int((60 * 1000) / self.words_per_minute)
        self.timer.setInterval(self.interval)
        
    def is_running(self):
        """Check if animation is currently running"""
        return self.is_animating 

    def _animate_text(self):
        """Animate the text word by word"""
        if not self.current_message:
            return
            
        words = re.findall(r'\S+|\s+', self.current_message)
        current_index = 0
        delay = 60.0 / self.words_per_minute  # Convert WPM to delay between words
        
        while not self.stop_animation and current_index < len(words):
            next_words, current_index = self._get_next_words(words, current_index)
            if next_words:
                text = ' '.join(next_words)
                self.text_updated.emit(text)
                time.sleep(delay)
                
        if not self.stop_animation:
            # Show the full message when animation is done
            self.text_updated.emit(self.current_message)
            self.animation_finished.emit()
        self.is_animating = False 