import json
import os
import requests
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from socketserver import BaseServer
from urllib.parse import urlparse, parse_qs
from jaka.nos.jakabot import *


#~ PID config
class PIDConfig:
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(PIDConfig, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self):
        self.Kp = 0.01
        self.Ki = 0.001
        self.Kd = 0.001

        self.integral = 0
        self.previous_error = 0

        self.max_step = 0.1
        self.max_step_change = self.max_step
        self.previous_zstep = 0

        self.alpha = 0.1  # Smoothing factor (0 < alpha < 1)
        self.previous_derivative = 0

pid = PIDConfig()


#~ Static settings
class SETTINGS:
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(SETTINGS, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self):
        #? network
        self.jaka_ip = '192.168.69.60'
        self.jaka_server_port = 42000

        self.rpi_ip = '192.168.69.120' if os.name == 'nt' else '192.168.69.62'
        self.rpi_port = 42001
        self.rpi_url = f'http://{self.rpi_ip}:{self.rpi_port}/'

        #? robot
        self.force_sensor_pin = 0
        self.angle_grinder_pin = 1
        self.emergency_output_pin = 2 # Make sure to setup this output to Trigger EM STOP internally on JAKA

        self.emergency_input_pin = 0
        self.pause_button_pin = 1

        self.workstation_frame = (-809.075, -11.325, -100.975, -0.18, -0.0034, 91.08)
        self.grinder_tool = (-137.104, 64.914, 200.520, -169.065, -0.301, -114.884)
        self.camera_tool = [78.21, 73.4, 50.54, 15.29, -0.46, 150.04]

        self.home_joints = [-195.853979, 108.126304, -114.461449, 86.588613, 87.045869, 103.318228]
        self.picture_joints = [-191.885584, 73.340272, -37.301865, 38.968284, 86.117135, 197.443493]
        self.change_flap_disc_joints = [-188.672630, 51.422710, -81.831690, 209.464020, 98.370150, 114.741520]
        self.AT_picture_joints = [-187.700363, 74.300811, -76.001885, 76.472066, 87.208311, 201.490599]

        self.x_boundary_range = [-565, 565]
        self.y_boundary_range = [-340, 345]
        self.z_boundary_range = [-40, 50] # need to be careful around the Control Panel / GUI

settings = SETTINGS()

robot = jakabot(settings.jaka_ip)


#~ Requests
def post_req_async(path, data):
    """Send a POST request asynchronously."""
    url = settings.rpi_url + path

    def send_post_request():
        try:
            response = requests.post(url, json=data, timeout=5)
            print(f'POST response: {response.status_code}, {response.text}')
        except requests.Timeout:
            print("The request timed out.")
        except requests.RequestException as e:
            print(f'Error sending POST request: {e}')

    # Create and start a new thread for the POST request
    threading.Thread(target=send_post_request, daemon=True).start()

def post_req_sync(path, data, timeout=5):
    """Send a POST request and return response."""
    url = settings.rpi_url + path

    try:
        response = requests.post(url, json=data, timeout=timeout)
        # print(f'Status Code: {response.status_code}')
        # print(f'Content-Type: {response.headers.get("Content-Type")}')

        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            try:
                response_data = response.json()
                # print("Parsed JSON data:", response_data)
                return response_data
            except ValueError as e:
                print("Error parsing JSON:", e)
                return None
        elif 'text/html' in content_type:
            # print("Received HTML response.")
            return response.text
        else:
            print("Received non-JSON, non-HTML response.")
            return response.text  # You might still want to return the raw text for other content types

    except requests.Timeout:
        print("The request timed out.")
        return None
    except requests.RequestException as e:
        print(f'Error sending POST request: {e}')
        return None


#~ MEMORY
class MEMORY:
    def __new__(cls, *args, **kw):
         if not hasattr(cls, '_instance'):
             orig = super(MEMORY, cls)
             cls._instance = orig.__new__(cls, *args, **kw)
         return cls._instance
    
    def __init__(self):
        self.lock = threading.Lock()
        self._status = 'Booting'
        self._start = False
        self._program = 0
        self._speed_multiplier = 0.2
        self._desired_force = -7

        self.generator1_target_pairs = []

        self.thread_mem_start = None

    def _get_status(self):
        with self.lock:
            return self._status
    def _set_status(self, s: str):
        print(f'new_status: {s}')
        with self.lock:
            self._status = s
        post_req_async(path='mem', data={'name': 'status', 'value': self._status})
    status = property(_get_status, _set_status)

    def _get_start(self):
        with self.lock:
            return self._start
    def _set_start(self, b: bool):
        # print(f'set_digital_start: {b}, program: {self._program} @ {time.time()}')
        with self.lock:
            self._start = b
    start = property(_get_start, _set_start)

    def _get_program(self):
        with self.lock:
            return self._program
    def _set_program(self, n: int):
        if self.thread_mem_start is None or not self.thread_mem_start.is_alive():
            with self.lock:
                # print(f'changing self.program from {self._program} to {n}')
                self._program = n
            self.start = True
            self.thread_mem_start = threading.Thread(target=self._reset_start, daemon=True)
            self.thread_mem_start.start()
        # else: print(f'thread is still alive...')
    program = property(_get_program, _set_program)

    def _get_speed_multiplier(self):
        with self.lock:
            return self._speed_multiplier
    def _set_speed_multiplier(self, val):
        if 0.05 <= val <= 4:
            with self.lock:
                self._speed_multiplier = val
        else:
            print(f'!!Warning!! val: {val} in _set_speed_multiplier is not within the valid range')
    speed_multiplier = property(_get_speed_multiplier, _set_speed_multiplier)

    def _get_desired_force(self):
        with self.lock:
            return self._desired_force
    def _set_desired_force(self, val):
        with self.lock:
            self._desired_force = val
    desired_force = property(_get_desired_force, _set_desired_force)

    def _reset_start(self):
        time.sleep(3)
        self.start = False
        self._program = 0

mem = MEMORY()


#~ Server handler
class JakaHttpHandler(SimpleHTTPRequestHandler):
    def text_response(self, code: int, text: str = ""):
        """Send a plain text response."""
        self.send_response(code)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(text.encode())
        return
        
    def json_response(self, code: int, data: dict = {}):
        """Send a JSON response."""
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))
        return

    def do_GET(self):
        """Handle GET requests."""
        url = urlparse(self.path)
        path = url.path
        query_params = parse_qs(url.query)

        try:
            if path == "/hello":
                self.json_response(200, {"state": True})
            elif path == "/mem":
                self.handle_mem_get(query_params)
            elif path == "/robot":
                self.handle_robot_get(query_params)
            else:
                self.text_response(404, "Not Found")
        except Exception as e:
            self.text_response(500, f"Internal Server Error: {str(e)}")

    def do_POST(self):
        """Handle POST requests."""
        url = urlparse(self.path)
        path = url.path
        content_length = int(self.headers["Content-Length"])
        body = self.rfile.read(content_length).decode("utf-8")

        print(f"POST request: path={path}, body={body}")

        try:
            body_data = json.loads(body)
        except json.JSONDecodeError:
            return self.text_response(400, "Invalid JSON format")

        try:
            if path == "/mem":
                self.handle_mem_set(body_data)
            elif path == "/robot_DO":
                self.handle_robot_DO(body_data)
            else:
                self.text_response(404, "Not Found")
        except Exception as e:
            self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})

    #~ GET request handlers
    def handle_mem_get(self, query_params):
        """Handle GET /mem with query parameters."""
        try:
            name = query_params.get("name", [None])[0]

            if not name:
                return self.json_response(400, {"error": "Missing 'name' in query parameters"})

            if name == "status":
                return self.json_response(200, {"status": mem.status})
            else:
                return self.json_response(400, {"error": f"Invalid 'name' value: {name}"})
        except Exception as e:
            self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})

    def handle_robot_get(self, query_params):
        """Handle GET /robot with query parameters."""
        try:
            name = query_params.get("name", [None])[0]

            if not name:
                return self.json_response(400, {"error": "Missing 'name' in query parameters"})

            if name == "frame":
                frame = [round(value, 3) for value in robot.get_frame(isdegs=True)[1]]
                return self.json_response(200, {"frame": frame})
            elif name == "tool":
                tool = [round(value, 3) for value in robot.get_tool(isdegs=True)[1]]
                return self.json_response(200, {"tool": tool})
            elif name == "tcp_pose":
                pose = [round(value, 3) for value in robot.get_tcp_pose()]
                return self.json_response(200, {"pose": pose})
            elif name == "transformation_data":
                frame = [round(value, 3) for value in robot.get_frame(isdegs=True)[1]]
                tool = [round(value, 3) for value in robot.get_tool(isdegs=True)[1]]
                pose = [round(value, 3) for value in robot.get_tcp_pose()]

                data_package = {
                    "frame": frame,
                    "tool": tool,
                    "pose": pose,
                    "camera_tool": settings.camera_tool,
                    "x_boundary_range": settings.x_boundary_range,
                    "y_boundary_range": settings.y_boundary_range,
                    "z_boundary_range": settings.z_boundary_range
                }
                return self.json_response(200, data_package)
            elif name == "is_in_pos":
                is_in_pos = robot.is_in_pos()[1]
                return self.json_response(200, {"is_in_pos": is_in_pos})
            else:
                self.json_response(400, {"error": "Invalid or missing 'name' parameter"})
        except Exception as e:
            self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})

    #~ POST request handlers
    def handle_mem_set(self, body_data):
        """Handle setting memory values via POST request."""
        try:
            name = body_data.get("name")
            value = body_data.get("value")

            if not name or value is None:
                self.json_response(400, {"error": "Missing 'name' or 'value' in request body"})
                return

            if name == "program":
                value = int(value)    
                mem.program = value
                self.json_response(200, {"status": "success"})
            elif name == "speed_multiplier":
                value = int(value)
                mem.speed_multiplier = value / 100
                self.json_response(200, {"status": "success"})
            elif name == "desired_force":
                value = int(value)
                mem.desired_force = value
                self.json_response(200, {"status": "success"})
            elif name == "generator1_target_pairs":
                if not isinstance(value, list):
                    self.json_response(400, {"error": "generator1_target_pairs requires 'value' to contain a list"})
                    return
                mem.generator1_target_pairs = value
                self.json_response(200, {"status": "success"})
            else:
                self.json_response(404, {"error": f"Variable '{name}' Not Found"})
        except Exception as e:
            self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})
    
    def handle_robot_DO(self, body_data):
        try:
            name = body_data.get("name")
            value = body_data.get("value")

            if not name or value is None:
                self.json_response(400, {"error": "Missing 'name' or 'value' in request body"})
                return
            
            try:
                pin_number = int(name)
            except ValueError:
                if name == "force_sensor":
                    pin_number = settings.force_sensor_pin
                elif name == "angle_grinder":
                    pin_number = settings.angle_grinder_pin
                elif name == "emergency_output":
                    pin_number = settings.emergency_output_pin
                else:
                    self.json_response(404, {"error": f"Invalid 'name': {name}"})
                    return

            if value == "toggle":
                pin_val = not robot.get_DO(pin_number)
            elif value in ["True", "False"]:
                pin_val = value == "True"
            else:
                pin_val = bool(int(value))
            
            robot.set_DO(pin_number, pin_val)
            self.json_response(200, {"status": "success"})
        except Exception as e:
            self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})

    # def log_message(self, format, *args):
    #     """Suppress default HTTP logging (optional)."""
    #     return

#~ Server
class JakaHttpServer(HTTPServer):
    def __init__(self, port=settings.jaka_server_port):
        super().__init__(('', port), JakaHttpHandler)

    def run_server(self):
        """ Run the server in a new thread """
        print(f"Server started at port {self.server_port}")
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop_server(self):
        """ Stop the server gracefully """
        self.shutdown()  # This will stop serve_forever() loop
        self.server_close()
        print("Server stopped")


server = JakaHttpServer()





if __name__ == '__main__':
    robot.init()
    server.run_server()

    try:
        while True:
            time.sleep(0.25)
    except KeyboardInterrupt:
        pass

    server.stop_server()


