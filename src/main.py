import sys
from PyQt5.QtWidgets import QApplication
from audio_app import AudioApp

def main():
    """The main function to start the application."""
    app = QApplication(sys.argv)
    ex = AudioApp()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
