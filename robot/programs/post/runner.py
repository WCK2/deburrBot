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


def apriltag_target_runner():
    robot.movej(settings.AT_picture_joints, speed=40)
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
        data = {'name': 'apriltag_target_runner', 'value': data_package}, 
        timeout = 12
    )

    print(f'apriltag_target_runner response: {response}')
    if not isinstance(response, dict):
        print(f'Error: Response is not a dictionary!!')
        return

    selected_detections = response.get('selected_detections', [])
    program_selection = response.get('program_selection', 0)
    target_selections = response.get('target_selections', [])

    #? run through valid detections
    for c, detection in enumerate(selected_detections):
        if not detection.get('valid', False):
            print(f'Skipping selected_detections{[c]} bc it is invalid')
            continue

        if program_selection == 12:
            tag_ref = detection.get("pose_tcp_2_world", None)
            right_ref = detection.get("right_ref", None)
            left_ref = detection.get("left_ref", None)

            if not all(isinstance(ref, list) for ref in [tag_ref, right_ref, left_ref]):
                print(f'Invalid detection data. Skipping {c}...')
                continue
            
            print(f'running prog {program_selection} via apriltag_target_runner')
            Grind_MS3_CALE10in(tag_ref, right_ref, left_ref, target_selections)
        
        elif program_selection == 13:
            tag_ref = detection.get('pose_tcp_2_world', None)

            if not isinstance(tag_ref, list):
                print(f'Invalid detection data. Skipping {c}...')
                continue

            print(f'running prog {program_selection} via apriltag_target_runner')
            # Grind_MS3_10in_Rear(tag_ref, target_selections)









#~ Prog select
def SelectProgram(p):
    if p==0: pass
    elif p==1: generator1_deburring_program()
    elif p==2: apriltag_target_runner()
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
    # StartRun(999)



    # EndRun(999)


    robot.logout()
    server.stop_server()














