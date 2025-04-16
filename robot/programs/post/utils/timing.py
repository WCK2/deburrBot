import time

class RobotRunTimer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        if self.start_time is None:
            print("Warning: RobotRunTimer has not been started.")
            return
        
        elapsed_time = time.time() - self.start_time
        self.start_time = None  # Reset for next run
        
        if elapsed_time >= 60:
            minutes = int(elapsed_time // 60)
            seconds = elapsed_time % 60
            print(f"Run completed in {minutes} min & {seconds:.3f} sec.")
        else:
            print(f"Run completed in {elapsed_time:.3f} seconds.")


