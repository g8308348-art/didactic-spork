from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import signal
import sys
import logging
from datetime import datetime

# Add the parent directory to sys.path to allow importing from helpers
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from main_logic.py
from main_logic import (
    process_transaction, setup_logging, 
)

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

            # Ensure required fields are present
            if not all(key in data for key in ['transaction', 'action', 'user_comment']):
                self.send_response(400)
                self._set_cors_headers()
                self.end_headers()
                self.wfile.write(b'Missing required fields: transaction, action, user_comment')
                return
            
            # Create a temporary file with the transaction data
            try:
                # Ensure input directory exists
                with open(temp_file_path, 'w') as f:
                    f.write(f"{data['transaction']}\n{data['action']}\n{data['user_comment']}")
                
                # Process the transaction using our main logic
                from playwright.sync_api import sync_playwright
                with sync_playwright() as playwright:
                    process_transaction(playwright, temp_file_path)
                
                response = {
                    'status': 'success',
                    'message': f"Transaction {data['transaction']} processed successfully"
                }
            except Exception as e:
                logging.error(f"Error processing transaction: {str(e)}")
                response = {
                    'status': 'error',
                    'message': str(e)
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
    # Set up logging
    setup_logging()
    logging.info(f"Starting server on port {port}...")
    
    # Ensure directories exist
    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        logging.info('Shutting down the server gracefully...')
        httpd.server_close()
        logging.info('Server has been shut down')
        sys.exit(0)
    
    # Register the signal handler for CTRL+C (SIGINT)
    signal.signal(signal.SIGINT, signal_handler)
    
    logging.info('Press CTRL+C to stop the server')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        logging.info('Server has been shut down')

if __name__ == '__main__':
    run()