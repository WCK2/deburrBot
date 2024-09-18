import threading
import os
import time
from PyQt5.QtCore import QThread, pyqtSignal
from utils.D435_rpi import D435, rgbd_read_data
from utils.config import settings, idata
from utils.memory import mem
from gui.workers.tpost import get_req


class TCamera(QThread):
    finished = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.mythread = threading.Thread(target=self.__run)

    def __run(self):
        #? take pic
        if settings.TESTING:
            d435 = D435(load_json='')
        else:
            d435 = D435()

        if d435.camera_detected:
            rgbd_data = d435.get_data(save=True)
            idata.set_rgbd(rgbd_data)
            d435.close()
        elif settings.TESTING:
            rgbd_data = rgbd_read_data('d435_2024-09-17_10-40-24')
            idata.set_rgbd(rgbd_data)
        else:
            print(f'!!WARNING!! No Camera Detected')
            return
        
        #? get robot data
        data = get_req(path='robot', data={'name': 'transformation_data'})
        if data is None:
            if not settings.TESTING:
                print(f'!!WARNING!! Unable to get transformation_data from the robot server')
                return
            data = {
                'frame': [-809.075, -11.325, -100.975, -0.180246, -0.0034, 91.08],
                'tool': [-139.39, 64.585, 199.93, -169.95, 0.288, -115.89],
                'pose': [-69.134, -299.98, 441.363, 11.497, -15.384, -94.289],
                'camera_tool': [78.21, 73.4, 50.54, 15.29, -0.46, 150.04]
            }
        
        print(f'transformation_data:\n{data}')
        idata.robot_frame = data['frame']
        idata.robot_tool = data['tool']
        idata.robot_pose = data['pose']
        idata.robot_camera_tool = data['camera_tool']

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