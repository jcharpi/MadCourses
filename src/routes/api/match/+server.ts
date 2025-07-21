import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
	const body = await event.request.json();

	// Determine backend URL based on environment
	const isDev = process.env.NODE_ENV === 'development';
	const BACKEND_URL = isDev
		? 'http://localhost:8001/match'
		: `${event.url.origin}/api/match`;

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
				error: isDev
					? 'Python API server not running. Please start it with: python api_server.py'
					: 'Internal server error'
			}),
			{
				status: 503,
				headers: { 'Content-Type': 'application/json' }
			}
		);
	}
};
