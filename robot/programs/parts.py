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
    params = 'frame, right, left, target_selections=[]'
    def right(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('right')
        tars = GetTargetMats(tar_frame)

        _start = 0
        AddMultiTarSel(_start, len(tars)-1)
        
        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(right[:])')

        for c, t in enumerate(tars):
            robot.AddCode(f'# target {c}')
            AddSingleTarSel(c + _start)

            _rx = -1
            t1 = RelFrame(t.Offset(rx=_rx), x=0, y=15)
            t2 = RelFrame(t.Offset(rx=_rx), x=0, y=-15)

            if c == 0:
                robot.nos_MoveL(FAST, RelFrame(t1, z=50))
            
            robot.nos_MoveL(FAST, RelFrame(t1, z=15))
            AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)

            if c == len(tars) - 1:
                robot.nos_MoveL(FAST, RelFrame(t2, z=50))

            AddTab(False)
        
        AddTab(False)

    def left(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('left')
        tars = GetTargetMats(tar_frame)

        _start = 4
        AddMultiTarSel(_start, _start + len(tars)-1)

        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(left[:])')

        for c, t in enumerate(tars):
            robot.AddCode(f'# target {c}')
            AddSingleTarSel(c + _start)

            _rx = -1
            t1 = RelFrame(t.Offset(rx=_rx), x=10, y=15)
            t2 = RelFrame(t.Offset(rx=_rx), x=10, y=-15)

            if c == 0:
                robot.nos_MoveL(FAST, RelFrame(t1, z=50))
            
            robot.nos_MoveL(FAST, RelFrame(t1, z=15))
            AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)

            if c == len(tars) - 1:
                robot.nos_MoveL(FAST, RelFrame(t2, z=50))

            AddTab(False)
        
        AddTab(False)

    def run(self):
        robot.AddCode(f'target_selections = target_selections or {CreateIntList(0, 7)}')
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

        Grinder(0)
        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())

        # robot.nos_MoveJ(FASTAF, jtars.picture_joints.Joints())






#^=========================
#^ MS3 10in Door Rear - Grind weld blemishes
#^=========================
class Grind_MS3_10in_Rear(GENERIC_ATPROGRAM):
    params = 'frame, target_selections=[]'
    def spot_welds(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('spot_welds')
        tars = GetTargetMats(tar_frame)

        _start = 0
        AddMultiTarSel(_start, _start + len(tars)-1)

        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(frame[:])')

        for c, t in enumerate(tars):
            robot.AddCode(f'# target {c}')
            AddSingleTarSel(c + _start)

            _rx = -1
            t1 = RelFrame(t.Offset(rx=_rx), x=0, y=15)
            t2 = RelFrame(t.Offset(rx=_rx), x=0, y=-15)

            if c == 0 or c == 4:
                robot.nos_MoveL(FAST, RelFrame(t1, z=50))
            
            robot.nos_MoveL(FAST, RelFrame(t1, z=15))
            AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)

            if c == len(tars) - 1:
                robot.nos_MoveL(FAST, RelFrame(t2, z=50))

            AddTab(False)
        
        AddTab(False)

    def corners(self):
        robot.AddCode(f'# -- {inspect.currentframe().f_code.co_name} --')
        tar_frame = self.frame.findChild('corners')
        tars = GetTargetMats(tar_frame)

        SetFrame(tar_frame, False)
        robot.AddCode('robot.set_frame(frame[:])')

        for c, t in enumerate(tars):
            # if c != 1: continue
            robot.AddCode(f'# target {c}')

            if c == 0: rx_list = [0, -12.5, -25]
            elif c == 1: rx_list = [0, 10, 20]
            elif c == 2: rx_list = [0, -12.5, -25]
            elif c == 3: rx_list = [0, 10, 20]

            for cc, _rx in enumerate(rx_list):
                t1 = RelFrame(t.Offset(rx=_rx), x=-15)
                t2 = RelFrame(t.Offset(rx=_rx), x=15)

                if cc == 0:
                    robot.nos_MoveL(FAST, RelFrame(t1, z=50))
                
                robot.nos_MoveL(FAST, RelFrame(t1, z=15))
                AT_force_target_pair_run(t1, t2, zcontact=True, easeon=10, easeoff=30)
            
                if cc == len(rx_list) - 1:
                    robot.nos_MoveL(FAST, RelFrame(t2, z=50))


    def run(self):
        robot.AddCode(f'target_selections = target_selections or {CreateIntList(0, 7)}')
        robot.setSlowSpeeds(*slow_speeds)
        robot.setFastSpeeds(*fast_speeds)

        SetTool(self.tool)
        SetFrame(self.frame, False)
        robot.AddCode('robot.set_frame(frame[:])')
        
        Grinder(1)
        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())

        self.spot_welds()
        # robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())
        # self.corners()

        Grinder(0)
        robot.nos_MoveJ(FASTAF, jtars.home_joints.Joints())





