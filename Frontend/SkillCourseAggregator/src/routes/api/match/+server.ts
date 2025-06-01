import type { RequestHandler } from '@sveltejs/kit';

/**
 * PROXY ENDPOINT: Skill Matching API Gateway
 * ───────────────────────────────────────────
 * Forwards POST requests to Python backend API
 * Maintains request/response integrity
 * 
 * Route: POST /match → Python backend (localhost:8000)
 * 
 * Why this exists:
 * 1. Avoids CORS issues in development
 * 2. Provides single API surface for frontend
 * 3. Enables future auth/validation middleware
 */

export const POST: RequestHandler = async (event) => {
    // ─── REQUEST HANDLING ──────────────────────────────────
    // 1. Parse incoming JSON payload from frontend
    // 2. Maintain original data structure integrity
    const body = await event.request.json();

    // ─── BACKEND FORWARDING ────────────────────────────────
    // Proxy request to Python API with these characteristics:
    // • Preserves HTTP method (POST)
    // • Maintains content type (application/json)
    // • Passes through exact request body
    const res = await event.fetch('http://localhost:8000/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    // ─── RESPONSE RELAY ───────────────────────────────────
    // Return Python backend response with:
    // • Original status code (200, 400, 500, etc.)
    // • Identical response body
    // • Same headers (content-type, etc.)
    return new Response(res.body, {
        status: res.status,
        headers: res.headers
    });
};