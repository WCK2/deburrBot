import threading
import os
import time
from PyQt5.QtCore import QThread, pyqtSignal
from utils.D435_rpi import D435, rgbd_read_data
from utils.config import settings, idata
from utils.memory import mem
from gui.workers.tpost import get_req
from utils.img_processing import rgbd_depth_filter


class TCamera(QThread):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.mythread = threading.Thread(target=self.__run)

    def __run(self):
        #? take pic
        try:
            d435 = D435()
            # d435 = D435(load_json='')

            if d435.camera_detected:
                rgbd_data = d435.get_data(save=True)
                rgbd_data, _ = rgbd_depth_filter(rgbd_data, 100, 1500)
                idata.set_rgbd(rgbd_data)
            elif settings.TESTING:
                rgbd_data = rgbd_read_data('d435_2024-09-19_09-25-47')
                rgbd_data, _ = rgbd_depth_filter(rgbd_data, 100, 1500)
                idata.set_rgbd(rgbd_data)
            else:
                print(f'!!WARNING!! No Camera Detected')
                return
        finally:
            d435.close()
        
        #? get robot data
        data = get_req(path='robot', data={'name': 'transformation_data'})
        if data is None:
            if not settings.TESTING:
                print(f'!!WARNING!! Unable to get transformation_data from the robot server')
                return
            data = {
                'frame': [-809.075, -11.325, -100.975, -0.180246, -0.0034, 91.08],
                'tool': [-139.39, 64.585, 199.93, -169.95, 0.288, -115.89],
                'pose': [190.32, -151.19, 832.05, 11.618, -15.506, -94.229],
                'camera_tool': [78.21, 73.4, 50.54, 15.29, -0.46, 150.04],
                'x_boundary_range': [-565, 565],
                'y_boundary_range': [-340, 345],
                'z_boundary_range': [-40, 60]
            }
        
        # print(f'transformation_data:\n{data}')
        idata.robot_frame = data['frame']
        idata.robot_tool = data['tool']
        idata.robot_pose = data['pose']
        idata.robot_camera_tool = data['camera_tool']
        idata.x_boundary_range = data['x_boundary_range']
        idata.y_boundary_range = data['y_boundary_range']
        idata.z_boundary_range = data['z_boundary_range']

        self.finished.emit()


    def run(self):
        if self.mythread.is_alive():
            print('Previous take_picture call is still running. No new therad will be started!')
            return
        self.mythread = threading.Thread(target=self.__run)
        self.mythread.start()

    def threadstatus(self):
        return self.mythread.is_alive()






if __name__=="__main__":
    thread_cam = TCamera()
    thread_cam.finished.connect(lambda:print("thread finished!!"))
    thread_cam.run()
    input("")