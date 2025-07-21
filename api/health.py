#!/usr/bin/env python3
"""
Simple health check function for Vercel debugging
"""

import json

def handler(request):
    """Simple health check"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'status': 'ok', 'message': 'Health check passed'})
    }

def main(request):
    return handler(request)