import os
import copy
import numpy as np
from PyQt5.QtCore import *


SCREEN_WIDTH = 1024 # 800
SCREEN_HEIGHT = 600 # 480


class VPath:
    def __init__(self) -> None:
        self.assets = os.getcwd() + '/assets/'
        self.data = os.getcwd() + '/assets/data/'
        self.gif = os.getcwd() + '/assets/gif/'
        self.images = os.getcwd() + '/assets/images/'
        self.models = os.getcwd() + '/assets/models/'
        self.temp = os.getcwd() + '/assets/temp/'

vp = VPath()


class SETTINGS:
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(SETTINGS, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self): 
        self.TESTING = True if os.name == 'nt' else False
        if self.TESTING: print(f'\n--- TESTING MODE ---\n')

        #? gui
        self.label_img_width = 832
        self.label_img_height = 468
        self.panel_width = SCREEN_WIDTH - self.label_img_width

        #? Server / Network
        self.rpi_port = 42001

        self.robot_ip = '192.168.69.120' if os.name == 'nt' else '192.168.69.60'
        # self.robot_ip = '192.168.69.170'
        self.robot_port = 42000
        self.robot_url = f'http://{self.robot_ip}:{self.robot_port}/'

        # self.data_server_ip = 'http://192.168.69.169:80'

        #? image processing
        self.avoid_obstacles = False


    def reset(self):
        pass

settings = SETTINGS()



class IMAGE_DATA(QObject):
    custom_signal = pyqtSignal(str)
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(IMAGE_DATA, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rgbd_data = None
        self.sam_img_width = 640
        self.sam_img_height = 360
        
        self.robot_frame = [0,0,0,0,0,0]
        self.robot_tool = [0,0,0,0,0,0]
        self.robot_pose = [0,0,0,0,0,0]
        self.robot_camera_tool = [0,0,0,0,0,0]

        self.x_boundary_range = [0,0]
        self.y_boundary_range = [0,0]
        self.z_boundary_range = [0,0]

    def set_rgbd(self, rgbd_data):
        self.colors = copy.deepcopy(rgbd_data.colors) # 360, 640
        self.colors_original = copy.deepcopy(rgbd_data.colors_original) # 720, 1280
        self.depth = copy.deepcopy(rgbd_data.depth) # 360, 640
        self.vertices = copy.deepcopy(rgbd_data.vertices) # 360, 640

        self.path_with_timestamp = copy.deepcopy(rgbd_data.path_with_timestamp)
        self.depth_intrinsics = copy.deepcopy(rgbd_data.depth_intrinsics)
        self.color_intrinsics = copy.deepcopy(rgbd_data.color_intrinsics)

        self.camera_params = (self.color_intrinsics['fx'], self.color_intrinsics['fy'], self.color_intrinsics['ppx'], self.color_intrinsics['ppy'])
        self.camera_distortion = np.array(self.color_intrinsics['coeffs'])

        # if not os.path.exists(vp.data + f'{self.folder_name}'):
        #     os.makedirs(vp.data + f'{self.folder_name}')

        self.sam_img_height, self.sam_img_width = self.colors.shape[:2]


idata = IMAGE_DATA()

