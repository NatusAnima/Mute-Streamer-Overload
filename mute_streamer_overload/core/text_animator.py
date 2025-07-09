from PyQt6.QtCore import QObject, QTimer, pyqtSignal
import re
import time
import threading

class TextAnimator(QObject):
    """Class to handle additive text animation with fade-out"""
    text_updated = pyqtSignal(str)  # Signal to update the displayed text
    animation_finished = pyqtSignal()  # Signal when animation is complete
    fade_out = pyqtSignal()  # Signal to trigger fade-out in the UI
    
    def __init__(self, words_per_minute=200, min_chars=10, max_chars=50):
        super().__init__()
        self.words_per_minute = words_per_minute
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.timer = QTimer()
        self.interval = int((60 * 1000) / self.words_per_minute)
        self.timer.setInterval(self.interval)
        self.words = []
        self.current_index = 0
        self.is_animating = False
        self.current_message = ""
        self.animation_thread = None
        self.stop_animation = False
    
    def set_character_limits(self, min_chars, max_chars):
        self.min_chars = min_chars
        self.max_chars = max_chars
    
    def start_animation(self, message):
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
        self.stop_animation = True
        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join()
        self.is_animating = False
    
    def set_words_per_minute(self, wpm):
        self.words_per_minute = wpm
        self.interval = int((60 * 1000) / self.words_per_minute)
        self.timer.setInterval(self.interval)
    
    def is_running(self):
        return self.is_animating
    
    def _animate_text(self):
        if not self.current_message:
            return
        print(f"[ANIMATOR] Starting animation for: '{self.current_message}'")
        words = re.findall(r'\S+|\s+', self.current_message)
        i = 0
        n = len(words)
        delay = 60.0 / self.words_per_minute
        while i < n and not self.stop_animation:
            # Start a new sentence
            sentence_words = []
            char_count = 0
            # Build up the sentence word by word, additive
            while i < n:
                word = words[i]
                # If adding this word would exceed max_chars, break
                next_count = char_count + len(word) + (1 if sentence_words else 0)
                if next_count > self.max_chars:
                    break
                if sentence_words:
                    char_count += 1  # space
                sentence_words.append(word.strip())
                char_count += len(word.strip())
                # Emit the additive build-up
                self.text_updated.emit(' '.join(sentence_words))
                time.sleep(delay)
                i += 1
            # After reaching max_chars, pause before next sentence
            if i < n:
                time.sleep(delay)
        # Fade out at the end
        if not self.stop_animation:
            print(f"[ANIMATOR] Animation finished, emitting fade_out signal")
            self.animation_finished.emit()
            self.fade_out.emit()
        self.is_animating = False