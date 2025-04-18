import threading
import xmlrpc.client
from nos.req import http
from setup import *
import pickle
import gzip
import time
# import keyboard
from utils.timing import RobotRunTimer


#~ Initializations
stopwatch = RobotRunTimer()


#~ Tool I/O
def Grinder(b):
    if b:
        CheckRobotFlags()
        robot.set_DO(settings.angle_grinder_pin, True)
        time.sleep(0.5)
    else:
        robot.waitmove()
        robot.set_DO(settings.angle_grinder_pin, False)


#~ Safety
def CheckRobotFlags(wait=True):
    if wait: robot.waitmove()
    status = robot.status(-1)[1]
    """
    status
        (0)  error code. 0=normal.
        (1)  in place flag. 0=not. 1=in place.
        (2)  powered flag. 0=off, 1=on.
        (3)  enabled flag. 0=off, 1=on.
        (4)  Rapidrate. Robots operation magnification
        (5)  Protective Stop. 0=no collision. 1=collision
        (6)  Drag State. 0=off, 1=on
        ...
        (22) socket connection. 0=dc, 1=connected
        (23) emergency stop. 0=not, 1=emergency stop
    """
    if not status[2]:
        raise Error(f'Raised ERROR: status[2]: {status[2]}')
    elif not status[3]:
        raise Error(f'Raised ERROR: status[3]: {status[3]}') # tripped when acceleration EM stop happens
    elif status[5]:
        raise Error(f'Raised ERROR: status[5]: {status[5]}')
    elif not status[22]:
        raise Error(f'Raised ERROR: status[22]: {status[22]}')
    elif status[23]:
        raise Error(f'Raised ERROR: status[23]: {status[23]}')


#~ Force sensor
def ZeroForceSensor():
    robot.waitmove()
    time.sleep(1)
    robot.set_compliant_type(1, 0)
    time.sleep(0.5)
    robot.set_compliant_type(0, 0)
    time.sleep(0.1)

def CheckForceSensor():
    """ Check Force Sensor status. Return True when ON """
    print('CheckForceSensor()')
    f1 = robot.get_force()[0]
    print(f1)
    time.sleep(0.5)
    if not robot.get_DO(settings.force_sensor_pin):
        robot.set_DO(settings.force_sensor_pin, 1)
        time.sleep(1)
        return CheckForceSensor()
    elif robot.get_compliant_type()[1] != 0:
        robot.set_compliant_type(0, 0)
        time.sleep(1)
        return CheckForceSensor()
    elif (f1 == 0.0) or (f1 == robot.get_force()[0]):
        print(robot.get_force()[0])
        robot.set_torque_sensor_mode(0)
        time.sleep(1)
        robot.set_torque_sensor_mode(1)
        time.sleep(1)
        return CheckForceSensor()
    else: return True


#~ Computation helpers
def get_max_abs(data:list):
    d_abs = [abs(val) for val in data]
    d_max = max(d_abs)
    d_index = d_abs.index(d_max)
    return data[d_index]

def check_forces_conditions(forces):
    condition_1 = any(value > 1 or value < -1 for value in forces[:3])
    condition_2 = any(value > 0.25 or value < -0.25 for value in forces[3:])
    return condition_1 or condition_2


#~ Force move stuff
def SAM_force_target_run(targets: list, zcontact: bool=True, easeon: int=20, easeoff: int=40):
    """ Consecutive target pathing in servo mode (from one target to the next) """
    data_log = {
        'pose': [],
        'zero_forces': [],
        'error': [],
        'integral': [],
        'derivative': [],
        'zstep': [],
        'time': [],
    }
    max_xy_step = 0.25

    #? ease on
    t_easeon = targets[0].copy()
    t_easeon[2] = easeon
    robot.movel(t_easeon, speed=25, accel=125)
    robot.waitmove()

    robot.servo_move_use_joint_LPF(0.4)
    ZeroForceSensor()
    robot.servo_move_enable(True)
    time.sleep(0.5)

    #? initial z-contact
    if zcontact:
        counter = 0
        zstep = 0
        break_counter = 0
        no_contact_tolerance = 5
        pstart = robot.get_tcp_pose()
        while True:
            d = abs(robot.get_tcp_pose()[2] - pstart[2])
            if d > (easeon + no_contact_tolerance):
                print(f'break zcontact loop, without contact. (d={d})')
                break

            zero_forces = robot.get_zeroforce()
            error = (mem.desired_force * 1.5) - zero_forces[2]
            if error > 0:
                break_counter += 1
                print(f'break_contact loop incremented to: {break_counter}')
                if break_counter >= 4:
                    print(f'break zcontact loop, with contact. (d={d})')
                    break

            pid.integral += error * 0.004  # dt is approximately 0.004 seconds

            raw_derivative = (error - pid.previous_error) / 0.004
            derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
            pid.previous_derivative = derivative

            zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

            # apply rate limit to zstep
            if zstep - pid.previous_zstep > pid.max_step_change:
                zstep = pid.previous_zstep + pid.max_step_change
            elif zstep - pid.previous_zstep < -pid.max_step_change:
                zstep = pid.previous_zstep - pid.max_step_change

            pid.previous_error = error
            pid.previous_zstep = zstep

            # limit the step size to max_step
            zstep = max(min(zstep, pid.max_step*5), -pid.max_step*5)
            current_speed_multiplier = mem.speed_multiplier
            zstep *= current_speed_multiplier

            robot.servo_p(cartesian_pose = [0, 0, zstep, 0, 0, 0], move_mode = 1)

            if counter % 20 == 0:
                CheckRobotFlags(wait=False)
            counter += 1

            # print(f'{zstep:.3f}, {error:.1f}, {d:.1f}')
            time.sleep(0.004)
            # if keyboard.is_pressed('q'): break

    #? begin looping through targets (omit targets[0])
    for c, tar in enumerate(targets):
        if c == 0: continue
        # print(f'{"-"*25}\nloop counter: {c}')

        #? preprocess pathing / step values
        p2 = tar
        p1 = robot.get_tcp_pose()

        # print(f' - p1: {p1}')
        # print(f' - p2: {p2}')

        pdiff = [_p2 - _p1 for _p2, _p1 in zip(p2, p1)]
        max_index = (pdiff.index(get_max_abs(pdiff[:2])))
        pfactor = abs(max_xy_step / pdiff[max_index])
        pstep = [round(_pdiff * pfactor, 7) for _pdiff in pdiff]

        # print(f'   - pdiff: {pdiff}')
        # print(f'   - max_index: {max_index}')
        # print(f'   - pfactor: {pfactor}')
        # print(f'   - pstep: {pstep}')

        #? apply movement and break once target is reached
        counter = 0
        zstep = 0
        while True:
            pose = robot.get_tcp_pose()

            if abs(pose[max_index] - p1[max_index]) > abs(pdiff[max_index]):
                break

            #? PID Controller
            zero_forces = robot.get_zeroforce()

            error = mem.desired_force - zero_forces[2]
            pid.integral += error * 0.004  # dt is approximately 0.004 seconds

            raw_derivative = (error - pid.previous_error) / 0.004
            derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
            pid.previous_derivative = derivative

            zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

            # apply rate limit to zstep
            if zstep - pid.previous_zstep > pid.max_step_change:
                zstep = pid.previous_zstep + pid.max_step_change
            elif zstep - pid.previous_zstep < -pid.max_step_change:
                zstep = pid.previous_zstep - pid.max_step_change

            pid.previous_error = error
            pid.previous_zstep = zstep

            # limit the step size to max_step
            zstep = max(min(zstep, pid.max_step), -pid.max_step)
            current_speed_multiplier = mem.speed_multiplier
            xstep = pstep[0] * current_speed_multiplier
            ystep = pstep[1] * current_speed_multiplier
            zstep *= current_speed_multiplier

            # print(f'zero_forces[2]: {zero_forces[2]:.3f}, error: {error:.3f}, integral: {pid.integral:.3f}, derivative: {derivative:.3f}, zstep: {zstep:.3f}')
            # print(f'xstep: {xstep:.3f}, ystep: {ystep:.3f}, zstep: {zstep:.3f}')

            robot.servo_p(cartesian_pose = [xstep, ystep, zstep, 0, 0, 0], move_mode = 1)

            #? log data
            data_log['pose'].append([round(val, 3) for val in pose])
            data_log['zero_forces'].append(round(zero_forces, 3))
            data_log['error'].append(round(error, 3))
            data_log['integral'].append(round(pid.integral, 3))
            data_log['derivative'].append(round(derivative, 3))
            data_log['zstep'].append(round(zstep, 3))
            data_log['time'].append(time.time())
            
            if counter % 20 == 0:
                CheckRobotFlags(wait=False)
            counter += 1

            time.sleep(0.004)
            # if keyboard.is_pressed('q'): break

        # robot.servo_p(cartesian_pose = [-xstep, -ystep, 0, 0, 0, 0], move_mode = 1)
        robot.waitmove()
        pfinal = robot.get_tcp_pose()
        # print(f' - Actual ending pose: {pfinal}')

    #? fin...
    robot.waitmove()
    robot.servo_move_enable(False)
    robot.waitmove()
    time.sleep(1)

    # Compress and save the data using pickle and gzip
    filename = os.getcwd() + f'/assets/temp/data_log_{time.strftime("%Y-%m-%d_%H-%M-%S")}.pkl.gz'
    with gzip.open(filename, 'wb') as f:
        pickle.dump(data_log, f)

    #? ease off
    t_easeoff = robot.get_tcp_pose()
    t_easeoff[2] += easeoff
    robot.movel(t_easeoff, speed=50, accel=125)
    robot.waitmove()


def SAM_force_target_pair_run(t_start: list, t_end: list, zcontact: bool=True, easeon: int=20, easeoff: int=40):
    """ Simple target pathing in servo mode (from one target to the next) """
    data_log = {
        'pose': [],
        'zero_forces': [],
        'error': [],
        'integral': [],
        'derivative': [],
        'zstep': [],
        'time': [],
    }
    max_xy_step = 0.25

    #? ease on
    t_easeon = t_start.copy()
    # t_easeon[2] += easeon #! May want to just set this to (0 + easeon) as long as the given part isnt super tall (3d)
    t_easeon[2] = easeon #! ... like so lol
    robot.movel(t_easeon, speed=25, accel=125)
    robot.waitmove()

    robot.servo_move_use_joint_LPF(0.4)
    ZeroForceSensor()
    robot.servo_move_enable(True)
    time.sleep(0.5)
    
    if zcontact:
        counter = 0
        zstep = 0
        break_counter = 0
        no_contact_tolerance = 5
        pstart = robot.get_tcp_pose()
        while True:
            d = abs(robot.get_tcp_pose()[2] - pstart[2])
            if d > (easeon + no_contact_tolerance):
                print(f'break zcontact loop, without contact. (d={d})')
                break

            zero_forces = robot.get_zeroforce()
            error = (mem.desired_force * 1.5) - zero_forces[2]
            if error > 0:
                break_counter += 1
                print(f'break_contact loop incremented to: {break_counter}')
                if break_counter >= 4:
                    print(f'break zcontact loop, with contact. (d={d})')
                    break

            pid.integral += error * 0.004  # dt is approximately 0.004 seconds

            raw_derivative = (error - pid.previous_error) / 0.004
            derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
            pid.previous_derivative = derivative

            zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

            # apply rate limit to zstep
            if zstep - pid.previous_zstep > pid.max_step_change:
                zstep = pid.previous_zstep + pid.max_step_change
            elif zstep - pid.previous_zstep < -pid.max_step_change:
                zstep = pid.previous_zstep - pid.max_step_change

            pid.previous_error = error
            pid.previous_zstep = zstep

            # limit the step size to max_step
            zstep = max(min(zstep, pid.max_step*5), -pid.max_step*5)
            current_speed_multiplier = mem.speed_multiplier
            zstep *= current_speed_multiplier

            robot.servo_p(cartesian_pose = [0, 0, zstep, 0, 0, 0], move_mode = 1)

            if counter % 20 == 0:
                CheckRobotFlags(wait=False)
            counter += 1

            # print(f'{zstep:.3f}, {error:.1f}, {d:.1f}')
            time.sleep(0.004)
            # if keyboard.is_pressed('q'): break

    #? preprocess pathing / step values
    p2 = t_end
    p1 = robot.get_tcp_pose()

    # print(f' - p1: {p1}')
    # print(f' - p2: {p2}')

    pdiff = [_p2 - _p1 for _p2, _p1 in zip(p2, p1)]
    max_index = (pdiff.index(get_max_abs(pdiff[:2])))
    pfactor = abs(max_xy_step / pdiff[max_index])
    pstep = [round(_pdiff * pfactor, 7) for _pdiff in pdiff]

    # print(f'   - pdiff: {pdiff}')
    # print(f'   - max_index: {max_index}')
    # print(f'   - pfactor: {pfactor}')
    # print(f'   - pstep: {pstep}')

    #? apply movement and break once target is reached
    counter = 0
    zstep = 0
    while True:
        pose = robot.get_tcp_pose()

        if abs(pose[max_index] - p1[max_index]) > abs(pdiff[max_index]):
            break

        #? PID Controller
        zero_forces = robot.get_zeroforce()

        error = mem.desired_force - zero_forces[2]
        pid.integral += error * 0.004  # dt is approximately 0.004 seconds

        raw_derivative = (error - pid.previous_error) / 0.004
        derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
        pid.previous_derivative = derivative

        zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

        # apply rate limit to zstep
        if zstep - pid.previous_zstep > pid.max_step_change:
            zstep = pid.previous_zstep + pid.max_step_change
        elif zstep - pid.previous_zstep < -pid.max_step_change:
            zstep = pid.previous_zstep - pid.max_step_change

        pid.previous_error = error
        pid.previous_zstep = zstep

        # limit the step size to max_step
        zstep = max(min(zstep, pid.max_step), -pid.max_step)
        current_speed_multiplier = mem.speed_multiplier
        xstep = pstep[0] * current_speed_multiplier
        ystep = pstep[1] * current_speed_multiplier
        zstep *= current_speed_multiplier

        # print(f'zero_forces[2]: {zero_forces[2]:.3f}, error: {error:.3f}, integral: {pid.integral:.3f}, derivative: {derivative:.3f}, zstep: {zstep:.3f}')
        # print(f'xstep: {xstep:.3f}, ystep: {ystep:.3f}, zstep: {zstep:.3f}')

        robot.servo_p(cartesian_pose = [xstep, ystep, zstep, 0, 0, 0], move_mode = 1)

        #? log data
        data_log['pose'].append([round(val, 3) for val in pose])
        data_log['zero_forces'].append(round(zero_forces, 3))
        data_log['error'].append(round(error, 3))
        data_log['integral'].append(round(pid.integral, 3))
        data_log['derivative'].append(round(derivative, 3))
        data_log['zstep'].append(round(zstep, 3))
        data_log['time'].append(time.time())
    
        if counter % 20 == 0:
            CheckRobotFlags(wait=False)
        counter += 1

        time.sleep(0.004)
        # if keyboard.is_pressed('q'): break

    robot.waitmove()
    pfinal = robot.get_tcp_pose()
    # print(f' - Actual ending pose: {pfinal}')

    #? fin...
    robot.waitmove()
    robot.servo_move_enable(False)
    robot.waitmove()
    time.sleep(0.1)

    # Compress and save the data using pickle and gzip
    filename = os.getcwd() + f'/assets/temp/data_log_{time.strftime("%Y-%m-%d_%H-%M-%S")}.pkl.gz'
    with gzip.open(filename, 'wb') as f:
        pickle.dump(data_log, f)
    
    #? ease off
    # t_easeoff = t_end.copy()
    t_easeoff = robot.get_tcp_pose()
    t_easeoff[2] += easeoff
    robot.movel(t_easeoff, speed=50, accel=125)
    robot.waitmove()


def AT_force_target_pair_run(t_start: list, t_end: list, zcontact: bool=True, easeon: int=20, easeoff: int=40):
    """ Simple target pathing in servo mode (from one target to the next) """
    data_log = {
        'pose': [],
        'zero_forces': [],
        'error': [],
        'integral': [],
        'derivative': [],
        'zstep': [],
        'time': [],
    }
    max_xy_step = 0.25

    #? ease on
    t_easeon = t_start.copy()
    t_easeon[2] += easeon
    robot.movel(t_easeon, speed=25, accel=125)
    robot.waitmove()

    robot.servo_move_use_joint_LPF(0.4)
    ZeroForceSensor()
    robot.servo_move_enable(True)
    time.sleep(0.5)
    
    if zcontact:
        counter = 0
        zstep = 0
        break_counter = 0
        no_contact_tolerance = 5
        pstart = robot.get_tcp_pose()
        while True:
            pose = robot.get_tcp_pose()
            d = abs(pose[2] - pstart[2])
            if d > (easeon + no_contact_tolerance):
                print(f'break zcontact loop, without contact. (d={d})')
                break

            zero_forces = robot.get_zeroforce()
            error = (mem.desired_force * 1.5) - zero_forces[2]
            if error > 0:
                break_counter += 1
                print(f'break_contact loop incremented to: {break_counter}. desired_force (not modified): {mem.desired_force}. error: {error}. zero_forces[2]: {zero_forces[2]}')
                if break_counter >= 5:
                    print(f'break zcontact loop, with contact. (d={d})')
                    break

            pid.integral += error * 0.004  # dt is approximately 0.004 seconds

            raw_derivative = (error - pid.previous_error) / 0.004
            derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
            pid.previous_derivative = derivative

            zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

            # apply rate limit to zstep
            if zstep - pid.previous_zstep > pid.max_step_change:
                zstep = pid.previous_zstep + pid.max_step_change
            elif zstep - pid.previous_zstep < -pid.max_step_change:
                zstep = pid.previous_zstep - pid.max_step_change

            pid.previous_error = error
            pid.previous_zstep = zstep

            # limit the step size to max_step
            zstep = max(min(zstep, pid.max_step*5), -pid.max_step*5)
            current_speed_multiplier = mem.speed_multiplier
            zstep *= current_speed_multiplier

            robot.servo_p(cartesian_pose = [0, 0, zstep, 0, 0, 0], move_mode = 1)

            #? log data
            data_log['pose'].append([round(val, 3) for val in pose])
            data_log['zero_forces'].append(round(zero_forces, 3))
            data_log['error'].append(round(error, 3))
            data_log['integral'].append(round(pid.integral, 3))
            data_log['derivative'].append(round(derivative, 3))
            data_log['zstep'].append(round(zstep, 3))
            data_log['time'].append(time.time())
        
            if counter % 20 == 0:
                CheckRobotFlags(wait=False)
            counter += 1

            # print(f'{zstep:.3f}, {error:.1f}, {d:.1f}')
            time.sleep(0.004)
            # if keyboard.is_pressed('q'): break

    #? preprocess pathing / step values
    p2 = t_end
    p1 = robot.get_tcp_pose()

    # print(f' - p1: {p1}')
    # print(f' - p2: {p2}')

    pdiff = [_p2 - _p1 for _p2, _p1 in zip(p2, p1)]
    max_index = (pdiff.index(get_max_abs(pdiff[:2])))
    pfactor = abs(max_xy_step / pdiff[max_index])
    pstep = [round(_pdiff * pfactor, 7) for _pdiff in pdiff]

    # print(f'   - pdiff: {pdiff}')
    # print(f'   - max_index: {max_index}')
    # print(f'   - pfactor: {pfactor}')
    # print(f'   - pstep: {pstep}')

    #? apply movement and break once target is reached
    counter = 0
    zstep = 0
    while True:
        pose = robot.get_tcp_pose()

        if abs(pose[max_index] - p1[max_index]) > abs(pdiff[max_index]):
            break

        #? PID Controller
        zero_forces = robot.get_zeroforce()

        error = mem.desired_force - zero_forces[2]
        pid.integral += error * 0.004  # dt is approximately 0.004 seconds

        raw_derivative = (error - pid.previous_error) / 0.004
        derivative = pid.alpha * raw_derivative + (1 - pid.alpha) * pid.previous_derivative
        pid.previous_derivative = derivative

        zstep = pid.Kp * error + pid.Ki * pid.integral + pid.Kd * derivative

        # apply rate limit to zstep
        if zstep - pid.previous_zstep > pid.max_step_change:
            zstep = pid.previous_zstep + pid.max_step_change
        elif zstep - pid.previous_zstep < -pid.max_step_change:
            zstep = pid.previous_zstep - pid.max_step_change

        pid.previous_error = error
        pid.previous_zstep = zstep

        # limit the step size to max_step
        zstep = max(min(zstep, pid.max_step), -pid.max_step)
        current_speed_multiplier = mem.speed_multiplier
        xstep = pstep[0] * current_speed_multiplier
        ystep = pstep[1] * current_speed_multiplier
        zstep *= current_speed_multiplier

        # print(f'zero_forces[2]: {zero_forces[2]:.3f}, error: {error:.3f}, integral: {pid.integral:.3f}, derivative: {derivative:.3f}, zstep: {zstep:.3f}')
        # print(f'xstep: {xstep:.3f}, ystep: {ystep:.3f}, zstep: {zstep:.3f}')

        robot.servo_p(cartesian_pose = [xstep, ystep, zstep, 0, 0, 0], move_mode = 1)

        #? log data
        data_log['pose'].append([round(val, 3) for val in pose])
        data_log['zero_forces'].append(round(zero_forces, 3))
        data_log['error'].append(round(error, 3))
        data_log['integral'].append(round(pid.integral, 3))
        data_log['derivative'].append(round(derivative, 3))
        data_log['zstep'].append(round(zstep, 3))
        data_log['time'].append(time.time())
    
        if counter % 20 == 0:
            CheckRobotFlags(wait=False)
        counter += 1

        time.sleep(0.004)
        # if keyboard.is_pressed('q'): break

    robot.waitmove()
    pfinal = robot.get_tcp_pose()
    # print(f' - Actual ending pose: {pfinal}')

    #? fin...
    robot.waitmove()
    robot.servo_move_enable(False)
    robot.waitmove()
    time.sleep(0.1)

    # Compress and save the data using pickle and gzip
    filename = os.getcwd() + f'/assets/temp/data_log_{time.strftime("%Y-%m-%d_%H-%M-%S")}.pkl.gz'
    with gzip.open(filename, 'wb') as f:
        pickle.dump(data_log, f)
    
    #? ease off
    # t_easeoff = t_end.copy()
    t_easeoff = robot.get_tcp_pose()
    t_easeoff[2] += easeoff
    robot.movel(t_easeoff, speed=50, accel=125)
    robot.waitmove()



#~ Program prep/cleanup
def StartRun(p):
    stopwatch.start()
    mem.status = f'running:{p}'
    robot.servo_move_enable(False)
    if robot.is_in_drag_mode()[1]:
        robot.drag_mode_enable(False)

    robot.set_frame(list(settings.workstation_frame))
    robot.set_tool(list(settings.grinder_tool))
    robot.waitmove()

def EndRun(p):
    robot.waitmove()
    stopwatch.stop()
    mem.status = f'idle:{p}'

    robot.set_frame(list(settings.workstation_frame))
    robot.set_tool(list(settings.grinder_tool))
    robot.waitmove()




