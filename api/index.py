import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        origin = self.headers.get('Origin')
        allowed = {item.strip() for item in __import__('os').environ.get('CORS_ORIGINS', 'https://markecia-web.vercel.app').split(',')}
        if origin in allowed:
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Vary', 'Origin')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_OPTIONS(self):
        origin = self.headers.get('Origin')
        allowed = {item.strip() for item in __import__('os').environ.get('CORS_ORIGINS', 'https://markecia-web.vercel.app').split(',')}
        if origin not in allowed:
            return self.respond(403, {'error': 'Origin is not allowed'})
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', origin)
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Vary', 'Origin')
        self.end_headers()

    def do_GET(self):
        self.respond(200, {'status': 'ok', 'service': 'ai-agent'})

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            message = json.loads(self.rfile.read(length)).get('message', '')
        except Exception:
            return self.respond(400, {'error': 'Invalid JSON'})
        if not message:
            return self.respond(400, {'error': 'message is required'})
        self.respond(200, {'response': 'The agent is available and connected to the MarkECIA environment.', 'recommendations': []})
