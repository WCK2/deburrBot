from gui.qt.nframe import *
from gui.qt.nstackedwidget import NStackedWidget
from gui.workers.ntimer import NTimer
from utils.config import vp, settings
from utils.memory import mem
from gui.workers.tserver import server
from gui.workers.tmobileSAM import TMobileSAM
from gui.qt.panel import SidePanel


signal.signal(signal.SIGINT, signal.SIG_DFL)    
qapp = QApplication(sys.argv)

class GlobalSignals(QObject):
    previous_page = pyqtSignal()
    next_page = pyqtSignal()
    reset_signal = pyqtSignal()
    home_signal = pyqtSignal()
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(GlobalSignals, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


gsig = GlobalSignals()
server.run_server()
tsam = TMobileSAM()


class SidePanel(SidePanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._next_page.connect(gsig.next_page)
        self._previous_page.connect(gsig.previous_page)




if __name__=="__main__":
    gsig.home_signal.connect(lambda:print("hello"))
    gsig.home_signal.emit()



