import time
from gui.qt.common import *
from utils.config import settings
from gui.workers.tpost import post_req_async


import random
import string
def generate_random_string():
    length = random.randint(20, 200)
    chars = string.ascii_letters + " " * 10  # Increase space probability
    random_string = ''.join(random.choices(chars, k=length))
    return random_string


class SidePanel(QLabel):
    _next_page = pyqtSignal()
    _previous_page = pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setGeometry(QRect(0, 0, settings.panel_width, SCREEN_HEIGHT))
        self.setFixedSize(settings.panel_width, SCREEN_HEIGHT)
        self.setObjectName('panel')

        #~ Left Panel
        panel_container = QFrame(self, objectName='container1')
        panel_container.setGeometry(QRect(0, 0, settings.panel_width, SCREEN_HEIGHT))
        panel = QVBoxLayout(panel_container)
        panel.setContentsMargins(0, 0, 0, 0)

        self.page_label = QLabel(objectName='param_value', text=f'Page: {mem.page}')
        self.page_btn_down = QPushButton(objectName='btn_grid', text='-')
        self.page_btn_up = QPushButton(objectName='btn_grid', text='+')
        self.page_btn_down.clicked.connect(lambda: self.__inc_page(False))
        self.page_btn_up.clicked.connect(lambda: self.__inc_page(True))
        page_grid = QGridLayout(panel_container)
        page_grid.setVerticalSpacing(0)
        page_grid.setHorizontalSpacing(5)
        page_grid.addWidget(self.page_label, 0, 0, 1, 2, alignment=Qt.AlignCenter)
        page_grid.addWidget(self.page_btn_down, 1, 0)
        page_grid.addWidget(self.page_btn_up, 1, 1)

        self.speed_label = QLabel(objectName='param_value', text=f'Speed: {mem.speed_option_list[mem.speed_index]}%')
        self.speed_btn_down = QPushButton(objectName='btn_grid', text='-')
        self.speed_btn_up = QPushButton(objectName='btn_grid', text='+')
        self.speed_btn_down.clicked.connect(lambda: self.__inc_speed(False))
        self.speed_btn_up.clicked.connect(lambda: self.__inc_speed(True))
        speed_grid = QGridLayout(panel_container)
        speed_grid.setVerticalSpacing(0)
        speed_grid.setHorizontalSpacing(5)
        speed_grid.addWidget(self.speed_label, 0, 0, 1, 2, alignment=Qt.AlignCenter)
        speed_grid.addWidget(self.speed_btn_down, 1, 0)
        speed_grid.addWidget(self.speed_btn_up, 1, 1)

        self.force_label = QLabel(objectName='param_value', text=f'Force: {abs(mem.force)}')
        self.force_btn_down = QPushButton(objectName='btn_grid', text='-')
        self.force_btn_up = QPushButton(objectName='btn_grid', text='+')
        self.force_btn_down.clicked.connect(lambda: self.__inc_force(False))
        self.force_btn_up.clicked.connect(lambda: self.__inc_force(True))
        force_grid = QGridLayout(panel_container)
        force_grid.setVerticalSpacing(0)
        force_grid.setHorizontalSpacing(5)
        force_grid.addWidget(self.force_label, 0, 0, 1, 2, alignment=Qt.AlignCenter)
        force_grid.addWidget(self.force_btn_down, 1, 0)
        force_grid.addWidget(self.force_btn_up, 1, 1)

        self.status_name = QLabel(objectName='param_name', text='Robot Status:')
        self.status_value = QLabel(objectName='param_value', text=str(mem.status), minimumWidth=settings.panel_width, maximumWidth=settings.panel_width)
        self.status_value.setWordWrap(True)
        self.status_value.setAlignment(Qt.AlignTop)
        status_grid = QGridLayout(panel_container)
        status_grid.setVerticalSpacing(0)
        status_grid.setHorizontalSpacing(5)
        status_grid.addWidget(self.status_name, 0, 0, alignment=Qt.AlignCenter)
        status_grid.addWidget(self.status_value, 1, 0, alignment=Qt.AlignCenter)

        self.btn_stop = QPushButton(self, objectName='btn_stop', text='STOP', minimumHeight=50, maximumHeight=50)
        self.btn_stop.setCheckable(True)
        self.btn_stop.clicked.connect(self.__onbtn_stop)

        panel.addSpacing(5)
        panel.addWidget(QLabel(self, objectName='title', text='Deburr Bot'), alignment=Qt.AlignCenter)
        panel.addSpacing(5)
        panel.addWidget(QLabel(self, objectName='container1', text='', minimumWidth=settings.panel_width, maximumWidth=settings.panel_width, minimumHeight=1, maximumHeight=1), alignment=Qt.AlignCenter)
        panel.addSpacing(5)
        panel.addLayout(page_grid)
        panel.addSpacing(10)
        panel.addLayout(speed_grid)
        panel.addSpacing(10)
        panel.addLayout(force_grid)
        panel.addSpacing(10)
        panel.addLayout(status_grid)
        panel.addStretch()
        panel.addSpacing(10)
        panel.addWidget(self.btn_stop, alignment=Qt.AlignCenter)
        panel.addSpacing(10)

        #~ Threads
        mem.new_status.connect(self.__on_new_status)


    #? Panel buttons / events
    def __inc_page(self, b:bool):
        n = 1 if b else -1
        i = mem.page + n
        if (i < 0) or (i >= mem.page_count): return
        mem.page = i
        self.page_label.setText(f'Page: {mem.page}')
        if b:
            self._next_page.emit()
        else:
            self._previous_page.emit()

    def __inc_speed(self, b:bool):
        n = 1 if b else -1
        i = mem.speed_index + n
        if (i < 0) or (i >= len(mem.speed_option_list)): return
        mem.speed_index = i
        self.speed_label.setText(f'Speed: {mem.speed_option_list[mem.speed_index]}%')
        post_req_async(path='mem', data={'name': 'speed_multiplier', 'value': mem.speed_option_list[mem.speed_index]})

    def __inc_force(self, b:bool):
        # mem.status = generate_random_string()
        n = 1 if b else -1
        p = abs(mem.force) + n
        if (p < 1) or (p > 8): return
        mem.force = -p
        self.force_label.setText(f'Force: {abs(p)}')
        post_req_async(path='mem', data={'name': 'desired_force', 'value': mem.force})

    def __on_new_status(self):
        self.status_value.setText(str(mem.status))
        if mem.status == 'Booting': pass
        elif mem.status == 'Emergency Stop': pass

    def __onbtn_stop(self):
        if self.btn_stop.isChecked():
            post_req_async(path='robot_DO', data={'name': 'emergency_output', 'value': True})
        else:
            post_req_async(path='robot_DO', data={'name': 'emergency_output', 'value': False})


    #? PyQt Events
    def showEvent(self, a0):
        self.page_label.setText(f'Page: {mem.page}')
        self.speed_label.setText(f'Speed: {mem.speed_option_list[mem.speed_index]}%')
        self.force_label.setText(f'Force: {abs(mem.force)}')
        self.status_value.setText(str(mem.status))
        return super().enterEvent(a0)

    def enterEvent(self, a0):
        return super().enterEvent(a0)

    def hideEvent(self, a0) -> None:
        return super().hideEvent(a0)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    qapp = QApplication(sys.argv)
    with open(vp.assets + 'style.css', 'r') as f:
        qapp.setStyleSheet(f.read())
    gui = QLabel()
    background = QLabel(gui)
    background.setGeometry(QRect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    background.setScaledContents(True)
    page = SidePanel(gui)

    if os.name == 'nt':
        page.setGeometry(QRect(0, 0,int(SCREEN_WIDTH), int(SCREEN_HEIGHT)))
        gui.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        gui.show()
    else: gui.showFullScreen()
    
    
    page.show()
    input("")