from gui.qt.nframe import *
from PyQt5.QtCore import pyqtSignal
import time


class NStackedWidget(QStackedWidget,NFrame):
    end_signal=pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # QShortcut(QKeySequence("q"), self).activated.connect(sys.exit)
        QShortcut(QKeySequence("q"), self).activated.connect(self.__exit)

    def __exit(self):
        self.end_signal.emit()
        time.sleep(0.1)
        sys.exit()

    def addWidget(self, w: QWidget)->QWidget:
        w.setParent(self)
        super().addWidget(w)
        return w

