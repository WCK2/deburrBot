from gui.qt.common import *
from utils.config import settings
from gui.workers.tpost import post_req_async


class ProgramPushButton(QPushButton):
    def __init__(self, program:int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.program = program
        self.clicked.connect(self.__post_program)

    def __post_program(self):
        # print(f'post prog: {self.program}')
        post_req_async(path='mem', data={'name': 'program', 'value': str(self.program)})



class HOME(NFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName('page_home')
        
        #~ initializations
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)

        container = QFrame(self, objectName='container1')
        container.setGeometry(QRect(settings.panel_width, 0, SCREEN_WIDTH-settings.panel_width, SCREEN_HEIGHT))
        layout = QGridLayout(container)
        layout.setVerticalSpacing(10)
        layout.setHorizontalSpacing(10)

        #~ -- right panel --
        self.label_toggle_outputs = QLabel(objectName='header', text='Toggle Outputs')
        self.btn_angle_grinder = QPushButton(objectName='btn', text='Angle Grinder')
        self.btn_angle_grinder.clicked.connect(lambda: post_req_async(path='robot_DO', data={'name': 'angle_grinder', 'value': 'toggle'}))
        self.btn_force_sensor = QPushButton(objectName='btn', text='Force Sensor')
        self.btn_force_sensor.clicked.connect(lambda: post_req_async(path='robot_DO', data={'name': 'force_sensor', 'value': 'toggle'}))

        self.label_quick_programs = QLabel(objectName='header', text='Quick Programs / Robot Control')
        self.btn_picture_pose = ProgramPushButton(100, objectName='btn', text='Move to:\npicture position')
        self.btn_home_pose = ProgramPushButton(101, objectName='btn', text='Move to:\nhome position')
        self.btn_change_flap_disc_pose = ProgramPushButton(102, objectName='btn', text='Move to:\nchange flap\ndisc position')
        self.btn_freedrive = ProgramPushButton(103, objectName='btn', text='Freedrive')

        self.label_system = QLabel(objectName='header', text='System')
        self.btn_shutdown = QPushButton(objectName='btn', text='Shutdown')
        self.btn_shutdown.clicked.connect(self.__on_confirm_shutdown)

        #~ layout
        # layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed))
        layout.addWidget(self.label_toggle_outputs, 0, 0, 1, 3, alignment=Qt.AlignCenter) # Row 0, Column 0, Span 1 row and 4 columns
        layout.addWidget(self.btn_angle_grinder, 1, 0)
        layout.addWidget(self.btn_force_sensor, 1, 1)
        layout.addWidget(QPushButton(objectName='btn', text='-'), 1, 2)

        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 2, 0, 1, 3)

        layout.addWidget(self.label_quick_programs, 3, 0, 1, 3, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_home_pose, 4, 0)
        layout.addWidget(self.btn_picture_pose, 4, 1)
        layout.addWidget(self.btn_change_flap_disc_pose, 4, 2)
        layout.addWidget(self.btn_freedrive, 5, 0)
        layout.addWidget(QPushButton(objectName='btn', text='-'), 5, 1)
        layout.addWidget(QPushButton(objectName='btn', text='-'), 5, 2)

        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 6, 0, 1, 3)

        layout.addWidget(self.label_system, 7, 0, 1, 3, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_shutdown, 8, 0)
        layout.addWidget(QPushButton(objectName='btn', text='-'), 8, 1)
        layout.addWidget(QPushButton(objectName='btn', text='-'), 8, 2)

        layout.addItem(QSpacerItem(10, 10, QSizePolicy.Minimum, QSizePolicy.Fixed), 9, 0, 1, 3)

        #~ add layouts
        self.side_panel = SidePanel(self)
        page_layout.addStretch()
        page_layout.addWidget(self.side_panel)
        page_layout.addLayout(layout)
        page_layout.addStretch()

        #~ Threads

    #? shutdown
    def __on_confirm_shutdown(self):
        message_box = QMessageBox(self)
        message_box.setObjectName('confirmShutdownBox')
        message_box.setWindowTitle('Confirm Shutdown')
        message_box.setText('Are you sure you want to shutdown the system?')
        message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        message_box.setDefaultButton(QMessageBox.No)

        reply = message_box.exec_()

        if reply == QMessageBox.Yes:
            self.__shutdown_system()

    def __shutdown_system(self):
        print(f'__shutdown_system')
        QApplication.quit()

        if os.name != 'nt':
            os.system("echo hi1 && sleep 10 && echo hi2")
            # os.system("sleep 10 && sudo shutdown -h now")

    #? PyQt Events
    def showEvent(self, a0):
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
    page = HOME(gui)
    if os.name == 'nt':
        page.setGeometry(QRect(0, 0,int(SCREEN_WIDTH), int(SCREEN_HEIGHT)))
        gui.resize(int(SCREEN_WIDTH), int(SCREEN_HEIGHT))
        gui.show()
    else: gui.showFullScreen()
    
    page.show()
    sys.exit(app.exec_())


    