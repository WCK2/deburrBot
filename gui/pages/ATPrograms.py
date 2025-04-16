from PIL import Image, ImageQt
import cv2
import numpy as np
import threading
from gui.qt.common import *
from gui.workers.tcamera import TCamera
from utils.config import idata, settings
from utils.memory import mem, atdata
from gui.workers.tpost import post_req_async
from utils.apriltag import TAG_ID_DATA, detect_and_estimate_tags
from utils.target_transformation import TargetTransformer, rotate_pose_around_x



class ATTargetSelector(QLabel):
    def __init__(self, parent=None, img_size=(300, 300)):
        super().__init__(parent)
        self.setObjectName('target_selector')
        self.setFixedSize(QSize(img_size[0], img_size[1]))
        self.target_buttons = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)

        self.label_img = QLabel(self, objectName='img')
        self.label_img.setFixedSize(QSize(*img_size))
        self.layout.addWidget(self.label_img, alignment=Qt.AlignCenter)

    def set_image(self, img_path):
        """Load a new image, resize it, and update buttons based on filename."""
        self.current_filename = os.path.basename(img_path)
        # print(f'img_path: {img_path}')

        if not os.path.exists(img_path):
            print(f'Image {self.current_filename} not found.')
            self.label_img.clear()
            self.update_buttons()
            return
        
        #? load image and resize
        img = cv2.imread(img_path)
        self.original_img_size = img.shape
        img = cv2.resize(img, (self.label_img.width(), self.label_img.height()), interpolation=cv2.INTER_AREA)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img.shape
        q_img = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
        self.label_img.setPixmap(QPixmap.fromImage(q_img))

        self.update_buttons()
    
    def update_buttons(self):
        for btn in self.target_buttons:
            btn.setParent(None)
        self.target_buttons.clear()

        button_positions = {
            'ATTargetSelector12.jpg': [(61, 493), (61, 380), (61, 223), (61, 98), (367, 565), (367, 435), (367, 195), (367, 67)],
            'ATTargetSelector13.jpg': [(67, 560), (67, 450), (67, 194), (67, 83), (366, 496), (366, 387), (366, 232), (366, 100)], # (50, 593), (50, 51), (383, 593), (383, 51)]
        }

        if self.current_filename in button_positions:
            scale_x = self.label_img.width() / self.original_img_size[1]
            scale_y = self.label_img.height() / self.original_img_size[0]

            btn_size = 40
            for i, (orig_x, orig_y) in enumerate(button_positions[self.current_filename], start=0):
                scaled_x = int(orig_x * scale_x)
                scaled_y = int(orig_y * scale_y)

                btn = QPushButton(self, objectName='btn_tar', text=f'{i}')
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.setFixedSize(btn_size, btn_size)

                btn.move(self.label_img.x() + scaled_x - btn_size // 2, self.label_img.y() + scaled_y - btn_size // 2)
                btn.show()
                self.target_buttons.append(btn)

    def get_selected_targets(self):
        """Return a list of enabled target button numbers."""
        return [int(btn.text()) for btn in self.target_buttons if btn.isChecked()]



class ATPROGRAMS(NFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('page_ATprograms')
        self.program_selection = 12
        
        #~ initializations
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self, objectName='container1')
        container.setGeometry(QRect(settings.panel_width, 0, SCREEN_WIDTH-settings.panel_width, SCREEN_HEIGHT))
        grid_layout = QGridLayout(container)
        grid_layout.setContentsMargins(20, 10, 20, 10)
        grid_layout.setSpacing(15)

        #~ program selection
        self.label_title = QLabel(self, objectName='h1', text='AprilTag Programs')
        self.label_title.setFixedHeight(self.label_title.sizeHint().height())

        self.label_program_selection = QLabel(self, objectName='h2', text=f'<u>Program Selection</u>: {self.program_selection}')
        self.label_program_selection.setFixedHeight(self.label_program_selection.sizeHint().height())

        self.btn_prog_down = QPushButton(self, objectName='btn_grid', text='-', minimumWidth=75, minimumHeight=40)
        self.btn_prog_down.clicked.connect(lambda: self.__inc_prog(False))
        self.btn_prog_up = QPushButton(self, objectName='btn_grid', text='+', minimumWidth=75, minimumHeight=40)
        self.btn_prog_up.clicked.connect(lambda: self.__inc_prog(True))

        #~ tar selector
        self.label_target_selector_title = QLabel(self, objectName='h2', text=f'<u>Target Selection</u>')
        self.label_target_selector_title.setFixedHeight(self.label_target_selector_title.sizeHint().height())

        self.target_selector = ATTargetSelector(self, img_size=(400, 350))
        self.target_selector.set_image(vp.images + f'ATTargetSelector{self.program_selection}.jpg')

        #~ robot img
        self.label_robot_img_title = QLabel(self, objectName='h2', text=f'<u>Detections</u>')
        self.label_robot_img_title.setFixedHeight(self.label_robot_img_title.sizeHint().height())

        self.label_draw_img = QLabel(self, objectName='img') # sets fixed size in first call to __setup_img

        #~ controls
        self.btn_start = QPushButton(self, objectName='btn',text='Start\nProgram')
        self.btn_start.clicked.connect(self.__on_start)

        #~ layout
        grid_layout.addWidget(self.label_title, 0, 0, 1, 4)
        grid_layout.addWidget(self.label_program_selection, 1, 0, 1, 2)
        grid_layout.addWidget(self.btn_prog_down, 2, 0, 1, 1)
        grid_layout.addWidget(self.btn_prog_up, 2, 1, 1, 1)
        grid_layout.addItem(QSpacerItem(10, 20, QSizePolicy.Minimum, QSizePolicy.Fixed), 3, 0, 1, 2)
        grid_layout.addWidget(self.label_robot_img_title, 4, 0, 1, 2)
        grid_layout.addWidget(self.label_draw_img, 5, 0, 1, 2)

        grid_layout.addWidget(self.label_target_selector_title, 1, 2, 1, 2)
        grid_layout.addWidget(self.target_selector, 2, 2, 4, 2, alignment=Qt.AlignCenter | Qt.AlignTop)

        # grid_layout.addWidget(self.btn_prep, 7, 0, 1, 2, alignment=Qt.AlignCenter)
        grid_layout.addWidget(self.btn_start, 7, 3, 1, 1, alignment=Qt.AlignCenter)


        #~ add layouts
        self.side_panel = SidePanel(self)
        page_layout.addWidget(self.side_panel)
        page_layout.addLayout(grid_layout)

        #~ Signals
        atdata.target_runner_detections.connect(self.__target_runner_results)

    #? signals / setup
    def __setupimg(self, img=None):
        if self.label_draw_img.width() != self.label_draw_img.maximumWidth():
            self.label_draw_img.setFixedWidth(self.label_draw_img.width())
            height = int(0.5625* self.label_draw_img.width())
            self.label_draw_img.setFixedHeight(height)

        if img is None:
            # img = cv2.imread(vp.images + 'ATPrograms.jpg')
            img = np.zeros((360, 640, 3), dtype=np.uint8)
        img = cv2.resize(img, (self.label_draw_img.width(), self.label_draw_img.height()), interpolation=cv2.INTER_AREA)
        
        if img is not None:
            img = cv2.resize(img, (self.label_draw_img.width(), self.label_draw_img.height()), interpolation=cv2.INTER_AREA)

            _height, _width, _ = img.shape
            bytes_per_line = 3 * _width
            q_image = QImage(img.data, _width, _height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image).scaled(
                self.label_draw_img.width(),
                self.label_draw_img.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.label_draw_img.setPixmap(pixmap)
        else:
            print("Error: No image data to display.")
            self.label_draw_img.clear()

    def __target_runner_results(self):
        self.__setupimg(atdata.draw_img)

    #? buttons
    def __inc_prog(self, b:bool):
        n = 1 if b else -1
        p = self.program_selection + n
        if p < 0: return
        self.program_selection = p
        self.label_program_selection.setText(f'<u>Program Selection</u>: {self.program_selection}')
        self.target_selector.set_image(vp.images + f'ATTargetSelector{self.program_selection}.jpg')

    def __on_start(self):
        atdata.program_selection = self.program_selection
        atdata.target_selections = self.target_selector.get_selected_targets()

        post_req_async(path='mem', data={'name': 'program', 'value': str(2)})
        # disable start button for a couple of seconds



    #? PyQt Events
    def showEvent(self, a0):
        self.btn_start.setEnabled(True)
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


    