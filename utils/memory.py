import threading
from PyQt5.QtCore import *


#~ memory class
class MEM(QObject):
    new_status = pyqtSignal()
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(MEM, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()
        self.page_count = 1 # updates in main.py

        #? system controls
        self.start = False
        self.stop = False

        self.page = 0
        self.speed_option_list = [25, 50, 75, 100, 125, 150, 200, 300]
        self.speed_index = 2
        self.force = -7
        self._status = 'Booting'

        #? data / image processing output
        self.coordinate_dict = {}
        
    def _get_status(self):
        with self.lock:
            return self._status
    def _set_status(self, s):
        with self.lock:
            self._status = s
        self.new_status.emit()
    status = property(_get_status, _set_status)
    

mem = MEM()










