#!/usr/bin/python
# Generated: January 31, 2025 -- 13:50:13 

from header import *


#=================================================
# Grind_MS3_CALE10in
#=================================================
def Grind_MS3_CALE10in(frame, right, left, target_selections=[]):
    print("running Grind_MS3_CALE10in")
    # INITIALIZATION
    target_selections = target_selections or [0, 1, 2, 3, 4, 5, 6, 7]
    robot.set_tool([-137.10451, 64.91408, 200.52066, -169.06509, -0.30131, -114.884])
    robot.set_frame(frame[:])
    Grinder(1)
    robot.set_tool([-137.105,64.9141,200.521,-169.065,-0.301313,-114.88399999999999])
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    # -- right --
    if any(num in target_selections for num in [0, 1, 2, 3]):
        robot.set_frame(right[:])
        # target 0
        if 0 in target_selections:
            robot.movel(pos=[112.465,29,147.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
            robot.movel(pos=[112.465,29,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([112.465, 29.0, 97.192, -1.0, 2.0, -0.0], [112.465, -1.0, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 1
        if 1 in target_selections:
            robot.movel(pos=[112.465,-75.5,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([112.465, -75.5, 97.192, -1.0, 2.0, -0.0], [112.465, -105.5, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 2
        if 2 in target_selections:
            robot.movel(pos=[112.465,-223.5,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([112.465, -223.5, 97.192, -1.0, 2.0, -0.0], [112.465, -253.5, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 3
        if 3 in target_selections:
            robot.movel(pos=[112.465,-351,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([112.465, -351.0, 97.192, -1.0, 2.0, -0.0], [112.465, -381.0, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
            robot.movel(pos=[112.465,-381,147.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    # -- left --
    if any(num in target_selections for num in [4, 5, 6, 7]):
        robot.set_frame(left[:])
        # target 0
        if 4 in target_selections:
            robot.movel(pos=[-96.349,93,147.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
            robot.movel(pos=[-96.349,93,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([-96.349, 93.0, 97.298, -1.0, -0.0, -0.0], [-96.349, 63.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 1
        if 5 in target_selections:
            robot.movel(pos=[-96.349,-23.5,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([-96.349, -23.5, 97.298, -1.0, -0.0, -0.0], [-96.349, -53.5, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 2
        if 6 in target_selections:
            robot.movel(pos=[-96.349,-252,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([-96.349, -252.0, 97.298, -1.0, -0.0, -0.0], [-96.349, -282.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
        # target 3
        if 7 in target_selections:
            robot.movel(pos=[-96.349,-372,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
            AT_force_target_pair_run([-96.349, -372.0, 97.298, -1.0, -0.0, -0.0], [-96.349, -402.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
            robot.movel(pos=[-96.349,-402,147.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    Grinder(0)
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    # DONE


#=================================================
# Main program select
#=================================================
# def ProgSel(p):
#     if type(p)==str: p=p.strip()
#     if p==999: pass
#     # elif p==12: Grind_MS3_CALE10in()
    # else: pass # return prog_ext(p)

#====================== END ======================
# Generated: January 31, 2025 -- 13:50:16 