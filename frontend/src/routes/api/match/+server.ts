import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
	const body = await event.request.json();

	// Use environment variable for backend URL
	const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000/api/match';

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
			headers: { 
				'Content-Type': res.headers.get('Content-Type') || 'application/json',
				'Access-Control-Allow-Origin': '*'
			}
		});
	} catch (error) {
		console.error('Failed to connect to Python API server:', error);
		return new Response(
			JSON.stringify({
				error: 'Backend API server not running. Please start it with: cd backend && python server.py'
			}),
			{
				status: 503,
				headers: { 'Content-Type': 'application/json' }
			}
		);
	}
};
