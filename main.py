from gui.qt.common import *
from gui.pages.home import HOME
from gui.pages.generator1 import GENERATOR1
from utils.memory import mem


class DEBURRBOT(NStackedWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.page_home:HOME = self.addWidget(HOME())
        self.page_generator1:GENERATOR1 = self.addWidget(GENERATOR1())

        gsig.previous_page.connect(self.__previous_page)
        gsig.next_page.connect(self.__next_page)

        mem.page_count = self.count()
        mem.page = 0
        self.setCurrentIndex(mem.page)

    # def reset(self):
    #     self.setCurrentWidget(self.page_home)
    #     # settings.reset()

    def __previous_page(self):
        self.setCurrentIndex(self.currentIndex()-1)
    def __next_page(self):
        self.setCurrentIndex(self.currentIndex()+1)
    def setCurrentIndex(self, index: int) -> None:
        return super().setCurrentIndex(index)
    def setCurrentWidget(self, w: QWidget) -> None:
        return super().setCurrentWidget(w)
    def hideEvent(self, a0: QHideEvent) -> None:
        return super().hideEvent(a0)
    def showEvent(self, a0: QShowEvent) -> None:
        return super().showEvent(a0)




if __name__ == "__main__":
    with open('assets/style.css', 'r') as f:
        qapp.setStyleSheet(f.read())
    
    app = DEBURRBOT()
    if os.name == 'nt':
        app.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        app.show()
    else:
        app.showFullScreen()

    input("")

