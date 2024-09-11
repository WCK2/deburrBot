import os
if os.name != 'nt':
    os.environ['DISPLAY'] = ':0'
    os.environ['XDG_RUNTIME_DIR'] = '/run/user/1000'
import sys
from utils.config import SCREEN_WIDTH, SCREEN_HEIGHT
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
import signal


class NFrame(QFrame):
    def __init__(self, *args, **kwargs):
        QFrame.__init__(self,*args,**kwargs)
        # # self.resize(QApplication.primaryScreen().size())
        self.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        self.setWindowFlags(Qt.WindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint))
        
        QShortcut(QKeySequence("Esc"), self).activated.connect(sys.exit)

        bg1 = QLabel(self)
        bg1.setGeometry(QRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))




if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    with open('assets/style.css', 'r') as f:
        app.setStyleSheet(f.read())
    
    gui = NFrame()
    gui.show()
    input("")