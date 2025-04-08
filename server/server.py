from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import random
import signal
import sys

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set headers for CORS support"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()
    
    def do_GET(self):
        # Serve index.html for the root endpoint
        if self.path == '/':
            self.path = '/index.html'
        
        # Build the file path relative to the 'static' folder
        file_path = os.path.join(os.getcwd(), 'static', self.path.lstrip('/'))
        try:
            with open(file_path, 'rb') as file:
                self.send_response(200)
                if self.path.endswith('.html'):
                    self.send_header('Content-type', 'text/html')
                elif self.path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(file.read())
        except Exception as e:
            self.send_error(404, 'File not found: ' + self.path)

    def do_POST(self):
        # Define a simple API endpoint at /api
        if self.path == '/api':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data)
            except json.JSONDecodeError:
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'Invalid JSON')
                return

            # Process the data - mock success/failure for testing
            # 70% chance of success
            if random.random() < 0.7:
                response = {
                    'success': True, 
                    'message': 'Transaction processed successfully', 
                    'received': data,
                    'transactionId': f'TXN-{random.randint(1000, 9999)}'
                }
            else:
                # Generate different types of errors
                error_types = [
                    'Transaction validation failed',
                    'Server processing error',
                    'Database connection timeout',
                    'Invalid transaction format'
                ]
                error_message = random.choice(error_types)
                response = {
                    'success': False,
                    'message': error_message,
                    'errorCode': random.randint(400, 500)
                }
                
            response_data = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-Length', len(response_data))
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(response_data)
        else:
            self.send_error(404, 'Endpoint not found')

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print('\nShutting down the server gracefully...')
        httpd.server_close()
        print('Server has been shut down')
        sys.exit(0)
    
    # Register the signal handler for CTRL+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    print('Press CTRL+C to stop the server')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print('Server has been shut down')

if __name__ == '__main__':
    run()