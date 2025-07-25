<script lang="ts">
	/* ===================================================================
     MADCOURSES - UW-Madison Skill-to-Course Matching System (Svelte)
     Design Palette:
       Primary: UW Red (#C5050C)
       Text: Black
       Backgrounds: Pale neutrals
       Accent: Subtle yellow (amber-400)
     =================================================================== */

	/* ─────────────────────────────  Imports  ───────────────────────────── */
	import { writable, derived, get } from 'svelte/store';
	import { onMount } from 'svelte';

	// === About tooltip state ===
	let aboutOpen = false;
	let aboutWrapper: HTMLElement;

	function toggleAbout() {
		aboutOpen = !aboutOpen;
	}

	onMount(() => {
		/* runs client‑side only */
		function handleClickOutside(event: MouseEvent) {
			if (aboutOpen && aboutWrapper && !aboutWrapper.contains(event.target as Node)) {
				aboutOpen = false;
			}
		}

		window.addEventListener('click', handleClickOutside);

		/* return cleanup → called automatically when component unmounts (client only) */
		return () => window.removeEventListener('click', handleClickOutside);
	});

	// ===== TYPE DEFINITIONS =====
	interface Course {
		id: number;
		subject: string;
		level: number;
		title: string;
		similarity: number;
		credit_amount: number;
		last_taught: string;
	}

	// ===== REACTIVE STATE =====
	// Skill management
	const skills = writable<string[]>([]);
	const newSkill = writable('');

	// Search filters (initialized as empty)
	const filters = writable({
		subject: '',
		levelMin: '',
		levelMax: '',
		creditMin: '',
		creditMax: '',
		lastTaught: '',
		k: '3'
	});

	// Reactive credit validation
	$: {
		const minVal = Number($filters.creditMin);
		if (
			minVal > 0 && // Only validate when min is positive
			$filters.creditMax !== '' && // Max must not be empty
			Number($filters.creditMax) < minVal
		) {
			// Ensure creditMax >= creditMin
			filters.update((f) => ({
				...f,
				creditMax: f.creditMin
			}));
		}
	}

	// Filter reset functionality
	function resetFilters() {
		filters.set({
			subject: '',
			levelMin: '',
			levelMax: '',
			creditMin: '',
			creditMax: '',
			lastTaught: '',
			k: '3'
		});
		// Only search if we have skills
		const currentSkills = get(skills).filter((s) => s.trim());
		if (currentSkills.length > 0) {
			search();
		}
	}

	// Active skill selection
	const activeSkill = writable<string>('');

	// API results storage and loading state
	const results = writable<Array<{ skill: string; matches: Course[] }>>([]);
	const isLoading = writable(false);
	const isFirstSearch = writable(true);

	// Derived active skill courses
	const coursesForActiveSkill = derived([results, activeSkill], ([$results, $activeSkill]) => {
		const block = $results.find((b) => b.skill === $activeSkill);
		return block ? block.matches : [];
	});

	// ===== EVENT HANDLERS =====
	// Skill management
	function addSkill() {
		// Add new skill after validation
		newSkill.update((s) => s.trim());
		const value = get(newSkill);
		if (value && !get(skills).includes(value)) {
			skills.update((arr) => [...arr, value]);
			activeSkill.set(value);
		}
		newSkill.set('');
	}

	function removeSkill(skill: string) {
		// Remove skill and update active selection
		skills.update((arr) => arr.filter((s) => s !== skill));
		if (get(activeSkill) === skill && get(skills).length) {
			activeSkill.set(get(skills)[0]);
		}
	}

	// Search execution
	async function search() {
		// Prepare API payload
		const currentSkills = get(skills).filter((s) => s.trim());
		if (currentSkills.length === 0) return;

		// Set loading state
		isLoading.set(true);

		const f = get(filters);
		const payload: Record<string, unknown> = {
			skills: currentSkills,
			k: parseInt(f.k) || 3
		};

		// Apply active filters
		if (f.subject) payload.subject_contains = f.subject;
		if (f.levelMin) payload.level_min = parseInt(f.levelMin);
		if (f.levelMax) payload.level_max = parseInt(f.levelMax) + 99;
		if (f.creditMin) payload.credit_min = parseFloat(f.creditMin);
		if (f.creditMax) payload.credit_max = parseFloat(f.creditMax);
		if (f.lastTaught) payload.last_taught = f.lastTaught;

		try {
			// Execute API request
			const res = await fetch('/api/match', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});

			if (!res.ok) {
				console.error('API error:', await res.text());
				return;
			}

			// Process results
			const json = await res.json();
			results.set(json.results);

			// Update active skill if needed
			if (!get(activeSkill) && currentSkills.length) {
				activeSkill.set(currentSkills[0]);
			}

			// Mark first search as complete
			isFirstSearch.set(false);
		} catch (err) {
			console.error('Fetch failed:', err);
		} finally {
			// Reset loading state
			isLoading.set(false);
		}
	}
</script>

<!-- ===== HEADER SECTION ===== -->
<header
	class="w-full bg-red-700 text-white px-6 py-4 shadow-md flex items-center justify-between select-none"
>
	<!-- App title with semester info -->
	<div class="flex items-baseline gap-3">
		<h1 class="text-2xl font-semibold tracking-wide">MadCourses</h1>
		<span class="text-sm text-red-200 font-medium">Fall 25-26 Courses</span>
	</div>

	<!-- About + click‑toggle tooltip -->
	<div class="relative inline-block ml-4" bind:this={aboutWrapper}>
		<!-- Trigger:    real <button> → built‑in keyboard support  -->
		<button
			type="button"
			class="cursor-pointer decoration-white/70 decoration-2 select-none focus:outline-none"
			aria-expanded={aboutOpen}
			aria-controls="about-tooltip"
			on:click|stopPropagation={toggleAbout}
		>
			About
		</button>

		{#if aboutOpen}
			<div
				id="about-tooltip"
				role="dialog"
				aria-modal="false"
				class="absolute right-0 mt-2 w-60 rounded-lg bg-white text-black text-sm p-4 shadow-lg border z-20"
			>
				<p>
					<strong>MadCourses</strong> is a personal project of mine that matches job skills with
					UW‑Madison courses. Enter skills, tweak the filters, then press <em>Search</em> to see which
					classes align best with what you hope to learn.
				</p>
				<br />
				<p>
					Developed by
					<strong>
						<a
							href="https://www.linkedin.com/in/josh-charpentier-79b1b9253/"
							target="_blank"
							class="font-semibold hover:text-red-700"
						>
							Josh Charpentier
						</a>
					</strong>
				</p>
			</div>
		{/if}
	</div>
</header>

<!-- ===== MAIN LAYOUT ===== -->
<main
	class="grid gap-6 p-6 bg-white text-black min-h-screen xl:grid-cols-12 xl:divide-x xl:divide-gray-200"
>
	<!-- Skills Column -->
	<section class="col-span-12 xl:col-span-3 flex flex-col gap-6">
		<h2 class="text-xl font-semibold">Skills</h2>

		<!-- Skill input -->
		<div class="flex gap-2 items-end">
			<div class="flex-1">
				<label for="skill-input" class="sr-only">Add skill</label>
				<input
					id="skill-input"
					bind:value={$newSkill}
					type="text"
					placeholder="e.g. data analysis"
					class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
					on:keydown={(e) => e.key === 'Enter' && addSkill()}
				/>
			</div>
			<button
				class="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-red-600"
				on:click={addSkill}>Add</button
			>
		</div>

		<!-- Skills list -->
		<ul class="space-y-2 overflow-visible pb-6">
			{#each $skills as skill}
				<li
					class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-3 py-2"
				>
					<button
						on:click={() => activeSkill.set(skill)}
						class="flex-1 text-left {skill === $activeSkill ? 'font-semibold text-red-700' : ''}"
						>{skill}</button
					>
					<button
						class="ml-2 text-gray-500 hover:text-red-600 focus:outline-none"
						aria-label={`Remove ${skill}`}
						on:click={() => removeSkill(skill)}>&times;</button
					>
				</li>
			{/each}
		</ul>
	</section>

	<!-- Filters Column -->
	<section class="col-span-12 xl:col-span-3 flex flex-col gap-6 px-0 xl:px-6">
		<div class="flex items-center justify-between mb-4">
			<h2 class="text-xl font-semibold">Filters</h2>

			<!-- Filter reset -->
			<button
				on:click={resetFilters}
				class="text-sm px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-400"
			>
				Reset
			</button>
		</div>

		<div class="space-y-4">
			<!-- Subject filter -->
			<div class="flex flex-col gap-1">
				<label for="subject" class="font-medium">Subject contains</label>
				<input
					id="subject"
					type="text"
					placeholder="e.g. COMP SCI"
					bind:value={$filters.subject}
					class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
				/>
			</div>

			<!-- Level filters -->
			<div class="grid grid-cols-2 gap-4">
				<div class="flex flex-col gap-1">
					<label for="levelMin" class="font-medium">Level min</label>
					<select
						id="levelMin"
						bind:value={$filters.levelMin}
						class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
					>
						<option value="" selected>Select</option>
						{#each Array.from({ length: 9 }).map((_, i) => (i + 1) * 100) as lvl}
							<option value={lvl}>{lvl}s</option>
						{/each}
					</select>
				</div>
				<div class="flex flex-col gap-1">
					<label for="levelMax" class="font-medium">Level max</label>
					<select
						id="levelMax"
						bind:value={$filters.levelMax}
						class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
					>
						<option value="" selected>Select</option>
						{#each Array.from({ length: 9 }).map((_, i) => (i + 1) * 100) as lvl}
							<option value={lvl}>{lvl}s</option>
						{/each}
					</select>
				</div>
			</div>

			<!-- Credit filters -->
			<div class="grid grid-cols-2 gap-4">
				<div class="flex flex-col gap-1">
					<label for="creditMin" class="font-medium">Credits min</label>
					<input
						id="creditMin"
						type="number"
						min="1"
						step="1"
						placeholder="min"
						bind:value={$filters.creditMin}
						class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
					/>
				</div>
				<div class="flex flex-col gap-1">
					<label for="creditMax" class="font-medium">Credits max</label>
					<input
						id="creditMax"
						type="number"
						min={$filters.creditMin ? $filters.creditMin : 1}
						step="1"
						placeholder="max"
						bind:value={$filters.creditMax}
						class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
					/>
				</div>
			</div>

			<!-- Semester filter -->
			<div class="flex flex-col gap-1">
				<label for="lastTaught" class="font-medium">Last taught</label>
				<select
					id="lastTaught"
					bind:value={$filters.lastTaught}
					class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
				>
					<option value="" selected>Any</option>
					<option value="F24">F24</option>
					<option value="S25">S25</option>
					<option value="U25">U25</option>
				</select>
			</div>

			<!-- Results count -->
			<div class="flex flex-col gap-1">
				<label for="k" class="font-medium">Number of matches per skill (1-10)</label>
				<input
					id="k"
					type="number"
					min="1"
					max="10"
					placeholder="3"
					bind:value={$filters.k}
					class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
				/>
			</div>

			<!-- Search trigger -->
			<button
				class="w-full {$isLoading
					? 'bg-red-700'
					: 'bg-red-600 hover:bg-red-700'} text-white font-semibold px-4 py-3 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-red-600 mt-4 flex items-center justify-center gap-2"
				on:click={search}
				disabled={$isLoading}
			>
				{#if $isLoading}
					<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
						<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"
						></circle>
						<path
							class="opacity-75"
							fill="currentColor"
							d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
						></path>
					</svg>
					{$isFirstSearch ? 'Caching...' : 'Searching...'}
				{:else}
					Search
				{/if}
			</button>
		</div>
	</section>

	<!-- Results Column -->
	<section class="col-span-12 xl:col-span-6 flex flex-col gap-6 px-0 xl:px-6">
		<h2 class="text-xl font-semibold flex items-center gap-2">
			Results
			<span class="text-sm text-gray-500">(top matches for each skill)</span>
		</h2>

		<!-- Skill tabs -->
		<div class="flex gap-2 overflow-x-auto pb-2">
			{#each $skills as skill}
				<button
					class="px-4 py-2 rounded-full border capitalize border-gray-300 whitespace-nowrap transition-all
                 {skill === $activeSkill
						? 'bg-red-600 text-white border-red-600'
						: 'bg-white hover:bg-gray-100'}"
					on:click={() => activeSkill.set(skill)}>{skill}</button
				>
			{/each}
		</div>

		<!-- Courses list -->
		<ul class="space-y-4 overflow-y-auto pr-2 pb-10" style="max-height: calc(100vh - 280px);">
			{#each $coursesForActiveSkill as course}
				<li
					class="bg-white border border-gray-200 rounded-xl p-4 shadow hover:shadow-md transition-shadow select-text"
				>
					<h3 class="font-semibold text-lg mb-1">
						{course.subject}
						{course.level} – {course.title}
					</h3>
					<p class="text-sm text-gray-600">
						Credits: {course.credit_amount} | Last Taught: {course.last_taught
							? course.last_taught
							: 'N/A'} | Similarity: {course.similarity.toFixed(3)}
					</p>
				</li>
			{/each}

			<!-- Empty states -->
			{#if $coursesForActiveSkill.length === 0}
				{#if get(results).length === 0}
					<li class="text-center text-gray-500 py-4">Hit the search button to find courses!</li>
				{:else}
					<li class="text-center text-gray-500 py-4">No results to display.</li>
				{/if}
			{/if}
		</ul>
	</section>
</main>

<!-- ===== GLOBAL STYLES ===== -->
<style>
	::selection {
		background: #c5050c; /* UW red */
		color: white;
	}
</style>
