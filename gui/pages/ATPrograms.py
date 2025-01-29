from PIL import Image, ImageQt
import cv2
import threading
from gui.qt.common import *
from gui.workers.tcamera import TCamera
from utils.config import idata, settings
from utils.memory import mem, atdata
from gui.workers.tpost import post_req_async
from utils.apriltag import TAG_ID_DATA, detect_and_estimate_tags
from utils.target_transformation import TargetTransformer, rotate_pose_around_x


class ATPROGRAMS(NFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('page_ATprograms')
        
        #~ initializations
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self, objectName='container1')
        container.setGeometry(QRect(settings.panel_width, 0, SCREEN_WIDTH-settings.panel_width, SCREEN_HEIGHT))
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        #~ labels
        self.label_title = QLabel(objectName='h1', text='AprilTag Programs')
        # self.label_header = QLabel(objectName='h2', text='Secure parts in their AprilTag Fixtures on the station')

        #~ image
        self.img_shape = (640, 360)
        self.label_img = QLabel(self)
        self.label_img.setFixedSize(*self.img_shape)
        self.label_img.setAlignment(Qt.AlignCenter)

        #~ buttons
        self.btn_prep = QPushButton(self, objectName='btn', text='Move and\ntake picture')
        self.btn_prep.clicked.connect(self.__on_prep)
        self.btn_start = QPushButton(self, objectName='btn',text='Start\nProgram')
        self.btn_start.clicked.connect(self.__on_start)

        hbox1 = QHBoxLayout()
        hbox1.setContentsMargins(0,0,0,0)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_prep, alignment=Qt.AlignCenter)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_start, alignment=Qt.AlignCenter)
        hbox1.addStretch()

        #~ layout
        layout.addStretch()
        layout.addWidget(self.label_title)
        layout.addStretch()
        # layout.addWidget(self.label_header)
        layout.addWidget(self.label_img, alignment=Qt.AlignCenter)
        layout.addStretch()
        layout.addLayout(hbox1)
        layout.addStretch()

        #~ add layouts
        self.side_panel = SidePanel(self)
        page_layout.addStretch()
        page_layout.addWidget(self.side_panel)
        page_layout.addLayout(layout)
        page_layout.addStretch()

        #~ Signals
        atdata.coarse_data.connect(self.__coarse_results)


    #? setup
    def __setupimg(self, img=None):
        if img is None:
            img = cv2.imread(vp.images + 'ATPrograms.jpg')
        img = cv2.resize(img, (settings.label_img_width, settings.label_img_height), interpolation=cv2.INTER_AREA)
        
        if img is not None:
            img = cv2.resize(img, self.img_shape, interpolation=cv2.INTER_AREA)
            img = cv2.resize(img, self.img_shape, interpolation=cv2.INTER_AREA)
            _height, _width, _ = img.shape
            bytes_per_line = 3 * _width
            q_image = QImage(img.data, _width, _height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image).scaled(
                self.label_img.width(),
                self.label_img.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_img.setPixmap(pixmap)
        else:
            print("Error: No image data to display.")
            self.label_img.clear()

    #? buttons / signals
    def __on_prep(self):
        post_req_async(path='mem', data={'name': 'program', 'value': str(10)})
        self.btn_start.setEnabled(False)

    def __coarse_results(self):
        self.__setupimg(atdata.draw_img)

        if atdata.detections:
            self.btn_start.setEnabled(True)
        else:
            self.btn_start.setEnabled(False)

    def __on_start(self):
        post_req_async(path='mem', data={'name': 'program', 'value': str(11)})
        self.btn_start.setEnabled(False)

    #? PyQt Events
    def showEvent(self, a0):
        self.btn_prep.setEnabled(True)
        self.btn_start.setEnabled(False)
        self.__setupimg(img=None)
        return super().enterEvent(a0)

    def enterEvent(self, a0):
        return super().enterEvent(a0)

    def hideEvent(self, a0) -> None: 
        return super().hideEvent(a0)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    with open('assets/style.css', 'r') as f:
        app.setStyleSheet(f.read())

    gui = QLabel()
    page = ATPROGRAMS(gui)
    if os.name == 'nt':
        page.setGeometry(QRect(0, 0,int(SCREEN_WIDTH), int(SCREEN_HEIGHT)))
        gui.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        gui.show()
    else: gui.showFullScreen()
    
    page.show()
    sys.exit(app.exec_())


    