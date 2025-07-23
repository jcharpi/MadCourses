#!/usr/bin/env node
/**
 * Upload courses.json to Vercel Blob Storage
 * Run this locally after exporting the database to JSON
 */

import { put } from '@vercel/blob';
import { readFile } from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function uploadToBlob() {
    try {
        // Read the JSON file
        const jsonPath = join(__dirname, '..', 'courses.json');
        const jsonData = await readFile(jsonPath, 'utf-8');
        
        console.log(`Uploading ${(jsonData.length / 1024 / 1024).toFixed(2)} MB to Vercel Blob Storage...`);
        
        // Upload to Vercel Blob Storage
        const blob = await put('courses.json', jsonData, {
            access: 'public',
            contentType: 'application/json'
        });
        
        console.log('Upload successful!');
        console.log('Blob URL:', blob.url);
        console.log('Blob size:', blob.size, 'bytes');
        
    } catch (error) {
        console.error('Upload failed:', error);
        process.exit(1);
    }
}

uploadToBlob();