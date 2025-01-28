from rdkgen import *




#~ Program runners
def generator1_deburring_program():
    robot.movej(settings.home_joints, speed=25)
    robot.waitmove()

    ZeroForceSensor()
    # robot.set_DO(settings.angle_grinder_pin, True)
    
    target_pairs = mem.generator1_target_pairs
    for pair in target_pairs:
        t_start = pair[0]
        t_end = pair[1]
        if len(t_start) != 6 or len(t_end) != 6:
            print(f'!!WARNING!! target pair list(s) are incorrect length. {pair}')
            continue
        SAM_force_target_pair_run(t_start, t_end, zcontact=True, easeon=15, easeoff=30)

    robot.waitmove()
    robot.set_DO(settings.angle_grinder_pin, False)
    robot.movej(settings.home_joints, speed=25)
    robot.movej(settings.picture_joints, speed=25)
    mem.generator1_target_pairs = []
    robot.waitmove()


def apriltag_coarse_pic():
    robot.movej(settings.AT_picture_joints, speed=25) #* temp
    robot.waitmove()
    time.sleep(1)

    frame = [round(value, 3) for value in robot.get_frame(isdegs=True)[1]]
    tool = [round(value, 3) for value in robot.get_tool(isdegs=True)[1]]
    pose = [round(value, 3) for value in robot.get_tcp_pose()]

    data_package = {
        "frame": frame,
        "tool": tool,
        "pose": pose,
        "camera_tool": settings.camera_tool,
    }
    print(f'data_package: {data_package}')

    response = post_req_sync(
        path = 'ATPrograms', 
        data = {'name': 'coarse_pic', 'value': data_package}, 
        timeout = 12
    )

    if not isinstance(response, dict):
        print('Error: Response is not a dictionary!')
        return
    detections = response.get('detections', [])
    mem.AT_detections = detections
    print(f'mem.AT_detections: {mem.AT_detections}')


def apriltag_runner():
    for detection in mem.AT_detections:
        print(f'\ndetection: {detection}')
        program = detection.get("program", None)
        if program == 12:
            tag_ref = detection.get("pose_tcp_2_world", None)
            right_ref = detection.get("right_ref", None)
            left_ref = detection.get("left_ref", None)

            if not all(isinstance(ref, list) for ref in [tag_ref, right_ref, left_ref]):
                print(f'Invalid detection data. Skipping...')
                continue
            
            print(f'running prog {program} via apriltag_runner')
            Grind_MS3_CALE10in(tag_ref, right_ref, left_ref)
    
    mem.AT_detections = []


def t_right1():
    """ rotated frame with contact at the front of the disc """
    right_frame = [-932.84, -51.44, -57.816, 0.337, 43.791, 91.411]
    targets = [
        [112.465, 14.0, 97.191, 0.0, -0.0, 0.0],
        [112.465, -90.5, 97.191, -2.0, -0.0, 0.0],
        [112.465, -238.5, 97.191, 0.0, -0.0, 0.0],
        [112.465, -366, 97.191, -2.0, -0.0, 0.0],
    ]
    right_joints = [-215.464082, 73.202357, -106.285847, 85.427061, 116.575930, 65.915229]

    mem.speed_multiplier = 0.75
    mem.desired_force = -7

    robot.set_frame(right_frame[:])
    robot.movej(settings.home_joints, speed=25)
    robot.movej(right_joints, speed=25)
    robot.waitmove()

    ZeroForceSensor()
    # robot.set_DO(settings.angle_grinder_pin, True) #! tool on/off

    for c,t in enumerate(targets):
        if (c == 0) or (c == 1):
            mem.speed_multiplier = 0.70
            mem.desired_force = -7
        else:
            mem.speed_multiplier = 0.70
            mem.desired_force = -8.5

        t_start = t[:]
        t_start[1] += 15
        t_end = t[:]
        t_end[1] += -15

        AT_force_target_pair_run(t_start, t_end, zcontact=True, easeon=7.5, easeoff=30)

    robot.waitmove()
    robot.set_DO(settings.angle_grinder_pin, False)
    robot.movej(right_joints, speed=25)
    robot.movej(settings.home_joints, speed=25)
    # robot.movej(settings.picture_joints, speed=15)
    robot.waitmove()

def t_right2():
    """ rotated frame with contact at the front of the disc (compensating for the 50 deg rotation bc of bad door) """
    right_frame = [-932.84, -51.44, -57.816, 0.370, 48.791, 91.455]
    # targets = [
    #     [97.567, 14.0, 106.624, 0.0, 0.0, 0.0],
    #     [97.567, -90.5, 106.624, 0.0, 0.0, 0.0],
    #     [97.567, -238.5, 106.624, 0.0, 0.0, 0.0],
    #     [97.567, -366, 106.624, 0.0, 0.0, 0.0],
    # ]
    targets = [
        [97.567, 14.0, 106.624, -1.0, 0.0, 0.0],
        [97.567, -90.5, 106.624, -1.0, 0.0, 0.0],
        [97.567, -238.5, 106.624, -1.0, 0.0, 0.0],
        [97.567, -366, 106.624, -1.0, 0.0, 0.0],
    ]
    right_joints = [-215.464082, 73.202357, -106.285847, 85.427061, 116.575930, 65.915229]

    mem.speed_multiplier = 0.6
    mem.desired_force = -8.5

    robot.set_frame(right_frame[:])
    robot.movej(settings.home_joints, speed=25)
    robot.movej(right_joints, speed=25)
    robot.waitmove()

    ZeroForceSensor()
    # robot.set_DO(settings.angle_grinder_pin, True) #! tool on/off

    for c,t in enumerate(targets):
        # if (c == 0) or (c == 1):
        #     mem.speed_multiplier = 0.8
        #     mem.desired_force = -5
        # else:
        #     mem.speed_multiplier = 1
        #     mem.desired_force = -7

        t_start = t[:]
        t_start[1] += 15
        t_end = t[:]
        t_end[1] += -15

        AT_force_target_pair_run(t_start, t_end, zcontact=True, easeon=7.5, easeoff=30)

    robot.waitmove()
    robot.set_DO(settings.angle_grinder_pin, False)
    robot.movej(right_joints, speed=25)
    robot.movej(settings.home_joints, speed=25)
    # robot.movej(settings.picture_joints, speed=15)
    robot.waitmove()

def t_right2_5():
    """ rotated frame with contact at the front of the disc (compensating for the 50 deg rotation bc of bad door) """
    right_frame = [-932.84, -51.44, -57.816, 0.370, 48.791, 91.455]
    targets = [
        # [97.567, 59.0, 106.624, 0.0, 0.0, 0.0], # -8.5, 0.5, 0
        # [97.567, 14.0, 106.624, -1.0, 0.0, 0.0], # -8.5, 0.5, -1
        # [97.567, -31, 106.624, -1.0, 0.0, 0.0], # -9.5, 0.5, -1
        # [97.567, -76, 106.624, -1.0, 0.0, 0.0], # -9.5, 0.35, -1
        # [97.567, -130, 106.624, -1.0, 0.0, 0.0], # -12, 0.3, -1
        # [97.567, -175, 106.624, -1.0, 0.0, 0.0], # -12, 0.7, -1
        # [97.567, -220, 106.624, -1.0, 0.0, 0.0], # -9, 0.5, -1
        # [97.567, -265, 106.624, -1.0, 0.0, 0.0], # -9, 0.6, -1
        # [97.567, -310, 106.624, -1.0, 0.0, 0.0],
        [97.567, -355, 106.624, -1.0, 0.0, 0.0], # -9, 0.6, -1
    ]
    right_joints = [-215.464082, 73.202357, -106.285847, 85.427061, 116.575930, 65.915229]

    mem.desired_force = -9
    mem.speed_multiplier = 0.6

    robot.set_frame(right_frame[:])
    robot.movej(settings.home_joints, speed=25)
    robot.movej(right_joints, speed=25)
    robot.waitmove()

    ZeroForceSensor()
    # robot.set_DO(settings.angle_grinder_pin, True) #! tool on/off

    for c,t in enumerate(targets):
        t_start = t[:]
        t_start[1] += 15
        t_end = t[:]
        t_end[1] += -15

        AT_force_target_pair_run(t_start, t_end, zcontact=True, easeon=7.5, easeoff=30)

    robot.waitmove()
    robot.set_DO(settings.angle_grinder_pin, False)
    robot.movej(right_joints, speed=25)
    robot.movej(settings.home_joints, speed=25)
    # robot.movej(settings.picture_joints, speed=15)
    robot.waitmove()

def test_gen():
    frame = [-932.840, -51.440, -57.816, 0.244, -1.208, 91.172]
    right = [-932.840, -51.440, -57.816, 0.337, 43.791, 91.411]
    left = [-932.840, -51.440, -57.816, 0.352, -46.207, 90.922]

    mem.desired_force = -8.5
    mem.speed_multiplier = 0.6
    # robot.set_DO(settings.angle_grinder_pin, False) #! tool on/off

    Grind_MS3_CALE10in(frame, right, left)

    robot.waitmove()
    # robot.set_DO(settings.angle_grinder_pin, False)

    robot.set_frame(list(settings.workstation_frame))
    robot.set_tool(list(settings.grinder_tool))
    robot.waitmove()









#~ Prog select
def SelectProgram(p):
    if p==0: pass
    elif p==1: generator1_deburring_program()
    elif p==10: apriltag_coarse_pic()
    elif p==11: apriltag_runner()
    elif p==100:
        robot.movej(settings.picture_joints, speed=15)
    elif p==101:
        robot.movej(settings.home_joints, speed=15)
    elif p==102:
        robot.movej(settings.change_flap_disc_joints, speed=15)
    elif p==103:
        b = robot.is_in_drag_mode()[1]
        toggle = not b
        if toggle:
            ZeroForceSensor()
            time.sleep(1)
            robot.drag_mode_enable(toggle)
        else:
            robot.drag_mode_enable(toggle)





if __name__=="__main__":
    server.run_server()
    robot.init()
    robot.servo_move_enable(False)
    print(robot.get_force())

    CheckForceSensor()
    robot.servo_move_enable(False)
    robot.set_collision_val(1)

    #* testing
    StartRun(999)

    # t_right1()
    # t_right2()
    # t_right2_5()
    test_gen()

    # robot.set_DO(settings.angle_grinder_pin, True) #! tool on/off
    # robot.waitmove()
    # time.sleep(5)
    # robot.waitmove()
    # robot.set_DO(settings.angle_grinder_pin, False) #! tool on/off


    EndRun(999)


    robot.logout()
    server.stop_server()














