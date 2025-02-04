import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from utils.config import settings, idata
from utils.memory import mem, atdata
from utils.D435_rpi import D435, rgbd_read_data
from utils.img_processing import rgbd_depth_filter


#~ Server handler
class RpiHttpHandler(SimpleHTTPRequestHandler):
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
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return
    
    def do_GET(self):
        """Handle GET requests."""
        url = urlparse(self.path)
        query = parse_qs(url.query)
        path = url.path
        
        if path == '/hello':
            self.json_response(200, {"state": True})
        elif path == '/take_pic':
            try:
                d435 = D435()
                rgbd_data = d435.get_data(save=True)
                # mem.custom_signal.emit('take_pic')
                # idata.custom_signal.emit('take_pic')
                self.json_response(200, {"status": "success", "message": "Image captured!"})
            except Exception as e:
                self.json_response(500, {"error": f"Internal Server Error: {str(e)}"})
        else:
            self.text_response(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests."""
        url = urlparse(self.path)
        path = url.path
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')

        print(f'POST request: path={path}, body={body}')

        try:
            body_data = json.loads(body)
        except json.JSONDecodeError:
            return self.text_response(400, "Invalid JSON format")

        if path == "/mem":
            self.handle_set_mem(body_data)
        elif path == "/ATPrograms":
            self.handle_ATPrograms(body_data)
        else:
            self.text_response(404, "Not Found")

    def handle_set_mem(self, body_data):
        """Handle setting memory values via POST request."""
        name = body_data.get("name")
        value = body_data.get("value")

        # Validate input
        if name is None or value is None:
            return self.text_response(400, "Missing 'name' or 'val' in request body")

        if name == 'status':
            # Update the status and return the new value
            mem.status = str(value)
            return self.json_response(200, {"status": "success"})
        else:
            # Handle invalid 'name' values
            return self.text_response(400, f"Invalid 'name' value: {name}")

    def handle_ATPrograms(self, body_data):
        """Handle setting memory values via POST request."""
        name = body_data.get("name")
        value = body_data.get("value")

        print(f'name: {name}')
        print(f'value: {value}')

        if name is None or value is None:
            return self.text_response(400, "Missing 'name' or 'value' in request body")

        if name == 'apriltag_target_runner':
            required_keys = {"frame", "tool", "pose", "camera_tool"}
            if not isinstance(value, dict) or not required_keys.issubset(value.keys()):
                print(f'Invalid value format. Expected keys: ....')
                return self.text_response(400, f"Invalid value format. Expected keys: {', '.join(required_keys)}")
            
            d435 = D435()
            rgbd_data = d435.get_data(save=True)
            rgbd_data, _ = rgbd_depth_filter(rgbd_data, 100, 1500)
            
            selected_detections = atdata.get_target_runner_detections(rgbd_data, robot_data=value)

            return self.json_response(200, {"status": "success", 
                                            "selected_detections": selected_detections,
                                            "program_selection": atdata.program_selection,
                                            "target_selections": atdata.target_selections
                                            })
        
        else:
            return self.text_response(400, f"Invalid 'name' value: {name}")

    # def log_message(self, format, *args):
    #     """Suppress default HTTP logging (optional)."""
    #     return


#~ Server
class RpiHttpServer(HTTPServer):
    def __init__(self, port=settings.rpi_port):
        super().__init__(("", port), RpiHttpHandler)

    def run_server(self):
        """ Run the server in a new thread """
        print(f"Server started at port {self.server_port}")
        threading.Thread(target=self.serve_forever, daemon=True).start()

    def stop_server(self):
        """ Stop the server gracefully """
        self.shutdown()  # This will stop serve_forever() loop
        self.server_close()
        print("Server stopped")


server = RpiHttpServer()














