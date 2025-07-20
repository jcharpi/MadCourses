import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
	const body = await event.request.json();

	// In development, proxy to local Python API server
	// In production, Vercel will route /api/match directly to our Python function
	const BACKEND_URL = 'http://localhost:8001/match';

	try {
		const res = await fetch(BACKEND_URL, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(body)
		});

		// Relay the response exactly
		const text = await res.text();
		return new Response(text, {
			status: res.status,
			headers: { 'Content-Type': res.headers.get('Content-Type') || 'application/json' }
		});
	} catch (error) {
		console.error('Failed to connect to Python API server:', error);
		return new Response(
			JSON.stringify({
				error: 'Python API server not running. Please start it with: python api_server.py'
			}),
			{
				status: 503,
				headers: { 'Content-Type': 'application/json' }
			}
		);
	}
};
