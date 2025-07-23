import adapter from '@sveltejs/adapter-vercel';
import adapterAuto from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	extensions: ['.svelte'],
	preprocess: [vitePreprocess()],

	kit: {
		// Use adapter-auto for local dev, Vercel will override this
		adapter: process.env.VERCEL ? adapter() : adapterAuto()
	}
};
export default config;
