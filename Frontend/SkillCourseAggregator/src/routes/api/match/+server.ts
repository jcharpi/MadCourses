import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
  const body = await event.request.json();

  const res = await fetch('https://charpi-madcourses-backend.hf.space/match', {
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
};
