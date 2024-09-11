import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from utils.config import settings, idata
from utils.memory import mem


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














