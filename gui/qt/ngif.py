import os
import sys
from PyQt5 import QtGui
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
import signal
from utils.config import vp


class NGif(QLabel):
    def __init__(self, fname='', *args, **kwargs):
        """ Base Page class. Full screen borderless """
        self.__path = vp.gif
        super().__init__(*args, **kwargs)
        self.setObjectName('NGif')
        self.src = property(lambda: self.fname, self.set_src)
        if fname != '': self.set_src(fname)

    def set_src(self, fname:str):
        self.setMovie(QMovie(self.__path + fname))
    
    def play(self):
        self.movie().start()
    def stop(self):
        self.movie().stop()
        
    def showEvent(self, a0: QShowEvent):
        self.play()
        return super().showEvent(a0)
    def hideEvent(self, a0):
        self.stop()
        return super().hideEvent(a0)
        
        