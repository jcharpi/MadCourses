import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
	const body = await event.request.json();

	// Point to local development server
	const BACKEND_URL = 'http://localhost:8000/api/match';

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
				error: 'Python API server not running. Please start it with: venv/Scripts/activate && python local_server.py'
			}),
			{
				status: 503,
				headers: { 'Content-Type': 'application/json' }
			}
		);
	}
};
