from jaka.nos.jakabot import *
import keyboard
import datetime


ip_jaka = '192.168.69.60'
robot = jakabot(ip_jaka)
robot.init()
robot.servo_move_enable(False)
robot.set_collision_val(1)

#~ Helpers
def setup():
    # print(robot.get_frame())
    # print(robot.get_tool())
    # print(robot.get_tcp_pose())
    robot.set_frame([-809.075, -11.325, -100.975, -0.18, -0.0034, 91.08])
    # robot.set_tool([-133.368, 77.0, 200.0, -169.95, 0.288, -115.89])
    robot.set_tool([-98.008, 44.501, 199.967, -179.955, 0.288, -115.887])
    robot.waitmove()

def log(s):
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}]~ {s}")


class CONTROLLER:
    s_mm = 1.0
    vel = 5
    def __init__(self) -> None:
        movement_hotkeys = {
            'a': [-1, 0, 0, 0, 0, 0],
            'd': [1, 0, 0, 0, 0, 0],
            'w': [0, 1, 0, 0, 0, 0],
            's': [0, -1, 0, 0, 0, 0],
            'r': [0, 0, 1, 0, 0, 0],
            'f': [0, 0, -1, 0, 0, 0],
        }
        for key, action in movement_hotkeys.items():
            if isinstance(action,list):
                keyboard.add_hotkey(key, lambda a=action: self.incmove(a))
            else:
                print(f'did not register: ({key})')

        keyboard.add_hotkey('space', lambda: log(f'joints: {robot.get_joints()}'))
        keyboard.add_hotkey('j', lambda: log(f'joints: {robot.get_joints()}'))
        keyboard.add_hotkey('p', lambda: log(f'joints: {robot.get_tcp_pose()}'))

        keyboard.add_hotkey('v', lambda: self.change_vel())
        keyboard.add_hotkey('z', lambda: self.change_mm(0))

        keyboard.wait('q')

    def change_mm(self, n):
        if n==0:
            rr=input('  >> Enter new move distance: ')
            try:
                n=float(rr)
                self.s_mm=n
            except: pass
        else:
            self.s_mm+=n
        log(f's_mm={self.s_mm}')

    def change_vel(self):
        rr=input('  >> Enter new velocity: ')
        try:
            n=float(rr)
            self.vel=n
        except: pass
        log(f'vel={self.vel}')

    def incmove(self, p):
        if not (isinstance(p, list) and len(p) == 6):
            return
        p=[element*self.s_mm for element in p]
        log(f'movel({p}, ...)')
        robot.movel(p, move_mode=1, speed=self.vel)
        robot.waitmove()






if __name__=="__main__":
    setup()
    ctrl=CONTROLLER()

    print('end')
    
