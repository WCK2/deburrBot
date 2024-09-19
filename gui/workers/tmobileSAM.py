import copy
import gzip
import numpy as np
import pickle
import threading
import time
from PyQt5.QtCore import QThread, pyqtSignal
from assets.models.mobile_sam.config import *
from utils.config import idata, vp, settings
from utils.memory import mem
from utils.img_processing import *
from utils.target_transformation import get_vertex, TargetTransformer
from gui.workers.tpost import post_req_sync


class TMobileSAM(QThread):
    set_finished = pyqtSignal()
    run_finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.image_is_set_flag = False
        self.target_pairs_post_status = False
        SAM = sam_model_registry[MODEL](checkpoint=CHECKPOINT)
        SAM.to(device=DEVICE)
        self.sam = SamPredictor(SAM)
        self.mythread = threading.Thread(target=self.__set)

    def __set(self):
        self.image_is_set_flag = False
        self.target_pairs_post_status = False
        self.sam.set_image(idata.colors)
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

    def run(self, input_points:list, input_labels:list):
        self.target_pairs_post_status = False
        self.input_points = input_points
        self.input_labels = input_labels
        masks, _, _ = self.sam.predict(
            point_coords = np.asarray(self.input_points),
            point_labels = np.asarray(self.input_labels),
            multimask_output = False,
        )
        if not os.path.exists(idata.path_with_timestamp): os.makedirs(idata.path_with_timestamp)

        #* Step 1: object mask
        mask = masks[0]
        roi_mask = copy.deepcopy(mask)
        cv2.imwrite(idata.path_with_timestamp + 'roi_mask_step1.jpg', roi_mask.astype(np.uint8) * 255)

        self.masked_img = apply_mask(idata.colors, mask.copy())
        self.draw_img = self.masked_img.copy()
        self.obj_bw_img = copy.deepcopy(idata.colors)
        self.obj_bw_img[..., :3] = np.array([255,255,255], dtype=np.uint8) * mask.copy()[..., None]

        cv2.imwrite(idata.path_with_timestamp + 'colors.jpg', cv2.cvtColor(idata.colors, cv2.COLOR_RGB2BGR))
        cv2.imwrite(idata.path_with_timestamp + 'masked_img.jpg', cv2.cvtColor(self.masked_img, cv2.COLOR_RGB2BGR))
        cv2.imwrite(idata.path_with_timestamp + 'obj_bw_img.jpg', self.obj_bw_img)

        masked_vertices = copy.deepcopy(idata.vertices)
        masked_vertices[~mask] = [0, 0, 0]
        flattened_vertices = masked_vertices.reshape(-1, 3)
        unique_vertices = np.unique(flattened_vertices, axis=0)

        origin, a, b, c, d = fit_plane(unique_vertices)
        # print(f'origin: {origin}')
        # plot_points_and_plane(unique_vertices, origin, a, b, c, d)

        #* Step 2: obstacle mask
        # if settings.avoid_obstacles:
        if False:
            z_offsets = calculate_z_offset(idata.vertices, a, b, c, d) # offset wrt calculated ocject origin

            upper_threshold = 75
            lower_threshold = 10
            obstacle_mask = (z_offsets > lower_threshold) & (z_offsets < upper_threshold)
            obstacle_mask[idata.depth == 0] = False
            cv2.imwrite(idata.path_with_timestamp + f'obstacle_mask_{lower_threshold}_{upper_threshold}.jpg', obstacle_mask.astype(np.uint8) * 255)

            padded_obstacle_mask = apply_tool_padding_to_obstacles(obstacle_mask, idata.vertices, idata.path_with_timestamp)
            cv2.imwrite(idata.path_with_timestamp + 'padded_obstacle_mask.jpg', padded_obstacle_mask.astype(np.uint8) * 255)

            combined_mask = np.logical_and(roi_mask, padded_obstacle_mask)
            roi_mask[combined_mask] = 0
            self.draw_img[combined_mask] = [255, 0, 0]
            cv2.imwrite(idata.path_with_timestamp + 'roi_mask_step2.jpg', roi_mask.astype(np.uint8) * 255)
            cv2.imwrite(idata.path_with_timestamp + 'draw_img_step2.jpg', cv2.cvtColor(self.draw_img, cv2.COLOR_RGB2BGR))

        #* Step 3: generate target path(s)
        _fx = idata.color_intrinsics['fx']
        _fy = idata.color_intrinsics['fy']
        fx = _fx * (roi_mask.shape[1] / idata.color_intrinsics['width'])
        fy = _fy * (roi_mask.shape[0] / idata.color_intrinsics['height'])

        width_mm_per_pixel = origin[2] / fx
        height_mm_per_pixel = origin[2] / fy
        # print(f'width mm per pixel (x): {width_mm_per_pixel} mm')
        # print(f'height mm per pixel (y): {height_mm_per_pixel} mm')

        tool_x_diameter_mm = 20
        tool_x_diameter_pixels = int(tool_x_diameter_mm / width_mm_per_pixel)
        # print(f'tool_x_diameter_pixels: {tool_x_diameter_pixels}')

        coordinate_pairs, self.draw_img = top_down_stripes(roi_mask, self.draw_img, tool_x_diameter_pixels, width_mm_per_pixel, height_mm_per_pixel, min_keep_distance=10)
        # print('coordinate_pairs:\n' + '\n'.join(str(p) for p in coordinate_pairs) + '\n') ## log
        cv2.imwrite(idata.path_with_timestamp + 'draw_img_step3.jpg', cv2.cvtColor(self.draw_img, cv2.COLOR_RGB2BGR))

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
            'mask': mask,
            'coordinate_pairs': coordinate_pairs,
            'camera_target_pairs': camera_target_pairs,
            'robot_target_pairs': robot_target_pairs,
            'valid_target_pairs': valid_target_pairs,
            'robot_frame': idata.robot_frame,
            'robot_tool': idata.robot_tool,
            'robot_pose': idata.robot_pose,
            'robot_camera_tool': idata.robot_camera_tool
        }

        filename_log = idata.path_with_timestamp + f'tmobileSAM_data_log_{time.strftime("%H-%M-%S")}.pkl.gz'
        with gzip.open(filename_log, 'wb') as f:
            pickle.dump(data_log, f)
        

        #? fin
        self.run_finished.emit()





if __name__=="__main__":
    thread_sam=TMobileSAM()
    # thread_sam.finished.connect(lambda:print("thread finished!!"))
    # thread_sam.run()
    input("enter to end")