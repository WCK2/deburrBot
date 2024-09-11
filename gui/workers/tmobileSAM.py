import copy
import gzip
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

        masked_depth = np.zeros_like(idata.depth, dtype=idata.depth.dtype)
        masked_depth[mask] = idata.depth[mask]

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

        pixel_width = origin[2] / fx
        pixel_height = origin[2] / fy
        # print(f'pixel_width (x): {pixel_width} mm')
        # print(f'pixel_height (y): {pixel_height} mm')

        tool_x_diameter_mm = 20
        tool_x_diameter_pixels = int(tool_x_diameter_mm / pixel_width)
        print(f'tool_x_diameter_pixels: {tool_x_diameter_pixels}')

        coordinate_pairs, self.draw_img = top_down_stripes(roi_mask, self.draw_img, tool_pixel_diameter=tool_x_diameter_pixels)
        print('coordinate_pairs:\n' + '\n'.join(str(p) for p in coordinate_pairs) + '\n') ## log
        cv2.imwrite(idata.path_with_timestamp + 'draw_img_step3.jpg', cv2.cvtColor(self.draw_img, cv2.COLOR_RGB2BGR))

        #* Step 4: convert target pairs (pixel coords wrt image) --> vertices (wrt camera) --> robot targets (pose wrt robot frame and tool)
        camera_target_pairs = []
        for pair in coordinate_pairs:
            processed_pair = []
            invalid_vertex_flag = False # True when get_vertex has returned (0,0,0) - meaning the depth data for that coord was not found by the camera

            for coords in pair:
                _vertex = get_vertex(idata.vertices, coords)
                if _vertex == (0, 0, 0):
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

        self.robot_target_pairs = []
        for pair in camera_target_pairs:
            processed_pair = []

            for pose in pair:
                new_pose = transformer.transform(pose)
                processed_pair.append(new_pose)
            
            self.robot_target_pairs.append(processed_pair)
        
        self.robot_target_pairs = np.round(self.robot_target_pairs, 3).tolist()
        print('robot_target_pairs:\n' + '\n'.join(str(p) for p in self.robot_target_pairs) + '\n') ## log

        #* Step 5: post target_pairs
        res = post_req_sync(path='mem', data={'name': 'generator1_target_pairs', 'value': self.robot_target_pairs})
        if isinstance(res, dict):
            if res.get('status') == 'success':
                self.target_pairs_post_status = True
            else:
                print(f'Request failed. Error: {res.get("error", "Unknown error")}')
        else:
            print('Received non-JSON response or error.')

        #? save
        # self.save_results()
        # np.save(idata.path_with_timestamp + 'idata_vertices.npy', idata.vertices)

        # depth_min = np.min(idata.depth)
        # depth_max = np.max(idata.depth)
        # normalized_depth = (idata.depth - depth_min) / (depth_max - depth_min) * 255
        # normalized_depth_image = normalized_depth.astype(np.uint8)
        # cv2.imwrite(idata.path_with_timestamp + 'normalized_depth_image.jpg', normalized_depth_image)

        data_log = {
            'input_points': self.input_points,
            'input_label': self.input_labels,
            'image': idata.colors,
            'mask': mask,
            'coordinate_pairs': coordinate_pairs,
            'camera_target_pairs': camera_target_pairs,
            'robot_target_pairs': self.robot_target_pairs
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