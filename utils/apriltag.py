import os
import copy
import cv2
from pupil_apriltags import Detector
from utils.D435_rpi import D435, rgbd_read_data
from utils.target_transformation import *
import time
from rich import print


#~ global
TAG_ID_DATA = {
    0: {'tag_size_mm': 70, 'program': None, 'requires_fine': False},
    1: {'tag_size_mm': 120, 'program': 12, 'requires_fine': False, 'boundaries': {'x': [-1050, -900], 'y': [-210, 165], 'z': [-75, -40], 'rx': [-7.5, 7.5], 'ry': [-7.5, 7.5], 'rz': [84, 99]}},
    2: {'tag_size_mm': 120, 'program': 13, 'requires_fine': False, 'boundaries': {'x': [-1050, -900], 'y': [-210, 165], 'z': [-75, -40], 'rx': [-2.5, 2.5], 'ry': [-2.5, 2.5], 'rz': [88, 94]}},
    3: {'tag_size_mm': 120, 'program': 13, 'requires_fine': False, 'boundaries': {'x': [-1050, -900], 'y': [-295, 165], 'z': [-100, -40], 'rx': [-2.5, 2.5], 'ry': [-2.5, 2.5], 'rz': [88, 94]}},
    4: {'tag_size_mm': 120, 'program': None, 'requires_fine': False},
}

#~ helper functions
def cv2_show(img, title: str='Image'):
    cv2.imshow(title, img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


#~ detection
def detect_and_estimate_tags(img, camera_params, camera_distortion=np.zeros(5), show=False):
    # Initialize detector
    at_detector = Detector(
        families='tag36h11',
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.0,
        refine_edges=1,
        decode_sharpening=0.25,
        debug=0
    )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    draw_img = copy.deepcopy(img)

    #? detect AprilTags without pose estimation
    tags = at_detector.detect(gray, estimate_tag_pose=False)
    detections = []
    processed_tag_ids = set()  # Track processed tag IDs

    if tags:
        print(f'{len(tags)} AprilTag(s) detected.')
        for tag in tags:
            tag_id = tag.tag_id
            tag_info = TAG_ID_DATA.get(tag_id)
            if not tag_info:
                print(f"Tag ID {tag_id} is not registered. Skipping.")
                continue

            # Check if tag_id has already been processed
            if tag_id in processed_tag_ids:
                print(f"Duplicate Tag ID {tag_id} detected. Skipping.")
                continue

            tag_size_mm = tag_info['tag_size_mm']
            tag_size_meters = (0.8 * tag_size_mm) / 1000  # Convert to meters

            #? Re-estimate pose with the correct tag size
            pose_tags = at_detector.detect(
                gray,
                estimate_tag_pose=True,
                camera_params=camera_params,
                tag_size=tag_size_meters
            )

            for pose_tag in pose_tags:
                if pose_tag.tag_id == tag_id:
                    rot_vec, _ = cv2.Rodrigues(pose_tag.pose_R)
                    trans_vec = pose_tag.pose_t * 1000  # Convert to mm
                    pose = np.round(tform_2_pose(rt_2_tform(pose_tag.pose_R, trans_vec)), 3).tolist()
                    print(f'pose: {pose}')

                    tag_data = {
                        'id': pose_tag.tag_id,
                        'program': TAG_ID_DATA.get(pose_tag.tag_id, {}).get('program', None),
                        'requires_fine': TAG_ID_DATA.get(pose_tag.tag_id, {}).get('requires_fine', None),
                        # 'family': pose_tag.tag_family,
                        # 'center': pose_tag.center,
                        # 'corners': pose_tag.corners,
                        'decision_margin': round(pose_tag.decision_margin, 2),
                        'tag_size_mm': tag_size_mm,
                        'pose': pose,
                        # 'rot_vec': rot_vec,
                        # 'trans_vec': trans_vec,
                        # 'pose_err': pose_tag.pose_err,
                    }
                    detections.append(tag_data)

                    # Mark this tag_id as processed
                    processed_tag_ids.add(tag_id)

                    # Mark on draw img
                    corners = np.int32(pose_tag.corners)
                    for i in range(4):
                        cv2.circle(draw_img, tuple(corners[i]), 5, (255, 0, 0), 1)
                        cv2.line(draw_img, tuple(corners[i]), tuple(corners[(i + 1) % 4]), (0, 255, 0), 1)
                    cv2.circle(draw_img, tuple(np.int32(pose_tag.center)), 5, (255, 0, 0), 1)
                    
                    camera_matrix = np.array([[camera_params[0], 0, camera_params[2]],
                                                [0, camera_params[1], camera_params[3]],
                                                [0, 0, 1]])
                    draw_img = cv2.cvtColor(draw_img, cv2.COLOR_RGB2BGR)
                    cv2.drawFrameAxes(draw_img, camera_matrix, camera_distortion, rot_vec, trans_vec, tag_size_mm)
                    draw_img = cv2.cvtColor(draw_img, cv2.COLOR_BGR2RGB)

                    #? draw text
                    _text = str(tag_data['program'])
                    _font = cv2.FONT_HERSHEY_SIMPLEX
                    _font_scale = 0.9
                    _color = (255, 192, 203)
                    _thickness = 2
                    
                    _x = int(pose_tag.center[0] - tag_size_mm/2)
                    _y = int(pose_tag.center[1] - tag_size_mm/2)

                    cv2.putText(draw_img, _text, (_x, _y), _font, _font_scale, _color, _thickness, cv2.LINE_AA)

    else:
        print("No AprilTags detected.")

    if show:
        cv2_show(draw_img, "AprilTag Detections")

    return detections, draw_img




if __name__ == '__main__':
    d435 = D435()

    # fname = 'd435_2024-12-05_10-53-42'
    # rgbd_data = rgbd_read_data(folder_path=fname)
    rgbd_data = d435.get_data(save=False)

    img = rgbd_data.colors_original
    # cv2_show(img)

    #? detect apriltag frame(s)
    camera_params = (d435.color_intrinsics['fx'], d435.color_intrinsics['fy'], d435.color_intrinsics['ppx'], d435.color_intrinsics['ppy'])
    camera_distortion = np.array(d435.color_intrinsics['coeffs'])
    apriltags_wrt_camera = []

    detections, draw_img = detect_and_estimate_tags(img, camera_params, camera_distortion, show=True)
    print(detections)








