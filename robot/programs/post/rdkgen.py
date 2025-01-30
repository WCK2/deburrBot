#!/usr/bin/python
# Generated: January 30, 2025 -- 13:16:19 

from header import *


#=================================================
# Grind_MS3_CALE10in
#=================================================
def Grind_MS3_CALE10in(frame, right, left):
    print("running Grind_MS3_CALE10in")
    # INITIALIZATION
    robot.set_tool([-137.10451, 64.91408, 200.52066, -169.06509, -0.30131, -114.884])
    robot.set_frame(frame[:])
    Grinder(1)
    robot.set_tool([-137.105,64.9141,200.521,-169.065,-0.301313,-114.88399999999999])
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    # -- right --
    robot.set_frame(right[:])
    #   target 0
    robot.movel(pos=[112.465,29,147.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    robot.movel(pos=[112.465,29,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([112.465, 29.0, 97.192, -1.0, 2.0, -0.0], [112.465, -1.0, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 1
    robot.movel(pos=[112.465,-75.5,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([112.465, -75.5, 97.192, -1.0, 2.0, -0.0], [112.465, -105.5, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 2
    robot.movel(pos=[112.465,-223.5,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([112.465, -223.5, 97.192, -1.0, 2.0, -0.0], [112.465, -253.5, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 3
    robot.movel(pos=[112.465,-351,112.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([112.465, -351.0, 97.192, -1.0, 2.0, -0.0], [112.465, -381.0, 97.192, -1.0, 2.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    robot.movel(pos=[112.465,-381,147.192,-1.0,2.0,0],speed=100.0,accel=125.0,blend=0.0)
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    # -- left --
    robot.set_frame(left[:])
    #   target 0
    robot.movel(pos=[-96.349,93,147.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    robot.movel(pos=[-96.349,93,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([-96.349, 93.0, 97.298, -1.0, -0.0, -0.0], [-96.349, 63.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 1
    robot.movel(pos=[-96.349,-23.5,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([-96.349, -23.5, 97.298, -1.0, -0.0, -0.0], [-96.349, -53.5, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 2
    robot.movel(pos=[-96.349,-252,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([-96.349, -252.0, 97.298, -1.0, -0.0, -0.0], [-96.349, -282.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    #   target 3
    robot.movel(pos=[-96.349,-372,112.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    AT_force_target_pair_run([-96.349, -372.0, 97.298, -1.0, -0.0, -0.0], [-96.349, -402.0, 97.298, -1.0, -0.0, -0.0], zcontact=True, easeon=10, easeoff=30)
    robot.movel(pos=[-96.349,-402,147.298,-1.0,0,0],speed=100.0,accel=125.0,blend=0.0)
    robot.movej(joints=[-197.245,108.097,-114.41,86.5082,87.0719,97.8397],speed=60.0,accel=37.5,blend=0.0)
    Grinder(0)
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
# Generated: January 30, 2025 -- 13:16:23 