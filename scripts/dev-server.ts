#!/usr/bin/env node

import { spawn, type ChildProcess } from 'child_process';

let devProcess: ChildProcess | null = null;

// Function to kill process gracefully
function killProcess(): void {
	if (devProcess) {
		console.log('\n🛑 Shutting down dev server...');

		// On Windows, kill the entire process tree
		if (process.platform === 'win32') {
			spawn('taskkill', ['/pid', devProcess.pid!.toString(), '/T', '/F'], {
				stdio: 'ignore'
			});
		} else {
			devProcess.kill('SIGTERM');
		}

		devProcess = null;
		console.log('✅ Dev server stopped');
	}
}

// Handle graceful shutdown
process.on('SIGINT', () => {
	killProcess();
	process.exit(0);
});

process.on('SIGTERM', () => {
	killProcess();
	process.exit(0);
});

// Handle Windows Ctrl+C
if (process.platform === 'win32') {
	process.on('SIGBREAK', () => {
		killProcess();
		process.exit(0);
	});
}

// Start the dev server
console.log('🚀 Starting dev server on port 8000...');
console.log('Press Ctrl+C to stop the server');

devProcess = spawn('npm', ['run', 'vite:dev'], {
	stdio: 'inherit',
	shell: true
});

devProcess.on('close', (code) => {
	if (code !== 0) {
		console.error(`Dev server exited with code ${code}`);
	}
	process.exit(code);
});

devProcess.on('error', (err) => {
	console.error('Failed to start dev server:', err);
	process.exit(1);
});