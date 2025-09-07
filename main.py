import http.server
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

class Storage:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(exist_ok=True)
        if not self.file_path.exists():
            self.file_path.write_text("{}")

    def read_messages(self):
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    def write_message(self, message_data):
        messages = self.read_messages()
        messages[str(datetime.now())] = message_data
        with open(self.file_path, 'w') as f:
            json.dump(messages, f, indent=2)

class Router:
    def __init__(self):
        self.routes = {'GET': {}, 'POST': {}}

    def add_route(self, method, path, handler):
        self.routes[method][path] = handler

    def handle_request(self, handler):
        parsed_path = urlparse(handler.path)
        method = handler.command
        route_handler = self.routes.get(method, {}).get(parsed_path.path)

        if route_handler:
            route_handler(handler)
        else:
            # Handle static files separately for simplicity in this example
            if method == 'GET':
                static_files = {
                    '/style.css': ('FullStack-Web-Development-hw3/style.css', 'text/css'),
                    '/logo.png': ('FullStack-Web-Development-hw3/logo.png', 'image/png')
                }
                if parsed_path.path in static_files:
                    filepath, content_type = static_files[parsed_path.path]
                    handler.send_file(filepath, content_type=content_type)
                    return
            
            handler.handle_error(404)

class MyHttpRequestHandler(http.server.BaseHTTPRequestHandler):
    router = Router()
    storage = Storage('storage/data.json')
    jinja_env = Environment(loader=FileSystemLoader('templates'))

    def do_GET(self):
        self.router.handle_request(self)

    def do_POST(self):
        self.router.handle_request(self)

    def send_file(self, filename, status=200, content_type='text/plain'):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.end_headers()
        try:
            with open(filename, 'rb') as f:
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.handle_error(404)

    def render_template(self, template_name, context={}):
        template = self.jinja_env.get_template(template_name)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(template.render(context).encode('utf-8'))

    def handle_error(self, status_code):
        self.send_file('FullStack-Web-Development-hw3/error.html', status_code, 'text/html')

# --- Handler Functions ---
def handle_index(handler):
    handler.send_file('FullStack-Web-Development-hw3/index.html', content_type='text/html')

def handle_message_page(handler):
    handler.send_file('FullStack-Web-Development-hw3/message.html', content_type='text/html')

def handle_read(handler):
    messages = handler.storage.read_messages()
    handler.render_template('read.html', {'messages': messages})

def handle_message_post(handler):
    content_length = int(handler.headers['Content-Length'])
    post_data = handler.rfile.read(content_length)
    data = parse_qs(post_data.decode('utf-8'))
    message_data = {
        'username': data.get('username', [''])[0],
        'message': data.get('message', [''])[0]
    }
    handler.storage.write_message(message_data)
    handler.send_response(302)
    handler.send_header('Location', '/message.html')
    handler.end_headers()

# --- Server Setup ---
def run(server_class=http.server.HTTPServer, handler_class=MyHttpRequestHandler, port=3000):
    # Register routes
    handler_class.router.add_route('GET', '/', handle_index)
    handler_class.router.add_route('GET', '/message.html', handle_message_page)
    handler_class.router.add_route('GET', '/read', handle_read)
    handler_class.router.add_route('POST', '/message', handle_message_post)

    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting httpd server on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()