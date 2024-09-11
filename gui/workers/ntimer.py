from PyQt5.QtCore import QTimer

class NTimer(QTimer):
    def __init__(self, interval, cb=lambda:None, repeat=True) -> None:
        super().__init__()
        self.cb = cb
        self.repeat = repeat
        self.setSingleShot(not repeat)
        self.setInterval(interval)
        self.timeout.connect(cb)
        
    def isRunning(self):
        return self.isActive()
    
    def kill(self):
        self.stop()
        
    def reset(self):
        b = self.isActive()
        self.stop()
        if b: self.start()