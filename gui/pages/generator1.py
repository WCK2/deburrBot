from PIL import Image, ImageQt
import cv2
import threading
from gui.qt.common import *
from gui.workers.tcamera import TCamera
from utils.config import idata, settings
from gui.workers.tpost import post_req_async
from gui.qt.ngif import NGif


class GENERATOR1(NFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('page_generator1')
        
        #~ initializations
        self.star_objs = []
        self.star_coords = []
        self.star_labels = []

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self, objectName='container1')
        container.setGeometry(QRect(settings.panel_width, 0, SCREEN_WIDTH-settings.panel_width, SCREEN_HEIGHT))
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        #~ -- right panel --
        #~ image
        img_user = cv2.imread(vp.images + 'instructions.jpg')
        img_user = cv2.resize(img_user, (settings.label_img_width, settings.label_img_height), interpolation=cv2.INTER_AREA)
        _height, _width, _ = img_user.shape
        bytes_per_line = 3 * _width
        img_user = QImage(img_user.data, _width, _height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

        self.label_img = QLabel(self)
        self.label_img.setGeometry(QRect(0, 0, settings.label_img_width, settings.label_img_height))
        self.label_img.setPixmap(QPixmap.fromImage(img_user))

        self.btn_img = QPushButton(self, objectName='btn_img')
        self.btn_img.setGeometry(QRect())
        self.btn_img.clicked.connect(self.__onimgbtn)

        self.img_star = QPixmap(vp.images + 'star.png').scaledToWidth(25)

        #~ Menu // row 1 Buttons
        self.btn_new_picture = QPushButton(self, objectName='btn', text='Reset and\nTake Picture')
        self.btn_new_picture.clicked.connect(self.__on_new_picture)
        self.btn_remove = QPushButton(self, objectName='btn',text='Remove')
        self.btn_remove.clicked.connect(self.__on_remove)
        self.btn_generate = QPushButton(self, objectName='btn',text='Generate')
        self.btn_generate.clicked.connect(self.__on_generate)
        self.btn_start = QPushButton(self, objectName='btn',text='Start\nProgram')
        self.btn_start.clicked.connect(self.__on_start)

        hbox1=QHBoxLayout()
        hbox1.setContentsMargins(0,0,0,0)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_new_picture, alignment=Qt.AlignCenter)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_remove, alignment=Qt.AlignCenter)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_generate, alignment=Qt.AlignCenter)
        hbox1.addStretch()
        hbox1.addWidget(self.btn_start, alignment=Qt.AlignCenter)
        hbox1.addStretch()

        #~ layout
        # layout.addStretch()
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

        #~ Gifs
        self.loading_gif = NGif('wait.gif', parent=container)
        self.loading_gif.setGeometry(QRect(0, 0, 250, 250))
        self.loading_gif.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.loading_gif.hide()

        #~ Threads
        self.thread_camera = TCamera()
        self.thread_camera.finished.connect(self.__thread_camera_finished)
        
        tsam.set_finished.connect(self.__tsam_set_finished)
        tsam.run_finished.connect(self.__tsam_run_finished)

        # self.start_timer = NTimer(1500, lambda: self.__onbtn_start(False), repeat=False)

    #? setup
    def __setup(self, img):
        self.__setupimg(img)
        self.__resizeimgbtn()

    def __setupimg(self, img=None):
        if img is None:
            img = cv2.imread(vp.images + 'instructions.jpg')
        img = cv2.resize(img, (settings.label_img_width, settings.label_img_height), interpolation=cv2.INTER_AREA)
        
        _height, _width, _ = img.shape
        bytes_per_line = 3 * _width
        q_image = QImage(img.data, _width, _height, bytes_per_line, QImage.Format_RGB888)#.rgbSwapped()
        self.label_img.setPixmap(QPixmap.fromImage(q_image))

    def __resizeimgbtn(self):
        qrect = self.label_img.geometry()
        self.btn_img.setGeometry(qrect.translated(settings.panel_width, 0))

    def __setup_loading_graphic(self):
        new_x = self.label_img.geometry().x() + (self.label_img.geometry().width() - self.loading_gif.width()) / 2
        new_y = self.label_img.geometry().y() + (self.label_img.geometry().height() - self.loading_gif.height()) / 2
        self.loading_gif.move(int(new_x), int(new_y))

    #? add points / remove / generate / clear
    def __onimgbtn(self):        
        global_pos = self.btn_img.mapFromGlobal(QCursor.pos())
        x_btn = global_pos.x()
        y_btn = global_pos.y()
        # print(f'x_btn: {x_btn}, y_btn: {y_btn}')

        x_ratio = idata.sam_img_width / self.btn_img.width()
        y_ratio = idata.sam_img_height / self.btn_img.height()
        x_sam = round(x_btn * x_ratio)
        y_sam = round(y_btn * y_ratio)
        # print(f'x_sam: {x_sam}, y_sam: {y_sam}')

        qrect = self.label_img.geometry()
        x_star, y_star, _, _ = qrect.translated(x_btn + settings.panel_width, y_btn).getCoords()

        star = QLabel(self, alignment=Qt.AlignCenter)
        __w = self.img_star.width()
        __h = self.img_star.height()
        star.setGeometry(x_star-int(__w/2), y_star-int(__h/2), __w, __h)
        star.setPixmap(self.img_star)
        star.show()
        self.btn_img.raise_()

        self.star_objs.append(star)
        self.star_coords.append([x_sam, y_sam])
        self.star_labels.append(1)
        # print(self.star_coords)

        if self.btn_new_picture.isEnabled() and tsam.image_is_set_flag:
            self.btn_generate.setEnabled(True)

    def __on_new_picture(self):
        if self.thread_camera.threadstatus(): return
        if tsam.threadstatus(): return
        if mem.status != 'idle:100':
            post_req_async(path='mem', data={'name': 'program', 'value': str(100)})
            if settings.TESTING:
                mem.status = 'idle:100'
            return
        
        self.__clear_stars()
        self.btn_new_picture.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.loading_gif.show()

        self.thread_camera.run()

    def __on_remove(self):
        if self.star_objs:
            star = self.star_objs.pop()
            star.deleteLater()
            del self.star_coords[-1]
            del self.star_labels[-1]
        if not self.star_objs:
            self.btn_generate.setEnabled(False)

    def __tsam_set_finished(self):
        self.loading_gif.hide()
        if self.star_objs:
            self.btn_generate.setEnabled(True)

    def __on_generate(self):
        self.btn_start.setEnabled(False)
        tsam.run(self.star_coords, self.star_labels)
    
    def __thread_camera_finished(self):
        self.btn_new_picture.setEnabled(True)
        self.__setup(idata.colors_original)
        tsam.set()

    def __tsam_run_finished(self):
        self.__setupimg(tsam.draw_img)
        if tsam.target_pairs_post_status:
            self.btn_start.setEnabled(True)

    def __on_start(self):
        if tsam.target_pairs_post_status:
            post_req_async(path='mem', data={'name': 'program', 'value': str(1)})
            self.btn_start.setEnabled(False)
        # TODO reset buttons ... and img? idk reset tsam.target_pairs_post_status?

    def __on_clear(self):
        # self.btn_generate.setEnabled(False)
        # self.btn_start.setEnabled(False)

        self.__clear_stars()
    
        self.__setup(idata.colors_original)

    def __clear_stars(self):
        self.star_coords = []
        self.star_labels = []

        while self.star_objs:
            star = self.star_objs.pop()
            star.deleteLater()
        

    #? PyQt Events
    def showEvent(self, a0):
        self.btn_new_picture.setEnabled(True)
        # self.btn_remove.setEnabled(False)
        self.btn_generate.setEnabled(False)
        self.btn_start.setEnabled(False)

        self.__setupimg(img=None)
        self.__resizeimgbtn()
        return super().enterEvent(a0)

    def enterEvent(self, a0):
        self.__setup_loading_graphic()
        return super().enterEvent(a0)

    def hideEvent(self, a0) -> None: 
        self.__clear_stars()
        return super().hideEvent(a0)



if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    with open('assets/style.css', 'r') as f:
        app.setStyleSheet(f.read())

    gui = QLabel()
    page = GENERATOR1(gui)
    if os.name == 'nt':
        page.setGeometry(QRect(0, 0,int(SCREEN_WIDTH), int(SCREEN_HEIGHT)))
        gui.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        gui.show()
    else: gui.showFullScreen()
    
    page.show()
    sys.exit(app.exec_())


    