import threading
from PyQt5.QtCore import *
import copy
import numpy as np
from utils.apriltag import TAG_ID_DATA, detect_and_estimate_tags
from utils.target_transformation import *


#~ memory class
class MEM(QObject):
    new_status = pyqtSignal()
    at_signals = pyqtSignal(str)
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
        self.speed_option_list = [20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 150, 200, 300]
        self.speed_index = 4
        
        self.force = -8.5
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


#~ AT Data class
class ATDATA(QObject):
    new_status = pyqtSignal()
    at_signals = pyqtSignal(str)
    coarse_data = pyqtSignal()
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(ATDATA, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.robot_frame = [0,0,0,0,0,0]
        self.robot_tool = [0,0,0,0,0,0]
        self.robot_pose = [0,0,0,0,0,0]
        self.robot_camera_tool = [0,0,0,0,0,0]

    def run_coarse_data(self, rgbd_data, robot_data: dict):
        print(f'run_coarse_data on rgbd_data {rgbd_data.path_with_timestamp.split("/")[-2]}')
        for key, value in robot_data.items():
            print(f'{key.capitalize():<15}: {value}')
        
        self.colors = copy.deepcopy(rgbd_data.colors) # 360, 640
        self.colors_original = copy.deepcopy(rgbd_data.colors_original) # 720, 1280
        self.vertices = copy.deepcopy(rgbd_data.vertices) # 360, 640

        self.path_with_timestamp = copy.deepcopy(rgbd_data.path_with_timestamp)
        self.depth_intrinsics = copy.deepcopy(rgbd_data.depth_intrinsics)
        self.color_intrinsics = copy.deepcopy(rgbd_data.color_intrinsics)

        self.camera_params = (self.color_intrinsics['fx'], self.color_intrinsics['fy'], self.color_intrinsics['ppx'], self.color_intrinsics['ppy'])
        self.camera_distortion = np.array(self.color_intrinsics['coeffs'])

        atdata.robot_frame = robot_data["frame"]
        atdata.robot_tool = robot_data["tool"]
        atdata.robot_pose = robot_data["pose"]
        atdata.robot_camera_tool = robot_data["camera_tool"]

        #? detection(s)
        self.detections, self.draw_img = detect_and_estimate_tags(
            self.colors_original, 
            self.camera_params, 
            self.camera_distortion, 
            show=False
        )

        #? transformations
        transformer = TargetTransformer(
            robot_frame = self.robot_frame,
            robot_tool = self.robot_tool,
            robot_pose = self.robot_pose,
            robot_camera_tool = self.robot_camera_tool
        )

        for c, detection in enumerate(self.detections):
            rotated_pose = rotate_pose_around_x(detection['pose'], 180)
            pose_wrt_frame = transformer.transform(rotated_pose, zero_rxryrz=False)

            #? prep necessary data and convert any arrays to lists
            detection['pose_wrt_frame'] = pose_wrt_frame.tolist()

            #? transform pose_wrt_frame to pose_wrt_world
            T_ref_2_world = pose_2_tform(self.robot_frame)
            T_tcp_2_ref = pose_2_tform(detection['pose_wrt_frame'])
            T_tcp_2_world = np.dot(T_ref_2_world, T_tcp_2_ref)
            pose_tcp_2_world = np.round(tform_2_pose(T_tcp_2_world), 3).tolist()
            detection['_pose_tcp_2_world'] = pose_tcp_2_world[:] #! temp: fixed rot

            temp_rot = [0.244, -1.208, 91.172] #! temp: fixed rot
            pose_tcp_2_world[3:] = temp_rot #! temp: fixed rot
            detection['pose_tcp_2_world'] = pose_tcp_2_world #! temp: fixed rot

            #? right and left ref frames
            right_ref = rotate_pose_around_y(pose_tcp_2_world, 45)
            detection['right_ref'] = right_ref

            left_ref = rotate_pose_around_y(pose_tcp_2_world, -45)
            detection['left_ref'] = left_ref

            #? check boundaries
            tag_id = detection.get('id')
            tag_data = TAG_ID_DATA.get(tag_id, {})
            boundaries = tag_data.get('boundaries', {})

            within_boundaries = True
            axes = ['x', 'y', 'z', 'rx', 'ry', 'rz']
            for i, axis in enumerate(axes):
                boundary = boundaries.get(axis, [float('-inf'), float('inf')])
                if not (boundary[0] <= pose_tcp_2_world[i] <= boundary[1]):
                    within_boundaries = False
                    print(f'Pose {axis} out of bounds for tag {tag_id}: {pose_tcp_2_world[i]} not in {boundary}')
                    break
            
            detection['valid'] = within_boundaries

            # TODO: Check that the part is on the jig

            #? log
            print(f'\ndetection[{c}]\n' + '=' * 30)
            for key, value in detection.items():
                print(f'{key.capitalize():<15}: {value}')
            print('=' * 30)



        self.coarse_data.emit()


atdata = ATDATA()





if __name__ == "__main__":
    from utils.D435_rpi import *
    from utils.img_processing import *
    from utils.config import vp
    
    d435 = D435()
    # rgbd_data = d435.get_data(save=False)
    # rgbd_data = rgbd_read_data('d435_2025-01-22_07-39-42')
    rgbd_data = rgbd_read_data('d435_2025-01-22_07-43-57')
    rgbd_data, _ = rgbd_depth_filter(rgbd_data, 100, 1500)

    robot_data = {
        'frame': [-809.075, -11.325, -100.975, -0.180246, -0.0034, 91.08],
        'tool': [-139.39, 64.585, 199.93, -169.95, 0.288, -115.89],
        'pose': [190.32, -151.19, 832.05, 11.618, -15.506, -94.229],
        'camera_tool': [78.21, 73.4, 50.54, 15.29, -0.46, 150.04],
    }

    atdata.run_coarse_data(rgbd_data, robot_data)
    cv2_show(atdata.draw_img)






