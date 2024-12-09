import os
import time
import sys
import datetime
import json
import cv2
import numpy as np
import pickle
from utils.D435_rpi import D435, rgbd_read_data
from utils.img_processing import plt_imshow




if __name__ == '__main__':
    # # d435 = D435(load_json='')
    # d435 = D435()
    # rgbd_data = d435.get_data(save=True)

    rgbd_data = rgbd_read_data(folder_path='d435_2024-09-06_08-08-24')
    plt_imshow(rgbd_data.colors, rgbd_data.vertices[:,:,2])
    plt_imshow(rgbd_data.vertices[:,:,0], rgbd_data.vertices[:,:,2])



