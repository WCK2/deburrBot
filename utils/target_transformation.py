import numpy as np
from scipy.spatial.transform import Rotation
from utils.config import *


#~ homogeneous transformation matrices
def pose_2_tform(pose, isdeg=True):
    """
    Convert a pose in [x, y, z, rx, ry, rz] format to a homogeneous transformation matrix.
    rx, ry, rz are in degrees.
    """
    pose = np.asarray(pose)
    x, y, z, rx, ry, rz = pose
    translation = [x, y, z]
    rotation = Rotation.from_euler('xyz', [rx, ry, rz], degrees=isdeg).as_matrix()
    transform = np.eye(4)
    transform[:3, :3] = rotation
    transform[:3, 3] = translation
    return transform

def tform_2_pose(T, isdeg=True):
    """
    Convert a homogeneous transformation matrix to a pose in [x, y, z, rx, ry, rz] format.
    rx, ry, rz are in degrees.
    """
    x, y, z = T[:3, 3]

    R_matrix = T[:3, :3]
    rotation = Rotation.from_matrix(R_matrix)
    rx, ry, rz = rotation.as_euler('xyz', degrees=isdeg)
    
    return np.array([x, y, z, rx, ry, rz])

def inverse_tform(T):
    """
    Compute the inverse of a homogeneous transformation matrix.
    """
    R_inv = T[:3, :3].T
    t_inv = -R_inv @ T[:3, 3]
    T_inv = np.eye(4)
    T_inv[:3, :3] = R_inv
    T_inv[:3, 3] = t_inv
    return T_inv

def tform_2_rt(T):
    """
    Extract the rotation matrix (3,3) and translation vector (3,) from a homogeneous transformation matrix (4,4).
    """
    R = T[:3, :3]
    t = T[:3, 3]
    return R, t

def rt_2_tform(R, t):
    """
    Combine a rotation matrix (3,3) and a translation vector (3,) into a homogeneous transformation matrix (4,4).
    """
    transform = np.eye(4)
    transform[:3, :3] = R
    transform[:3, 3] = t.reshape(3)
    return transform


#~ 3D helpers
def get_vertex(vertices, coord, radius:int=5):
    """
    Calculate the average vertex position around a given coordinate.
    
    Parameters:
    vertices: array of vertices from the processed depth image (rgbd_data.vertices).
    coord: Tuple (x, y) representing the coordinate in the image (col, row).
    radius: The radius around the point to consider for averaging (default is 2).
    
    Returns:
    average_vertex: A tuple (x, y, z) representing the average vertex position.
    """
    col, row = coord  # x, y is treated as col, row

    vertex = vertices[row, col]
    if not np.array_equal(vertex, [0, 0, 0]):
        return vertex
    
    # Extract the region around the coordinate
    row_start = max(0, row - radius)
    row_end = min(vertices.shape[0], row + radius + 1)
    col_start = max(0, col - radius)
    col_end = min(vertices.shape[1], col + radius + 1)
    
    region = vertices[row_start:row_end, col_start:col_end]
    
    # Filter out invalid vertices
    valid_vertices = region[(region != [0, 0, 0]).all(axis=2)]
    
    if len(valid_vertices) == 0:
        print(f'!!WARNING!! Could not find any valid vertices at coord: {coord}, with radius = {radius}')
        return (0, 0, 0)
    
    # Calculate the average of the valid vertices
    average_vertex = valid_vertices.mean(axis=0)
    
    return average_vertex



class TargetTransformer():
    def __init__(self, robot_frame, robot_tool, robot_pose, robot_camera_tool) -> None:
        self.T_frame_2_base = pose_2_tform(robot_frame)
        self.T_tool_2_flange = pose_2_tform(robot_tool)
        self.T_tool_2_frame = pose_2_tform(robot_pose)
        self.T_camera_2_flange = pose_2_tform(robot_camera_tool)

    def transform(self, target_pose):
        T_object_2_camera = pose_2_tform(target_pose)

        T_object_2_flange = np.dot(self.T_camera_2_flange, T_object_2_camera)
        T_object_2_tool = np.dot(inverse_tform(self.T_tool_2_flange), T_object_2_flange)
        T_object_2_frame_wrt_tool = np.dot(self.T_tool_2_frame, T_object_2_tool)

        p_object_2_frame_wrt_tool = tform_2_pose(T_object_2_frame_wrt_tool).tolist()
        ## p_object_2_frame_wrt_tool[3:] = np.array([0, 0, 0])
        # print(f'p_object_2_frame_wrt_tool: {p_object_2_frame_wrt_tool}')

        return p_object_2_frame_wrt_tool










