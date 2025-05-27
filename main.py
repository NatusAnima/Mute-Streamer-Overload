import sys
from PyQt6.QtWidgets import QApplication
from main_window import MuteStreamerOverload

def main():
    app = QApplication(sys.argv)
    window = MuteStreamerOverload()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 