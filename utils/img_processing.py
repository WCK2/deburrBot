import os
import copy
import math
import numpy as np
import cv2
import matplotlib.patches as patches
import matplotlib.pyplot as plt
# from mpl_toolkits.mplot3d import Axes3D
from sklearn.decomposition import PCA


#~ preprocessing
def rgbd_depth_filter(rgbd_data, min=None, max=None):
    if min is None: min = np.min(rgbd_data.depth)
    if max is None: max = np.max(rgbd_data.depth)

    filtered_image = np.full(rgbd_data.depth.shape, 127, dtype=np.uint8)

    filtered_image[rgbd_data.depth < min] = 0
    filtered_image[rgbd_data.depth > max] = 255

    rgbd_data.depth[rgbd_data.depth < min] = 0
    rgbd_data.depth[rgbd_data.depth > max] = 0

    rgbd_data.vertices[rgbd_data.vertices[:, :, 2] < min] = [0, 0, 0]
    rgbd_data.vertices[rgbd_data.vertices[:, :, 2] > max] = [0, 0, 0]

    return rgbd_data, filtered_image


#~ point/path generations
def get_bbox(m, scale=1.0):
    rows = np.any(m, axis=1)
    cols = np.any(m, axis=0)
    rmin, rmax = np.where(rows)[0][[0, -1]]
    cmin, cmax = np.where(cols)[0][[0, -1]]

    scaling_factor=(1/scale)

    x=int(cmin*scaling_factor)
    y=int(rmin*scaling_factor)
    w=int((cmax-cmin)*scaling_factor)
    h=int((rmax-rmin)*scaling_factor)
    return [x,y,w,h]

def get_border_targets(img):
    """ Return a list of coordinates (pixels) that roughly follow the border of the masked object """
    if isinstance(img,str): img=cv2.imread(img)
    gray=cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred=cv2.GaussianBlur(gray, (5, 5), 0)
    edges=cv2.Canny(blurred, 0, 255)

    kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    edges=cv2.dilate(edges, kernel, iterations=1)
    edges=cv2.erode(edges, kernel, iterations=1)

    contours, _=cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour=max(contours, key=cv2.contourArea)
    cv2.drawContours(img, [largest_contour], -1, (0, 255, 0), 2)

    #? Approximate contour w polygon
    epsilon=0.01*cv2.arcLength(largest_contour, True)
    approximation=cv2.approxPolyDP(largest_contour, epsilon, True)
    cv2.drawContours(img, [approximation], 0, (255, 0, 255), 2)

    #? Get points from contour
    num_points=approximation.shape[0]
    x_coords=approximation[:, 0, 0]
    y_coords=approximation[:, 0, 1]
    tars=[[int(x_coords[i]), int(y_coords[i])] for i in range(num_points)]

    radius=5
    color=(0,0,255)
    for t in tars:
        cv2.circle(img, (t[0],t[1]), radius, color, -1)

    return  img, tars

def get_inner_targets(img, d=40, LOG=False):
    r=int(d/2)
    dir=1
    color=(0,255,0)
    thickness=2
    arrow_tip_length=0.05

    true_indices=np.where(img)
    first_true_row=np.min(true_indices[0])
    last_true_row=np.max(true_indices[0])
    diff=last_true_row-first_true_row
    first_row_offset=first_true_row+int((diff%r)/2)
    if LOG: print(f'first true row: {first_true_row}\nlast true row: {last_true_row}\ndiff: {diff}\nfirst_row_offset: {first_row_offset}')

    img_striped=img.copy()
    stripe=np.zeros(img.shape, dtype=bool)
    stripe[first_row_offset::r,:]=True

    img_striped = np.logical_and(stripe, img_striped)
    # if LOG: show(img_striped)

    target_pairs=[]
    dir=1
    for row in range(img_striped.shape[0]):
        if dir>0: line_indices = np.where(img_striped[row])[0]
        else: line_indices = np.where(img_striped[row])[0][::-1]

        if len(line_indices) > 0:
            if LOG: print(f'\n{"-"*100}\n ROW: {row}, (dir={dir}) \n{"-"*100}')

            if dir>0:
                gaps = np.where(np.diff(line_indices) > r)[0]
                segments = np.split(line_indices, gaps + 1)
            else:
                gaps = np.where(np.diff(line_indices) < -r)[0]
                segments = np.split(line_indices, gaps + 1)

            if LOG: print(f'gaps: {gaps}\nlen(segments): {len(segments)}\nsegments: {segments}')
            for line in segments:
                target_pairs.append([[int(line[0]), row], [int(line[-1]), row]])
                cv2.arrowedLine(img, (target_pairs[-1][0][0],target_pairs[-1][0][1]), (target_pairs[-1][1][0],target_pairs[-1][1][1]), color, thickness, tipLength=arrow_tip_length)

            dir=dir*-1

    if LOG: print(f'\ntarget_pairs: {target_pairs}\n')
    return img, target_pairs


#~ visualization
def cv2_show(img):
    cv2.imshow('Image', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def plt_imshow(img1, img2=None):
    """
    Display one or two images using Matplotlib's plt.subplot.
    Shows a colorbar for each image.
    
    Args:
        img1: The first image to display.
        img2: The second image to display (optional).
    """
    if img2 is None:
        # Only one image to display
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        im1 = ax.imshow(img1)
        ax.set_title('Image 1')
        plt.colorbar(im1, ax=ax)
    else:
        # Two images to display
        fig, axs = plt.subplots(1, 2, figsize=(16, 8))
        im1 = axs[0].imshow(img1)
        axs[0].set_title('Image 1')
        plt.colorbar(im1, ax=axs[0])
        
        im2 = axs[1].imshow(img2)
        axs[1].set_title('Image 2')
        plt.colorbar(im2, ax=axs[1])
    
    plt.show()

def rgbd_imshow(**kwargs):
    num_images=len(kwargs)
    num_rows=(num_images+1)//2
    fig,axes=plt.subplots(num_rows, 2, figsize=(10, 5*num_rows))

    for i, (var_name, var_value) in enumerate(kwargs.items()):
        row_idx=i//2
        col_idx=i%2
        if num_rows>1: ax=axes[row_idx, col_idx]
        else: ax=axes[col_idx]
        
        cb=ax.imshow(var_value)
        plt.colorbar(cb,ax=ax)
        ax.set_title(var_name)
        ax.axis('off')
    
    mngr = plt.get_current_fig_manager()
    # mngr.window.wm_geometry('+0+0')
    try:
        mngr.window.setGeometry(0, 0, fig.get_figwidth() * 100, fig.get_figheight() * 100)
    except AttributeError:
        pass  # Ignore if setGeometry isn't available (e.g., on non-GUI backends)

    plt.tight_layout()
    plt.show()

def apply_mask(image, mask, color=(173, 216, 230)):
    masked_image = image.copy()
    masked_image[mask != 0] = color
    return masked_image

def draw_border_targets(img, tars):
    radius=5
    thickness=2
    color=(0,255,0)

    for c,[x,y] in enumerate(tars):
        cv2.circle(img, (x,y), radius, color, -1)
        if c==len(tars)-1: cv2.line(img, (x,y), (tars[0][0],tars[0][1]), color, thickness)
        else: cv2.line(img, (x,y), (tars[c+1][0],tars[c+1][1]), color, thickness)

    return  img

def draw_inner_targets(img, tars):
    thickness=2
    color=(255,165,0)

    for i in range(len(tars)):
        cv2.arrowedLine(img, (tars[i][0][0],tars[i][0][1]), (tars[i][1][0],tars[i][1][1]), color, thickness)

    return  img


def fit_plane(points):
    """
    Fit a plane to a set of 3D points.
    
    Args:
    points (numpy.ndarray): A Nx3 array of 3D points.

    Returns:
    tuple: Coefficients (a, b, c, d) of the plane equation ax + by + cz + d = 0.
    """
    origin = np.mean(points, axis=0)

    # Extract x, y, z coordinates from the points
    x = points[:, 0]
    y = points[:, 1]
    z = points[:, 2]
    
    # Create the A matrix and b vector for the linear system
    A = np.c_[x, y, np.ones(x.shape)]
    b = z
    
    # Solve the linear system using least squares method
    coeffs, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    a, b, d = coeffs
    c = -1  # Because we solve ax + by + cz = d

    return origin, a, b, c, d

def plot_points_and_plane(points, origin, a, b, c, d):
    """
    Plot the 3D points and the fitted plane.
    
    Args:
    points (numpy.ndarray): A Nx3 array of 3D points.
    a, b, c, d (float): Coefficients of the plane equation ax + by + cz + d = 0.
    x_vector (numpy.ndarray): X direction vector to plot.
    y_vector (numpy.ndarray): Y direction vector to plot.
    plane_normal (numpy.ndarray): Normal vector of the plane.
    """
    # Create a grid of points
    xx, yy = np.meshgrid(np.linspace(np.min(points[:, 0]), np.max(points[:, 0]), 10),
                         np.linspace(np.min(points[:, 1]), np.max(points[:, 1]), 10))
    zz = (-a * xx - b * yy - d) / c

    # Plotting
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], color='r', label='Points')

    # Plot the plane
    ax.plot_surface(xx, yy, zz, alpha=0.5, rstride=100, cstride=100)

    # Plot new axes
    axis_length = 200  # Length of the axes vectors
    ax.quiver(origin[0], origin[1], origin[2], axis_length, 0, 0, color='r', label='X-axis')
    ax.quiver(origin[0], origin[1], origin[2], 0, axis_length, 0, color='g', label='Y-axis')
    ax.quiver(origin[0], origin[1], origin[2], 0, 0, axis_length, color='b', label='Z-axis')

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title('3D Points and Fitted Plane')
    plt.legend()
    plt.show()

def calculate_z_offset(vertices, a, b, c, d):
    """
    Calculate the z-offset of each point from the plane defined by ax + by + cz + d = 0.
    
    Args:
    vertices (numpy.ndarray): A Nx3 array of 3D points.
    a, b, c, d (float): Coefficients of the plane equation.

    Returns:
    numpy.ndarray: A 2D array of z-offsets.
    """
    x = vertices[:, :, 0]
    y = vertices[:, :, 1]
    z = vertices[:, :, 2]
    
    # Calculate the z-offset for each point
    z_offset = (a * x + b * y + c * z + d) / np.sqrt(a**2 + b**2 + c**2)
    
    return z_offset

def apply_tool_padding_to_obstacles(obstacle_mask, vertices, folder):
    obstacle_img = obstacle_mask.astype(np.uint8) * 255
    final_obstacle_mask = np.zeros_like(obstacle_mask, dtype=obstacle_mask.dtype)
    img = cv2.GaussianBlur(obstacle_img, (5, 5), 0)
    img = cv2.morphologyEx(img, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    img = cv2.Canny(img, 30, 200)
    contours, _ = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    x_offset = 57.5
    negative_y_offset = 200
    positive_y_offset = 20

    for i, contour in enumerate(contours):
        area = cv2.contourArea(contour)
        if area > 50:
            # print(f'contour: {i}, area: {area}')
            contour_img = np.zeros_like(obstacle_img, dtype=np.uint8)
            cv2.drawContours(contour_img, [contour], -1, (255,255,255), thickness=cv2.FILLED)
            # plt_imshow(contour_img)
            contour_mask = contour_img == 255
            # plt_imshow(contour_mask.astype(np.uint8)*255)

            contour_vertices = copy.deepcopy(vertices)
            contour_vertices[~contour_mask] = [0,0,0]
            flattened_vertices = contour_vertices.reshape(-1, 3)
            unique_vertices = np.unique(flattened_vertices, axis=0)
            unique_vertices = unique_vertices[~np.all(unique_vertices == [0, 0, 0], axis=1)]
            
            x_average = np.mean(unique_vertices[:, 0])
            y_average = np.mean(unique_vertices[:, 1])
            z_average = np.mean(unique_vertices[:, 2])
            # print(f' x_average: {x_average} \n y_average: {y_average} \n z_average: {z_average}')

            x_min, x_max = np.min(unique_vertices[:, 0]), np.max(unique_vertices[:, 0])
            y_min, y_max = np.min(unique_vertices[:, 1]), np.max(unique_vertices[:, 1])
            # print(f' x_min: {x_min}, x_max: {x_max}')
            # print(f' y_min: {y_min}, y_max: {y_max}')

            x_range = (x_min - x_offset, x_max + x_offset)
            y_range = (y_min - negative_y_offset, y_max + positive_y_offset)
            # print(f' x_range: {x_range} \n y_range: {y_range}')

            x_vertices = vertices[:, :, 0]
            y_vertices = vertices[:, :, 1]
            x_mask = (x_vertices >= x_range[0]) & (x_vertices <= x_range[1]) & (x_vertices != 0)
            y_mask = (y_vertices >= y_range[0]) & (y_vertices <= y_range[1]) & (y_vertices != 0)
            xy_contour_mask = x_mask & y_mask

            xy_contour_mask_uint8 = xy_contour_mask.astype(np.uint8) * 255
            xy_contour_img = cv2.morphologyEx(xy_contour_mask_uint8, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8), iterations=3)
            # plt_imshow(xy_contour_img)
            cv2.imwrite(folder + f'xy_contour_img_{i}.jpg', xy_contour_img)
            xy_contour_mask = xy_contour_img.astype(bool)

            final_obstacle_mask = final_obstacle_mask | xy_contour_mask

    final_obstacle_img = final_obstacle_mask.astype(np.uint8) * 255
    cv2.imwrite(folder + f'final_obstacle_img.jpg', final_obstacle_img)

    return final_obstacle_mask


def top_down_stripes(roi_mask, draw_img, tool_pixel_diameter, width_mm_per_pixel, height_mm_per_pixel, min_keep_distance=10):
    # print(roi_mask.shape, roi_mask.dtype)
    d = int(tool_pixel_diameter)
    color = (0, 255, 0)
    thickness = 2
    arrow_tip_length = 0.05

    true_indices = np.where(roi_mask)
    first_true_col = np.min(true_indices[1])
    last_true_col = np.max(true_indices[1])
    diff = last_true_col - first_true_col
    first_col_offset = first_true_col + int((diff % d) / 2)
    # print(f' - first true col: {first_true_col}\n - last true col: {last_true_col}\n - diff: {diff}\n - first_col_offset: {first_col_offset}')

    img_striped = roi_mask.copy()
    stripe = np.zeros(roi_mask.shape, dtype=bool)
    stripe[:, first_col_offset::d] = True

    img_striped = np.logical_and(stripe, img_striped)
    # plt_imshow(img_striped)

    coordinate_pairs = []
    for col in range(img_striped.shape[1]):
        line_indices = np.where(img_striped[:, col])[0]

        if len(line_indices) > 0:
            gaps = np.where(np.diff(line_indices) > d)[0]
            segments = np.split(line_indices, gaps + 1)

            for line in segments:
                t_start = [col, int(line[0])]
                t_end = [col, int(line[-1])]

                delta_x_pixels = t_end[0] - t_start[0]
                delta_y_pixels = t_end[1] - t_start[1]

                delta_x_mm = delta_x_pixels * width_mm_per_pixel
                delta_y_mm = delta_y_pixels * height_mm_per_pixel

                distance_mm = math.sqrt(delta_x_mm**2 + delta_y_mm**2)
                # print(f'distance_mm: {distance_mm}')

                if distance_mm > min_keep_distance:
                    coordinate_pairs.append([t_start, t_end])
                    cv2.arrowedLine(draw_img, (coordinate_pairs[-1][0][0], coordinate_pairs[-1][0][1]), (coordinate_pairs[-1][1][0], coordinate_pairs[-1][1][1]), color, thickness, tipLength=arrow_tip_length)
                else:
                    print(f'skipping coordinate_pair {t_start}, {t_end} with distance_mm of {distance_mm} mm')

    # print(f'\ncoordinate_pairs: {coordinate_pairs}\n')
    # plt_imshow(draw_img)
    return coordinate_pairs, draw_img




if __name__=="__main__":
    get_border_targets(os.getcwd() + '/img_obj_bw.jpg')







