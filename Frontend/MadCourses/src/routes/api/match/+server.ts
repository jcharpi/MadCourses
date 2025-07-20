import type { RequestHandler } from '@sveltejs/kit';

export const POST: RequestHandler = async (event) => {
  const body = await event.request.json();

  // Use local backend for development, Vercel for production
  const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8001/match';
  
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
};
