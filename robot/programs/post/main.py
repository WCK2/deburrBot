# from header import *
from runner import *


#~ Main
def main():
    mem.status = 'idle'
    while True:
        time.sleep(1)
        print(f'>> Waiting for program number')
        while True:
            if mem.start:
                p = mem.program
                break
            CheckRobotFlags(wait=False)
            time.sleep(0.75)

        # if robot.status(22) != 1: print('no comms :o')
        CheckRobotFlags(wait=True)
        CheckForceSensor()
        print(f'> Program: {p}')

        StartRun(p)
        SelectProgram(p)
        EndRun(p)

        print(f'> Finished with prog: {p}\n')
        time.sleep(1)

#~ Setup
def setup():
    server.run_server()
    print('> server running')
    mem.status = 'Initializing'

    robot.init()
    robot.servo_move_enable(False)
    robot.set_collision_val(1)
    CheckForceSensor()
    print('> jaka initialize success')
    

#~ Crash
def crash():
    print("> crash()")
    mem.status = 'crash'

    try:
        if robot.connected:
            print("> JAKA is Connected")
            robot.set_DO(settings.angle_grinder_pin, False)
            # robot.disable()
    except:
        print(exc_info())
        print(" ^^ crash crashed :o")


#~ Main thread
if __name__ == "__main__":
    while True:
        try:
            print(">> PROGRAM START <<")
            setup()
            main()
            print("should never reach here")
        except KeyboardInterrupt:
            exc_info()
            break
        except Exception:
            exc_info()
            crash()
            try:
                print("\033[1;31;43m !! Restarting in 10 ", end="")
                for i in range(10):
                    time.sleep(1)
                    print(end=". ")
                print("\033[0;0m")
            except KeyboardInterrupt:
                print("kb interrupt \033[0;0m")
                sys.exit()
        except:
            exc_info()
            print("rip prog")
            crash()

