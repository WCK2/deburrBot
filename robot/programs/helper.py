from setup import *
import numpy as np
import copy


#~ RoboDK Stuff
def isClass(c):
    """Returns true if argument is a class"""
    class C():pass
    return type(c)==type(C)

def findChild(self,name,recursive=True):
    for child in self.Childs():
        if child.Name() == name:
            return child
        if recursive:
            if len(child.Childs())>0:
                r = child.findChild(name, recursive)
                if r: return r
Item.findChild = findChild

def GetTargetItems(frame):
    return [t for t in frame.Childs() if t.Type()==6]

def GetTargetMats(frame):
    return [t.Pose() for t in frame.Childs() if t.Type()==6]

def GetTargetNames(frame):
    return [t.Name() for t in frame.Childs() if t.Type()==6]

def GetIK(target_pose, ref_joints=None, tool=None, frame=None):
    if ref_joints is None:
        ref_joints = robot.Joints()
    if tool is None:
        tool = robot.PoseTool()
    if frame is None:
        frame = robot.PoseFrame()
    return robot.SolveIK(target_pose, ref_joints, tool, frame)

def AddJoints(joints, addition:list):
    if isinstance(joints, Mat):
        joints=joints.tolist()
    if len(joints)!=len(addition):
        print(f'Warning: AddJoints({joints, addition}) mst be of same len')
        return joints
    out=[j+a for j,a in zip(joints, addition)]
    return out

def SetTool(toolframe, generate=True):
    robot.setPoseTool(toolframe)
    pose = pose_2_xyzrpw(robot.PoseTool())
    rounded_pose = [round(val, 5) for val in pose]
    if generate:
        robot.AddCode(f'robot.set_tool({rounded_pose})')

def SetFrame(refframe, generate=True):
    robot.setPoseFrame(refframe)
    pose = pose_2_xyzrpw(robot.PoseFrame())
    rounded_pose = [round(val, 5) for val in pose]
    if generate:
        robot.AddCode(f'robot.set_frame({rounded_pose})')

#~ Tool I/O
def Grinder(b):
    if b:
        robot.AddCode('Grinder(1)')
        # if not MAKE: rdk.Command('Trace', 'On')
    else:
        robot.AddCode('Grinder(0)')
        # if not MAKE: rdk.Command('Trace', 'Off')

#~ Misc
def AddSleep(t):
    if MAKE: robot.AddCode("time.sleep(%s)" % t)
    else: time.sleep(t)

def CreateIntList(start, end):
    return list(range(start, end + 1))

def AddSingleTarSel(i: int):
    robot.AddCode(f'if {i} in target_selections:')
    robot.AddTab(True)

def AddMultiTarSel(start: int, end: int):
    robot.AddCode(f'if any(num in target_selections for num in {CreateIntList(start, end)}):')
    robot.AddTab(True)

def AddTab(b: bool):
    robot.AddTab(b)

#~ Target Runs
def AT_force_target_pair_run(t_start, t_end, zcontact=True, easeon=10, easeoff=30):
    if MAKE:
        p_start = pose_2_xyzrpw(t_start)
        p_start = [round(item, 3) for item in p_start]
        p_end = pose_2_xyzrpw(t_end)
        p_end = [round(item, 3) for item in p_end]

        robot.AddCode(f'AT_force_target_pair_run({p_start}, {p_end}, zcontact={zcontact}, easeon={easeon}, easeoff={easeoff})')
    else:
        robot.nos_MoveL(FAST, RelFrame(t_start, z=easeon))
        robot.nos_MoveL(SLOW, t_start)
        robot.nos_MoveL(SLOWAF, t_end)
        robot.nos_MoveL(FAST, RelFrame(t_end, z=easeoff))

















