<script lang="ts">
  /* ------------------------------------------------------------
     🎓 MadCourses – UW-Madison skill → course matcher (Svelte)
     Palette: UW red (#C5050C) primary, black text, pale backgrounds,
              subtle yellow accent (amber-400)
     ------------------------------------------------------------ */

  import { writable, derived, get } from "svelte/store";

  // —— Types ————————————————————————————————
  interface Course {
    id: number;
    subject: string;
    level: number;
    title: string;
    similarity: number;
    credit_amount: number;
    last_taught: string;
  }

  // —— Reactive State —————————————————————————————
  // List of skills to search for
  const skills = writable<string[]>([]);
  const newSkill = writable("");

  // Filter controls (all start empty)
  const filters = writable({
    subject: "",
    levelMin: "",
    levelMax: "",
    creditMin: "",
    creditMax: "",
    lastTaught: "",
    k: "5"
  });

  // Reactive guard: whenever creditMin changes to a non‐empty number,
  // ensure creditMax ≥ creditMin.
  $: {
    const minVal = Number($filters.creditMin);
    if (
      minVal > 0 &&                    // only run when creditMin is a positive number
      $filters.creditMax !== "" &&     // and creditMax is not empty
      Number($filters.creditMax) < minVal
    ) {
      // bump creditMax up to match creditMin
      filters.update(f => ({
        ...f,
        creditMax: f.creditMin
      }));
    }
  }

  // Add this function to reset all filters back to empty strings:
  function resetFilters() {
    filters.set({
      subject: "",
      levelMin: "",
      levelMax: "",
      creditMin: "",
      creditMax: "",
      lastTaught: "",
      k: "5"
    });
    search()
  }
  
  // Which skill tab is currently active
  const activeSkill = writable<string>("");

  // Raw API results: array of { skill, matches: Course[] }
  const results = writable<Array<{ skill: string; matches: Course[] }>>([]);

  // Derived: the Course[] for whichever skill is active
  const coursesForActiveSkill = derived(
    [results, activeSkill],
    ([$results, $activeSkill]) => {
      const block = $results.find((b) => b.skill === $activeSkill);
      return block ? block.matches : [];
    }
  );

  // —— Handlers ————————————————————————————————

  function addSkill() {
    // Trim any whitespace, then if nonempty and not already present, add
    newSkill.update((s) => s.trim());
    const value = get(newSkill);
    if (value && !get(skills).includes(value)) {
      skills.update((arr) => [...arr, value]);
      activeSkill.set(value);
    }
    newSkill.set("");
  }

  function removeSkill(skill: string) {
    skills.update((arr) => arr.filter((s) => s !== skill));
    // If the removed skill was active, pick the first remaining skill
    if (get(activeSkill) === skill && get(skills).length) {
      activeSkill.set(get(skills)[0]);
    }
  }

  async function search() {
    // Build payload, turning empty strings into undefined so the server can ignore them
    const currentSkills = get(skills).filter((s) => s.trim());
    if (currentSkills.length === 0) {
      // Nothing to search
      return;
    }

    const f = get(filters);
    const payload: Record<string, unknown> = {
      skills: currentSkills,
      k: parseInt(f.k) || 5
    };

    if (f.subject) payload.subject_contains = f.subject;
    if (f.levelMin) payload.level_min = parseInt(f.levelMin);
    if (f.levelMax) payload.level_max = parseInt(f.levelMax) + 99;
    if (f.creditMin) payload.credit_min = parseFloat(f.creditMin);
    if (f.creditMax) payload.credit_max = parseFloat(f.creditMax);
    if (f.lastTaught) payload.last_taught = f.lastTaught;

    try {
      const res = await fetch("/api/match", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        console.error("API error:", await res.text());
        return;
      }

      const json = await res.json();
      // json.results is expected as Array<{ skill: string; matches: Course[] }>
      results.set(json.results);

      // If no activeSkill or activeSkill was removed, set to first skill
      if (!get(activeSkill) && currentSkills.length) {
        activeSkill.set(currentSkills[0]);
      }
    } catch (err) {
      console.error("Fetch failed:", err);
    }

    if (f.lastTaught) {
    const semester = f.lastTaught;
    const year = semester.substring(1);
}
  }
</script>

<style>
  ::selection {
    background: #c5050c; /* UW red */
    color: white;
  }
</style>

<!-- —— HEADER ———————————————————————————————— -->
<header class="w-full bg-red-700 text-white px-6 py-4 shadow-md flex items-center select-none">
  <h1 class="text-2xl font-semibold tracking-wide">MadCourses</h1>
</header>

<!-- —— MAIN GRID —————————————————————————————— -->
<main class="grid gap-6 p-6 bg-white text-black min-h-screen xl:grid-cols-12 xl:divide-x xl:divide-gray-200">
  <!-- Skills Column -->
  <section class="col-span-12 xl:col-span-3 flex flex-col gap-6">
    <h2 class="text-lg font-medium">Skills</h2>

    <!-- Add skill input -->
    <div class="flex gap-2 items-end">
      <div class="flex-1">
        <label for="skill-input" class="sr-only">Add skill</label>
        <input
          id="skill-input"
          bind:value={$newSkill}
          type="text"
          placeholder="e.g. data analysis"
          class="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
          on:keydown={(e) => e.key === "Enter" && addSkill()}
        />
      </div>
      <button
        class="bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-red-600"
        on:click={addSkill}
      >Add</button>
    </div>

    <!-- Skills list -->
    <ul class="space-y-2 overflow-visible pb-6">
      {#each $skills as skill}
        <li class="flex items-center justify-between bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
          <button
            on:click={() => activeSkill.set(skill)}
            class="flex-1 text-left {skill === $activeSkill ? 'font-semibold text-red-700' : ''}"
          >{skill}</button>
          <button
            class="ml-2 text-gray-500 hover:text-red-600 focus:outline-none"
            aria-label={`Remove ${skill}`}
            on:click={() => removeSkill(skill)}
          >&times;</button>
        </li>
      {/each}
    </ul>
  </section>

  <!-- Filters Column -->
  <section class="col-span-12 xl:col-span-3 flex flex-col gap-6 px-0 xl:px-6">
    <div class="flex items-center justify-between mb-4">
    <h2 class="text-xl font-semibold">Filters</h2>
    <!-- Reset button goes here: -->
      <button
        on:click={resetFilters}
        class="text-sm px-3 py-1 bg-red-100 text-red-800 rounded hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-400"
      >
        Reset
      </button>
    </div>

    <div class="space-y-4">
      <!-- Subject contains -->
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

      <!-- Level range selectors -->
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

      <!-- Credit range -->
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

      <!-- Last taught -->
      <div class="flex flex-col gap-1">
        <label for="lastTaught" class="font-medium">Last taught</label>
        <select
          id="lastTaught"
          bind:value={$filters.lastTaught}
          class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
        >
          <option value="" selected>Any</option>
          <option value="F24">F24</option>
          <option value="S24">S24</option>
          <option value="U24">U24</option>
        </select>
      </div>

      <div class="flex flex-col gap-1">
        <label for="k" class="font-medium">Number of matches per skill (1-10)</label>
        <input
          id="k"
          type="number"
          min="1"
          max="10"
          placeholder="5"
          bind:value={$filters.k}
          class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
        />
      </div>
      <!-- Search button -->
      <button
        class="w-full bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-3 rounded-lg shadow focus:outline-none focus:ring-2 focus:ring-red-600 mt-4"
        on:click={search}
      >Search</button>
    </div>
  </section>

  <!-- Results Column -->
  <section class="col-span-12 xl:col-span-6 flex flex-col gap-6 px-0 xl:px-6">
    <h2 class="text-lg font-medium flex items-center gap-2">
      Results
      <span class="text-sm text-gray-500">(top matches for each skill)</span>
    </h2>

    <!-- Skill tabs -->
    <div class="flex gap-2 overflow-x-auto pb-2">
      {#each $skills as skill}
        <button
          class="px-4 py-2 rounded-full border capitalize border-gray-300 whitespace-nowrap transition-all
                 {skill === $activeSkill ? 'bg-red-600 text-white border-red-600' : 'bg-white hover:bg-gray-100'}"
          on:click={() => activeSkill.set(skill)}
        >{skill}</button>
      {/each}
    </div>

    <!-- Courses list -->
    <ul class="space-y-4 overflow-y-auto pr-2 pb-10" style="max-height: calc(100vh - 280px);">
      {#each $coursesForActiveSkill as course}
        <li class="bg-white border border-gray-200 rounded-xl p-4 shadow hover:shadow-md transition-shadow select-text">
          <h3 class="font-semibold text-lg mb-1">{course.subject} {course.level} – {course.title}</h3>
          <p class="text-sm text-gray-600">
            Credits: {course.credit_amount} | 
            Last Taught: {course.last_taught ? course.last_taught : "N/A"} | 
            Similarity: {course.similarity.toFixed(3)}
          </p>
        </li>
      {/each}
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
