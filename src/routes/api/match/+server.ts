import type { RequestHandler } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';
import type { Course } from '$lib/database';

export const POST: RequestHandler = async ({ request }) => {
	try {
		const body = await request.json();
		const { skills, k = 5, ...filters } = body;

		if (!skills || !Array.isArray(skills) || skills.length === 0) {
			return new Response(JSON.stringify({ error: 'Skills array is required' }), {
				status: 400,
				headers: { 'Content-Type': 'application/json' }
			});
		}

		// Process match request
		const results = [];

		for (const skill of skills) {
			// Create skill embedding using Hugging Face API
			const embedding = await createSkillEmbedding(skill);

			// Load course data from Vercel Blob Storage
			const { courses, embeddings } = await loadCourseData(filters);

			// Compute similarities
			const similarities = computeSimilarities(embedding, embeddings);

			// Get top-k results
			const matches = getTopKMatches(courses, similarities, k);

			results.push({ skill, matches });
		}

		return new Response(JSON.stringify({ results }), {
			status: 200,
			headers: { 'Content-Type': 'application/json' }
		});
	} catch (error) {
		console.error('Match API error:', error);
		return new Response(
			JSON.stringify({ error: error instanceof Error ? error.message : 'Internal server error' }),
			{ status: 500, headers: { 'Content-Type': 'application/json' } }
		);
	}
};

// Helper functions
async function createSkillEmbedding(text: string): Promise<number[]> {
	const HUGGINGFACE_API_KEY = env.HUGGINGFACE_API_KEY;
	const HUGGINGFACE_API_URL =
		'https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L12-v2/pipeline/feature-extraction';

	if (!HUGGINGFACE_API_KEY) {
		throw new Error('HUGGINGFACE_API_KEY environment variable is not set');
	}

	const response = await fetch(HUGGINGFACE_API_URL, {
		method: 'POST',
		headers: {
			Authorization: `Bearer ${HUGGINGFACE_API_KEY}`,
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({ inputs: [text] })
	});

	if (!response.ok) {
		throw new Error(`Hugging Face API error: ${response.status} - ${await response.text()}`);
	}

	const embeddings = await response.json();
	const embedding = embeddings[0];

	// Normalize the embedding
	const norm = Math.sqrt(embedding.reduce((sum: number, val: number) => sum + val * val, 0));
	return norm > 0 ? embedding.map((val: number) => val / norm) : embedding;
}

async function loadCourseData(filters: {
	subject_contains?: string;
	level_min?: number;
	level_max?: number;
	credit_min?: number;
	credit_max?: number;
	last_taught?: string;
	last_taught_ge?: string;
}) {
	const { loadCourseData: loadData } = await import('$lib/database');

	// Convert filter format from frontend to database format
	const dbFilters = {
		subject_contains: filters.subject_contains,
		level_min: filters.level_min,
		level_max: filters.level_max,
		credit_min: filters.credit_min,
		credit_max: filters.credit_max,
		last_taught: filters.last_taught_ge || filters.last_taught
	};

	return await loadData(dbFilters);
}

function computeSimilarities(queryEmbedding: number[], courseEmbeddings: number[][]): number[] {
	return courseEmbeddings.map((courseEmbedding) => {
		// Compute dot product (cosine similarity for normalized vectors)
		return queryEmbedding.reduce((sum, val, i) => sum + val * courseEmbedding[i], 0);
	});
}

function getTopKMatches(courses: Course[], similarities: number[], k: number) {
	const indexed = similarities.map((sim, idx) => ({ idx, sim }));
	indexed.sort((a, b) => b.sim - a.sim);

	return indexed.slice(0, k).map(({ idx, sim }) => ({
		...courses[idx],
		similarity: sim
	}));
}