#!/usr/bin/env python3
"""
Local test server for MadCourses RAG API
"""

import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

# Add the API directory to path
sys.path.append('api/python')
from match import match_courses

class LocalAPIHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/match':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"Received request: {data}")

                skills = data.get('skills', [])
                k = data.get('k', 5)

                # Extract filters
                filters = {
                    'subject_contains': data.get('subject_contains'),
                    'level_min': data.get('level_min'),
                    'level_max': data.get('level_max'),
                    'credit_min': data.get('credit_min'),
                    'credit_max': data.get('credit_max'),
                    'last_taught_ge': data.get('last_taught')
                }

                # Process each skill
                results = []
                for skill in skills:
                    matches = match_courses(skill, k=k, **filters)
                    results.append({
                        'skill': skill,
                        'matches': matches
                    })

                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                response = json.dumps({'results': results}, indent=2)
                self.wfile.write(response.encode())
                print(f"Sent {len(results)} skill results")

            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error_response = json.dumps({'error': str(e)})
                self.wfile.write(error_response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/api/match':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = json.dumps({
                'message': 'MadCourses RAG API - Local Test Server',
                'status': 'ready'
            })
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('localhost', port), LocalAPIHandler)
    print(f"Starting local test server on http://localhost:{port}")
    print(f"Test endpoint: http://localhost:{port}/api/match")
    print("Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
        server.shutdown()