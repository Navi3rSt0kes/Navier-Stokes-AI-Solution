import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def respond(self, status, payload):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        self.respond(200, {'status': 'ok', 'service': 'ai-agent'})

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            message = json.loads(self.rfile.read(length)).get('message', '')
        except Exception:
            return self.respond(400, {'error': 'JSON inválido'})
        if not message:
            return self.respond(400, {'error': 'message es obligatorio'})
        self.respond(200, {'response': 'El agente está disponible y conectado al entorno MarkECIA.', 'recommendations': []})
