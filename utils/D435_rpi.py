import os
import time
import sys
import datetime
import json
import cv2
import numpy as np
import pickle
import pyrealsense2 as rs


#~ initializations
colorizer = rs.colorizer()
align = rs.align(rs.stream.color)


#~ helper functions
class RGBDData:
    VERSION = '1.0.0'
    VERSION_PATH = os.path.abspath(__file__)
    def __init__(self, data_dict:dict) -> None:
        self.data_dict = data_dict
        self.data_dict['VERSION'] = self.VERSION
        self.data_dict['VERSION_PATH'] = self.VERSION_PATH

        self.depth                  = self.data_dict['depth']
        self.depth_image            = self.data_dict['depth_image']
        self.unfiltered_depth       = self.data_dict['unfiltered_depth']
        self.unfiltered_depth_image = self.data_dict['unfiltered_depth_image']
        self.colors_original        = self.data_dict['colors_original']
        self.colors                 = self.data_dict['colors']
        self.vertices               = self.data_dict['vertices']
        self.camera                 = self.data_dict['camera']
        self.path_wout_timestamp    = self.data_dict['path_wout_timestamp']
        self.path_with_timestamp    = self.data_dict['path_with_timestamp']
        self.depth_intrinsics       = self.data_dict['depth_intrinsics']
        self.color_intrinsics       = self.data_dict['color_intrinsics']


def rgbd_save_data(rgbd_data:RGBDData):
    os.makedirs(rgbd_data.path_with_timestamp, exist_ok=True)

    file_name = 'data_dict_1.pkl'
    file_number = 1
    while os.path.isfile(rgbd_data.path_with_timestamp + file_name):
        file_number += 1
        file_name = f'data_dict_{file_number}.pkl'

    with open(rgbd_data.path_with_timestamp + file_name, 'wb') as f:
        pickle.dump(rgbd_data.data_dict, f)


def rgbd_read_data(folder_path:str, file_name:str='data_dict_1.pkl'):
    if not (folder_path.startswith('C:') or folder_path.startswith('/home/')):
        folder_path = os.getcwd() + '/assets/data/' + folder_path

    if not folder_path.endswith('/'): folder_path += '/'
    if not file_name.endswith('.pkl'): file_name += '.pkl'

    if not os.path.exists(f'{folder_path}{file_name}'):
        sys.exit(f'!!Error!! Path does not exist: <{folder_path}{file_name}>')
    
    with open(f'{folder_path}{file_name}', 'rb') as f:
        data_dict = pickle.load(f)
    
    rgbd_data = RGBDData(data_dict)

    return rgbd_data


#~ D435 depth sensor class
class D435:
    _instance = None  # Class-level storage for the singleton instance

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(D435, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, **kwargs):
        if hasattr(self, "initialized"):
            return
        self.initialized = True
        self.device = None
        self.p = None
        self.profile = None

        self.camera = 'd435'
        self.vp_base = kwargs.get('vp_base', os.getcwd() + '/')
        self.vp_data = kwargs.get('vp_data', self.vp_base + 'assets/data/')
        self.load_json = kwargs.get('load_json', self.vp_base + 'assets/configs/d435_default1.json')

    def start_stream(self):
        print(f'start_stream (1)')
        if self.device is None:
            self.device = self.get_device()
        if self.device is None:
            raise RuntimeError(f"Camera {self.camera} not detected")
        
        self.set_post_processing()

        if os.path.isfile(self.load_json):
            self.load_json_params(self.load_json)
        else:
            print(f'!!Warning!! No file exists at: <{self.load_json}>')

        print(f'start_stream (2)')
        self.p = rs.pipeline()
        config = rs.config()
        config.enable_stream(rs.stream.depth, 848, 480, rs.format.z16, 30)
        config.enable_stream(rs.stream.color, 1280, 720, rs.format.rgb8, 30)

        print(f'start_stream (3)')
        self.profile = self.p.start(config)
        self.init_intrinsics()

        print(f'start_stream (4)')
        for _ in range(5):
            self.p.wait_for_frames()
        print(f'start_stream (5)')

    def stop_stream(self):
        print(f'stop_stream')
        if self.p is not None:
            try:
                self.p.stop()
            except RuntimeError as e:
                print(f"Warning: {e}")
            finally:
                self.p = None
                self.profile = None

    def restart_stream(self):
        self.stop_stream()
        self.start_stream()

    def get_device(self):
        context = rs.context()
        devices = context.query_devices()

        if len(devices) == 0:
            return None

        for device in devices:
            if self.camera.lower() in device.get_info(rs.camera_info.name).lower():
                return device
            # elif 'd415' in device.get_info(rs.camera_info.name).lower():
            #     return device
        return None

    def log_camera_settings(self):
        depth_sensor = self.device.first_depth_sensor()
        if depth_sensor.supports(rs.option.depth_units):
            depth_units = depth_sensor.get_option(rs.option.depth_units)
            print(f'Depth units: {depth_units}')
        else:
            print('Depth units not supported')

        depth_sensor = self.device.first_depth_sensor()
        depth_scale = depth_sensor.get_depth_scale()
        print(f'Depth scale: {depth_scale}')

    def set_post_processing(self):
        self.depth_to_disparity=rs.disparity_transform(True)
        self.disparity_to_depth=rs.disparity_transform(False)

        self.decimation=rs.decimation_filter()
        self.decimation.set_option(rs.option.filter_magnitude, 2)

        self.spatial=rs.spatial_filter()
        self.spatial.set_option(rs.option.filter_magnitude, 5)
        self.spatial.set_option(rs.option.filter_smooth_alpha, 1)
        self.spatial.set_option(rs.option.filter_smooth_delta, 50)
        self.spatial.set_option(rs.option.holes_fill, 3)

        self.temporal=rs.temporal_filter()
        self.temporal.set_option(rs.option.filter_smooth_alpha, 0.2)
        self.temporal.set_option(rs.option.filter_smooth_delta, 40)
        self.temporal.set_option(rs.option.holes_fill, 3)

        self.hole_filling=rs.hole_filling_filter()
        self.hole_filling.set_option(rs.option.holes_fill, 1)

    def load_json_params(self, filepath):
        self.device = self.get_device()
        advnc_mode = rs.rs400_advanced_mode(self.device)

        if not advnc_mode.is_enabled():
            print('Attempting to enable advanced mode...')
            advnc_mode.toggle_advanced_mode(True)
            time.sleep(5)

        print('Advanced mode is', 'enabled' if advnc_mode.is_enabled() else 'disabled')
        if advnc_mode.is_enabled():
            with open(filepath, 'r') as f:
                json_object = json.load(f)
            json_string = str(json_object).replace("'", '\"')
            advnc_mode.load_json(json_string)
        else:
            print(f'!!Warning!! Unable to load json configuration')

    def init_intrinsics(self, log=False):
        depth_intrinsics = self.profile.get_stream(rs.stream.depth).as_video_stream_profile().get_intrinsics()
        color_intrinsics = self.profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

        self.depth_intrinsics = {
            'width': depth_intrinsics.width,
            'height': depth_intrinsics.height,
            'ppx': depth_intrinsics.ppx,
            'ppy': depth_intrinsics.ppy,
            'fx': depth_intrinsics.fx,
            'fy': depth_intrinsics.fy,
            'coeffs': depth_intrinsics.coeffs
        }
        self.color_intrinsics = {
            'width': color_intrinsics.width,
            'height': color_intrinsics.height,
            'ppx': color_intrinsics.ppx,
            'ppy': color_intrinsics.ppy,
            'fx': color_intrinsics.fx,
            'fy': color_intrinsics.fy,
            'coeffs': color_intrinsics.coeffs
        }

        if log:
            print(f'depth_intrinsics: {self.depth_intrinsics}')
            print(f'color_intrinsics: {self.color_intrinsics}')

    def get_data(self, n=10, save=False):
        self.start_stream()
        
        for frame_idx in range(n):
            frames = self.p.wait_for_frames()
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()

            depth_frame = self.decimation.process(depth_frame)
            # depth_frame = self.depth_to_disparity.process(depth_frame)
            depth_frame = self.spatial.process(depth_frame)
            depth_frame = self.temporal.process(depth_frame)
            # depth_frame = self.disparity_to_depth.process(depth_frame)
            # # depth_frame = self.hole_filling.process(depth_frame) # can help fill some edges but sometimes it does way too much
        
        depth = np.asanyarray(depth_frame.get_data())
        depth_image = np.asanyarray((colorizer.colorize(depth_frame)).get_data())

        unfiltered_depth_frame = aligned_frames.get_depth_frame()
        unfiltered_depth = np.asanyarray(unfiltered_depth_frame.get_data())
        unfiltered_depth_image = np.asanyarray((colorizer.colorize(unfiltered_depth_frame)).get_data())

        color_frame = aligned_frames.get_color_frame()
        colors_original = np.asanyarray(color_frame.get_data())

        pc = rs.pointcloud()
        points = pc.calculate(depth_frame)
        vertices = np.asanyarray(points.get_vertices(3))

        #? convert depth to mm & resize colors to match depth.shape
        vertices *= 1000
        h, w, _ = vertices.shape
        colors = cv2.resize(colors_original, (w, h), interpolation=cv2.INTER_LINEAR)

        rgbd_data = RGBDData({
            'depth': depth,
            'depth_image': depth_image,
            'unfiltered_depth': unfiltered_depth,
            'unfiltered_depth_image': unfiltered_depth_image,
            'colors_original': colors_original,
            'colors': colors,
            'vertices': vertices,
            'camera': self.camera,
            'path_wout_timestamp': self.vp_data,
            'path_with_timestamp': self.vp_data + f'{self.camera}_{time.strftime("%Y-%m-%d_%H-%M-%S")}/',
            'depth_intrinsics': self.depth_intrinsics,
            'color_intrinsics': self.color_intrinsics
        })

        if save:
            rgbd_save_data(rgbd_data)

        self.stop_stream()

        return rgbd_data





from utils.img_processing import plt_imshow

if __name__ == '__main__':
    # d435 = D435(load_json='')
    d435 = D435()
    rgbd_data = d435.get_data(save=False)
    # print(rgbd_data.vertices.shape)
    # print(rgbd_data.colors_original.shape)
    # print(rgbd_data.colors.shape)

    # plt_imshow(rgbd_data.depth, rgbd_data.vertices[:,:,2])
    # plt_imshow(rgbd_data.vertices[:,:,0], rgbd_data.vertices[:,:,1])

    # rgbd_data = rgbd_read_data(folder_path='d435_2024-08-16_05-43-13')
    # plt_imshow(rgbd_data.colors, rgbd_data.vertices[:,:,0])




