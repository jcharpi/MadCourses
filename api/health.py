#!/usr/bin/env python3
"""
Simple health check function for Vercel debugging
"""

import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        response = json.dumps({'status': 'ok', 'message': 'Health check passed'})
        self.wfile.write(response.encode())