#!/usr/bin/env node

import { readFile } from 'fs/promises';
import { join } from 'path';
import { put } from '@vercel/blob';
import { config } from 'dotenv';

// Load environment variables
config({ path: '.env' });

interface CourseWithEmbedding {
	id: number;
	subject: string;
	level: number;
	title: string;
	credit_amount: number;
	credit_min: number;
	credit_max: number;
	last_taught: string;
	description: string;
	embedding: number[];
}

async function uploadCourseDataToBlob(): Promise<void> {
	try {
		console.log('🚀 Starting upload to Vercel Blob Storage...');

		// Check if token is available
		const token = process.env.BLOB_READ_WRITE_TOKEN;
		if (!token) {
			console.error('❌ BLOB_READ_WRITE_TOKEN not found in .env');
			console.log('Please add your Vercel Blob Storage token to .env:');
			console.log('BLOB_READ_WRITE_TOKEN=your_token_here');
			process.exit(1);
		}

		console.log('✅ Token found, loading courses.json...');

		// Find and load courses.json file
		const possiblePaths = [
			join(process.cwd(), 'courses.json') // Same directory as package.json
		];

		let coursesData: CourseWithEmbedding[] | null = null;

		for (const jsonPath of possiblePaths) {
			try {
				const jsonData = await readFile(jsonPath, 'utf-8');
				coursesData = JSON.parse(jsonData) as CourseWithEmbedding[];
				console.log(`✅ Found courses.json at: ${jsonPath}`);
				console.log(`📊 Loaded ${coursesData.length} courses`);
				break;
			} catch {
				continue;
			}
		}

		if (!coursesData) {
			console.error('❌ courses.json not found in any expected location');
			console.log('Searched paths:');
			possiblePaths.forEach((path) => console.log(`  - ${path}`));
			process.exit(1);
		}

		// Calculate file size
		const jsonString = JSON.stringify(coursesData);
		const sizeInMB = (Buffer.byteLength(jsonString, 'utf8') / 1024 / 1024).toFixed(2);
		console.log(`📁 File size: ${sizeInMB} MB`);

		// Upload to Vercel Blob Storage
		console.log('🔄 Uploading to Vercel Blob Storage...');

		const blob = new Blob([jsonString], { type: 'application/json' });

		const result = await put('courses.json', blob, {
			access: 'public',
			token: token,
			allowOverwrite: true
		});

		console.log('✅ Upload successful!');
		console.log(`🔗 Blob URL: ${result.url}`);
		console.log(`📝 Download URL: ${result.downloadUrl}`);
		console.log(`🕒 Uploaded at: ${new Date().toISOString()}`);
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : 'Unknown error';
		console.error('❌ Upload failed:', errorMessage);
		if (errorMessage.includes('403') || errorMessage.includes('401')) {
			console.log('🔑 This might be a token authentication issue.');
			console.log('Please verify your BLOB_READ_WRITE_TOKEN is correct.');
		}
		process.exit(1);
	}
}

// Run the upload
uploadCourseDataToBlob();
