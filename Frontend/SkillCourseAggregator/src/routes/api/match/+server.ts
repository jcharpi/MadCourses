import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
    const body = await event.request.json();

    // Forward the payload to your Python backend
    const res = await event.fetch('http://localhost:8000/match', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });

    return new Response(res.body, {
        status: res.status,
        headers: res.headers
    });
};
