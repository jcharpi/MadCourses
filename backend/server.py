#!/usr/bin/env python3
"""
MadCourses Production Server for Render.com
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import match module
try:
    from match import match_courses
    logger.info("Successfully imported RAG modules")
except ImportError as e:
    logger.error(f"Failed to import match module: {e}")
    exit(1)

PORT = int(os.environ.get('PORT', 8000))

class APIHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self._send_json({'status': 'healthy', 'service': 'MadCourses RAG API'})
        elif self.path == '/':
            self._send_json({'message': 'MadCourses RAG API', 'endpoints': {'POST /api/match': 'Course matching'}})
        else:
            self._send_json({'error': 'Not found'}, 404)

    def do_POST(self):
        if self.path != '/api/match':
            self._send_json({'error': 'Not found'}, 404)
            return

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            skills = data.get('skills', [])
            if not skills:
                self._send_json({'error': 'Skills required'}, 400)
                return

            k = min(max(int(data.get('k', 5)), 1), 20)

            # Extract filters
            filters = {}
            if data.get('subject_contains'): filters['subject_contains'] = data['subject_contains']
            if data.get('level_min'): filters['level_min'] = int(data['level_min'])
            if data.get('level_max'): filters['level_max'] = int(data['level_max'])
            if data.get('credit_min'): filters['credit_min'] = float(data['credit_min'])
            if data.get('credit_max'): filters['credit_max'] = float(data['credit_max'])
            if data.get('last_taught'): filters['last_taught_ge'] = data['last_taught']

            logger.info(f"Processing {len(skills)} skills with {len(filters)} filters")

            # Process each skill
            results = []
            for skill in skills:
                matches = match_courses(skill, k=k, **filters)
                results.append({'skill': skill, 'matches': matches})

            self._send_json({'results': results})

        except Exception as e:
            logger.error(f"Error: {e}")
            self._send_json({'error': str(e)}, 500)

if __name__ == '__main__':
    logger.info(f"Starting server on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), APIHandler)
    server.allow_reuse_address = True  # Allow port reuse
    logger.info("Server started successfully!")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested via Ctrl+C")
    finally:
        logger.info("Shutting down server...")
        server.shutdown()
        server.server_close()
        logger.info("Server stopped cleanly")