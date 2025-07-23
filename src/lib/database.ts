import { head } from '@vercel/blob';
import { env } from '$env/dynamic/private';

export interface Course {
	id: number;
	subject: string;
	level: number;
	title: string;
	credit_amount: number;
	credit_min: number;
	credit_max: number;
	last_taught: string;
	description: string;
}

interface CourseWithEmbedding extends Course {
	embedding: number[];
}

// Global cache for performance
let _coursesCache: CourseWithEmbedding[] | null = null;

export async function loadCourseData(filters?: {
	subject_contains?: string;
	level_min?: number;
	level_max?: number;
	credit_min?: number;
	credit_max?: number;
	last_taught?: string;
}): Promise<{ courses: Course[]; embeddings: number[][] }> {
	// Load from cache if available
	if (_coursesCache) {
		return filterCourses(_coursesCache, filters);
	}

	try {
		// Try to load from Vercel Blob Storage
		const blobInfo = await head('courses.json', {
			token: env.BLOB_READ_WRITE_TOKEN
		});
		if (blobInfo) {
			const response = await fetch(blobInfo.downloadUrl);
			const coursesData = (await response.json()) as CourseWithEmbedding[];
			_coursesCache = coursesData;
			return filterCourses(coursesData, filters);
		}

		throw new Error('Database not found in blob storage');
	} catch (error) {
		console.error('Error loading course data from blob storage:', error);

		// Fallback: Try to load from local file (development)
		try {
			const fs = await import('fs/promises');
			const path = await import('path');

			// Try multiple possible paths for the JSON file
			const possiblePaths = [
				path.join(process.cwd(), 'courses.json') // Same directory as package.json
			];

			let coursesData: CourseWithEmbedding[] | null = null;

			for (const jsonPath of possiblePaths) {
				try {
					const jsonData = await fs.readFile(jsonPath, 'utf-8');
					coursesData = JSON.parse(jsonData) as CourseWithEmbedding[];
					console.log(`Loaded course data from: ${jsonPath}`);
					break;
				} catch {
					// Try next path
					continue;
				}
			}

			if (!coursesData) {
				throw new Error('courses.json not found in any expected location');
			}

			_coursesCache = coursesData;
			return filterCourses(coursesData, filters);
		} catch (fallbackError) {
			console.error('Error loading course data from local file:', fallbackError);
			throw new Error('Course data not available - please upload to blob storage');
		}
	}
}

function filterCourses(
	courses: CourseWithEmbedding[],
	filters?: {
		subject_contains?: string;
		level_min?: number;
		level_max?: number;
		credit_min?: number;
		credit_max?: number;
		last_taught?: string;
	}
): { courses: Course[]; embeddings: number[][] } {
	let filtered = courses;

	if (filters) {
		filtered = courses.filter((course) => {
			if (
				filters.subject_contains &&
				!course.subject.toLowerCase().includes(filters.subject_contains.toLowerCase())
			) {
				return false;
			}
			if (filters.level_min && course.level < filters.level_min) {
				return false;
			}
			if (filters.level_max && course.level > filters.level_max) {
				return false;
			}
			if (filters.credit_min && course.credit_max < filters.credit_min) {
				return false;
			}
			if (filters.credit_max && course.credit_min > filters.credit_max) {
				return false;
			}
			if (filters.last_taught && course.last_taught < filters.last_taught) {
				return false;
			}
			return true;
		});
	}

	return {
		courses: filtered.map((course) => {
			// eslint-disable-next-line @typescript-eslint/no-unused-vars
			const { embedding, ...courseWithoutEmbedding } = course;
			return courseWithoutEmbedding;
		}),
		embeddings: filtered.map((course) => course.embedding)
	};
}
