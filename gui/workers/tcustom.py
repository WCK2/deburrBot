import copy
import gzip
import numpy as np
import pickle
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal
from utils.config import idata, vp, settings
from utils.memory import mem
from utils.img_processing import *
from utils.target_transformation import get_vertex, TargetTransformer
from gui.workers.tpost import post_req_sync


class TCustom(QThread):
    set_finished = pyqtSignal()
    run_finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.image_is_set_flag = False
        self.target_pairs_post_status = False
        self.mythread = threading.Thread(target=self.__set)

    def __set(self):
        self.image_is_set_flag = False
        self.target_pairs_post_status = False
        self.image_is_set_flag = True
        self.set_finished.emit()

    def set(self):
        if self.mythread.is_alive():
            print('Previous set_image call is still running. No new thread will be started!')
            return
        self.mythread = threading.Thread(target=self.__set)
        self.mythread.start()

    def threadstatus(self):
        return self.mythread.is_alive()

    def ____run(self, input_points:list, input_labels:list):
        #! Generate custom target PAIR list
        try:
            self.target_pairs_post_status = False
            self.input_points = input_points
            self.input_labels = input_labels
            if not os.path.exists(idata.path_with_timestamp): os.makedirs(idata.path_with_timestamp)

            #* Step 1: draw pixel targets
            self.draw_img = copy.deepcopy(idata.colors)
            pixel_targets = self.input_points
            print(f'pixel_targets: {pixel_targets}')

            for i in range(len(pixel_targets)):
                cv2.circle(self.draw_img, pixel_targets[i], radius=4, color=(0, 255, 0), thickness=-1)
                if i < len(pixel_targets) - 1:
                    cv2.arrowedLine(
                        self.draw_img,
                        pixel_targets[i],
                        pixel_targets[i + 1],
                        color=(255, 0, 0),
                        thickness=2,
                        tipLength=0.2
                    )
            cv2.imwrite(idata.path_with_timestamp + 'tcustom_draw_img.jpg', cv2.cvtColor(self.draw_img, cv2.COLOR_RGB2BGR))

            coordinate_pairs = [[pixel_targets[i], pixel_targets[i + 1]] for i in range(len(pixel_targets) - 1)]
            print(f'coordinate_pairs: {coordinate_pairs}')

            #* Step 4: convert target pairs (pixel coords wrt image) --> vertices (wrt camera) --> robot targets (pose wrt robot frame and tool)
            camera_target_pairs = []
            for pair in coordinate_pairs:
                processed_pair = []
                invalid_vertex_flag = False # True when get_vertex has returned (0,0,0) - meaning the depth data for that coord was not found by the camera

                for coords in pair:
                    _vertex = get_vertex(idata.vertices, coords)
                    if np.array_equal(_vertex, [0, 0, 0]):
                        invalid_vertex_flag = True
                    # _pose = np.concatenate([_vertex, [0, 0, 0]])
                    _pose = np.concatenate([_vertex, [180, 0, 0]])
                    processed_pair.append(_pose)

                if not invalid_vertex_flag:
                    camera_target_pairs.append(processed_pair)

            camera_target_pairs = np.round(camera_target_pairs, 3)
            print('camera_target_pairs:\n' + '\n'.join(str(p) for p in camera_target_pairs) + '\n') ## log

            transformer = TargetTransformer(
                robot_frame=idata.robot_frame,
                robot_tool=idata.robot_tool,
                robot_pose=idata.robot_pose,
                robot_camera_tool=idata.robot_camera_tool
            )

            robot_target_pairs = []
            for pair in camera_target_pairs:
                processed_pair = []

                for pose in pair:
                    new_pose = transformer.transform(pose)
                    processed_pair.append(new_pose)

                robot_target_pairs.append(processed_pair)
            
            robot_target_pairs = np.round(robot_target_pairs, 3)
            print('robot_target_pairs:\n' + '\n'.join(str(p) for p in robot_target_pairs) + '\n') ## log

            #? filter targets outside of workspace boundary
            all_target_poses = np.array([pose for pair in robot_target_pairs for pose in pair])
            valid_x = (all_target_poses[:, 0] >= idata.x_boundary_range[0]) & (all_target_poses[:, 0] <= idata.x_boundary_range[1])
            valid_y = (all_target_poses[:, 1] >= idata.y_boundary_range[0]) & (all_target_poses[:, 1] <= idata.y_boundary_range[1])
            valid_z = (all_target_poses[:, 2] >= idata.z_boundary_range[0]) & (all_target_poses[:, 2] <= idata.z_boundary_range[1])
            valid_indices = valid_x & valid_y & valid_z

            valid_indices_pairs = valid_indices.reshape(-1, 2)
            valid_pairs = valid_indices_pairs.all(axis=1)

            valid_target_pairs = [robot_target_pairs[i] for i in range(len(robot_target_pairs)) if valid_pairs[i]]
            print('valid_target_pairs:\n' + '\n'.join(str(p) for p in valid_target_pairs) + '\n') ## log

            #* Step 5: post target_pairs
            tx_target_pairs = [[pose.tolist() for pose in pair] for pair in valid_target_pairs]
            print(f'tx_target_pairs: {tx_target_pairs}\n')
            if not tx_target_pairs:
                raise ValueError(f'tx_target_pairs is empty: {tx_target_pairs}')
            
            res = post_req_sync(path='mem', data={'name': 'generator1_target_pairs', 'value': tx_target_pairs})
            if isinstance(res, dict):
                if res.get('status') == 'success':
                    self.target_pairs_post_status = True
                else:
                    print(f'Request failed. Error: {res.get("error", "Unknown error")}')
            else:
                print('Received non-JSON response or error.')

            #? save
            data_log = {
                'input_points': self.input_points,
                'input_label': self.input_labels,
                'image': idata.colors,
                'vertices': idata.vertices,
                'mask': None,
                'coordinate_pairs': coordinate_pairs,
                'camera_target_pairs': camera_target_pairs,
                'robot_target_pairs': robot_target_pairs,
                'valid_target_pairs': valid_target_pairs,
                'robot_frame': idata.robot_frame,
                'robot_tool': idata.robot_tool,
                'robot_pose': idata.robot_pose,
                'robot_camera_tool': idata.robot_camera_tool
            }

            filename_log = idata.path_with_timestamp + f'tcustom_data_log_{time.strftime("%H-%M-%S")}.pkl.gz'
            with gzip.open(filename_log, 'wb') as f:
                pickle.dump(data_log, f)

            #? fin
            self.run_finished.emit()

        except Exception as e:
            print(f'!!Error!! {e}')
            return


    def run(self, input_points:list, input_labels:list):
        #! Generate custom consecutive target list
        try:
            self.target_pairs_post_status = False
            self.input_points = input_points
            self.input_labels = input_labels
            if not os.path.exists(idata.path_with_timestamp): os.makedirs(idata.path_with_timestamp)

            #* Step 1: draw pixel targets
            self.draw_img = copy.deepcopy(idata.colors)
            pixel_targets = self.input_points
            print(f'pixel_targets: {pixel_targets}')

            for i in range(len(pixel_targets)):
                cv2.circle(self.draw_img, pixel_targets[i], radius=4, color=(0, 255, 0), thickness=-1)
                if i < len(pixel_targets) - 1:
                    cv2.arrowedLine(
                        self.draw_img,
                        pixel_targets[i],
                        pixel_targets[i + 1],
                        color=(255, 0, 0),
                        thickness=2,
                        tipLength=0.2
                    )
            cv2.imwrite(idata.path_with_timestamp + 'tcustom_draw_img.jpg', cv2.cvtColor(self.draw_img, cv2.COLOR_RGB2BGR))

            coordinates = copy.deepcopy(pixel_targets)
            print(f'coordinates: {coordinates}')

            #* Step 4: convert pixel targets (pixel coords wrt image) --> vertices (wrt camera) --> robot targets (pose wrt robot frame and tool)
            camera_targets = []
            for coord in coordinates:
                _vertex = get_vertex(idata.vertices, coord)
                if np.array_equal(_vertex, [0, 0, 0]):
                    pass
                else:
                    _pose = np.concatenate([_vertex, [180, 0, 0]])
                    camera_targets.append(_pose)

            camera_targets = np.round(camera_targets, 3)
            print('camera_targets:\n' + '\n'.join(str(p) for p in camera_targets) + '\n') ## log

            transformer = TargetTransformer(
                robot_frame=idata.robot_frame,
                robot_tool=idata.robot_tool,
                robot_pose=idata.robot_pose,
                robot_camera_tool=idata.robot_camera_tool
            )

            robot_targets = []
            for pose in list(camera_targets):
                new_pose = transformer.transform(pose)
                robot_targets.append(new_pose)

            robot_targets = np.round(robot_targets, 3)
            print('robot_targets:\n' + '\n'.join(str(p) for p in robot_targets) + '\n') ## log

            #? filter targets outside of workspace boundary
            all_target_poses = np.array(robot_targets)
            valid_x = (all_target_poses[:, 0] >= idata.x_boundary_range[0]) & (all_target_poses[:, 0] <= idata.x_boundary_range[1])
            valid_y = (all_target_poses[:, 1] >= idata.y_boundary_range[0]) & (all_target_poses[:, 1] <= idata.y_boundary_range[1])
            valid_z = (all_target_poses[:, 2] >= idata.z_boundary_range[0]) & (all_target_poses[:, 2] <= idata.z_boundary_range[1])
            valid_indices = valid_x & valid_y & valid_z
            print(f'valid_indices: \n{valid_indices}\n')

            valid_targets = [robot_targets[i] for i in range(len(robot_targets)) if valid_indices[i]]
            print('valid_targets:\n' + '\n'.join(str(p) for p in valid_targets) + '\n') ## log

            #* Step 5: post target_pairs
            tx_targets = [[pose.tolist() for pose in pair] for pair in valid_targets]
            print(f'tx_targets: {tx_targets}\n')
            if not tx_targets:
                raise ValueError(f'tx_target_pairs is empty: {tx_targets}')
            
            res = post_req_sync(path='mem', data={'name': 'generator1_target_pairs', 'value': tx_targets})
            if isinstance(res, dict):
                if res.get('status') == 'success':
                    self.target_pairs_post_status = True
                else:
                    print(f'Request failed. Error: {res.get("error", "Unknown error")}')
            else:
                print('Received non-JSON response or error.')

            #? save
            data_log = {
                'input_points': self.input_points,
                'input_label': self.input_labels,
                'image': idata.colors,
                'vertices': idata.vertices,
                'mask': None,
                'coordinates': coordinates,
                'camera_targets': camera_targets,
                'robot_targets': robot_targets,
                'valid_targets': valid_targets,
                'robot_frame': idata.robot_frame,
                'robot_tool': idata.robot_tool,
                'robot_pose': idata.robot_pose,
                'robot_camera_tool': idata.robot_camera_tool
            }

            filename_log = idata.path_with_timestamp + f'tcustom_data_log_{time.strftime("%H-%M-%S")}.pkl.gz'
            with gzip.open(filename_log, 'wb') as f:
                pickle.dump(data_log, f)

            #? fin
            self.run_finished.emit()

        except ValueError as ve:
            print(f'!!Error!! {ve}')
            return



