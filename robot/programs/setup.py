from rdk.nos.willrdk import *
import math


MAKE = True


#~ Speeds (linear_velocity, angular_velocity, linear_acceleration, angular_acceleration)
slow_speeds = 30, 15, 200, 5
fast_speeds = 75, 25, 125, 15
# fast_speeds = 250, 60, 125, 40


FAST = 0
SLOW = 1
FASTAF = 2
SLOWAF = 3


robot = rdk.Item("jaka12")
robot.setSlowSpeeds(*slow_speeds)
robot.setFastSpeeds(*fast_speeds)


rdk.Command('Trace', 'Off')
rdk.Command('Trace', 'Reset')


class JTARS:
    def __init__(self):
        self.joint_folder = rdk.Item('Joints')

        self.home_joints = self.joint_folder.findChild('home_joints')
        self.picture_joints = self.joint_folder.findChild('picture_joints')

jtars = JTARS()




