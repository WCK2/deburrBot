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
            rgbd_data = rgbd_read_data('d435_2024-08-22_14-22-56')
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
                'frame': [-809.075, -11.325, -100.975, -0.18, 0.01, 95.34],
                'tool': [-133.368, 77.0, 200.0, -170.0, 0.0, -120.0],
                'pose': [186.501, -154.541, 177.739, 10, -11.25, -90],
                'camera_tool': [81.943, 76.054, 48.418, 15.16, -0.332, 149.98]
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