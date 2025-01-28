from helper import *
from collections import defaultdict
import inspect



#^=======================================================================================================================
#^ Generic AT Programs Class
#^=======================================================================================================================
class GENERIC_ATPROGRAM():
    def __init__(self, **kwargs):
        self.kw = kwargs

        def get(n,d):
            out = kwargs.get(n,None)
            if out != None: return out
            elif hasattr(self, n): return getattr(self,n)
            else: return d

        self.fn                 = get('fn', self.__class__.__name__)
        self.params             = get('params', '')
        self.frame_name         = get('frame', '')
        self.tool_name          = get('tool', 'Flap Disc Front R2')

        if bool(get("auto", True)): self.main()

    def init(self):
        robot.AddCode("# INITIALIZATION")

        self.frame = rdk.Item(self.frame_name)
        self.tool = rdk.Item(self.tool_name)

    def run(self):
        pass

    def main(self):
        print(self.fn)
        robot.AddHeader(self.fn)
        robot.AddCode(f'def {self.fn}({self.params}):')
        robot.AddTab(True)
        robot.AddCode(f'print("running {self.fn}")')
        rdk.setCollisionActive(0)

        self.init()
        self.run()

        robot.AddCode("# DONE")
        robot.AddTab(False)



#^=========================
#^ MS3 10in Door - Grind weld blemishes
#^=========================
class Grind_MS3_CALE10in(GENERIC_ATPROGRAM):
    params = 'frame, right, left'
    def right(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('right')
        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(right[:])')

        tars = GetTargetMats(tar_frame)

        for c, t in enumerate(tars):
            robot.AddCode(f'#   target {c}')
            _rx = -1
            t1 = RelFrame(t.Offset(rx=_rx), x=0, y=15)
            t2 = RelFrame(t.Offset(rx=_rx), x=0, y=-15)

            if c == 0:
                robot.nos_MoveL(FAST, RelFrame(t1, z=50))
            
            robot.nos_MoveL(FAST, RelFrame(t1, z=15))
            AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)

            if c == len(tars) - 1:
                robot.nos_MoveL(FAST, RelFrame(t2, z=50))

    def left(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('left')
        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(left[:])')

        tars = GetTargetMats(tar_frame)

        for c, t in enumerate(tars):
            robot.AddCode(f'#   target {c}')
            _rx = -1
            t1 = RelFrame(t.Offset(rx=_rx), x=10, y=15)
            t2 = RelFrame(t.Offset(rx=_rx), x=10, y=-15)

            if c == 0:
                robot.nos_MoveL(FAST, RelFrame(t1, z=50))
            
            robot.nos_MoveL(FAST, RelFrame(t1, z=15))
            AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)

            if c == len(tars) - 1:
                robot.nos_MoveL(FAST, RelFrame(t2, z=50))





    def run(self):
        robot.setSlowSpeeds(*slow_speeds)
        robot.setFastSpeeds(*fast_speeds)

        SetTool(self.tool)
        SetFrame(self.frame, False)
        robot.AddCode('robot.set_frame(frame[:])')
        
        Grinder(1)

        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())
        self.right()
        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())
        self.left()
        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())

        Grinder(0)

        # robot.nos_MoveJ(FASTAF, jtars.picture_joints.Joints())





