<script lang="ts">
  /* ------------------------------------------------------------
     🎓 MadCourses – UW‑Madison skill → course matcher (Svelte)
     Palette: UW red (#C5050C) primary, black text, pale backgrounds,
              subtle yellow accent (amber‑400)
     ------------------------------------------------------------ */

  interface Course {
    id: number;
    subject: string;
    level: number;
    title: string;
    credit_amount: number;
    last_taught: string;
  }

  // —— Mock state ————————————————————————————————
  import { writable, derived, get } from "svelte/store";

  const skills = writable<string[]>(["data analysis", "creative writing"]);
  const newSkill = writable("");

  const filters = writable({
    subject: "",
    levelMin: "",   // selectors – blank by default
    levelMax: "",
    creditMin: "",  // numeric but start empty → placeholders only
    creditMax: "",
    lastTaught: ""
  });

  // 5 mock courses per skill
  const mockCourses: Course[] = Array.from({ length: 10 }).map((_, i) => ({
    id: i + 1,
    subject: i % 2 ? "COMP SCI" : "ENGL",
    level: 100 + i * 10,
    title: `Sample Course Title ${i + 1}`,
    credit_amount: 3,
    last_taught: i % 2 ? "F24" : "S24"
  }));

  const activeSkill = writable<string>("data analysis");
  const coursesForActiveSkill = derived([activeSkill], ([$activeSkill]) => {
    return mockCourses.slice(0, 5);
  });

  function addSkill() {
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
    if (get(activeSkill) === skill && get(skills).length) {
      activeSkill.set(get(skills)[0]);
    }
  }

  function search() {
    console.log("Searching with", {
      skills: get(skills),
      filters: get(filters)
    });
  }
</script>

<style>
  /* unify text selection highlight */
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
    <h2 class="text-lg font-medium">Filters</h2>

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
          <label for="levelMin" class="font-medium">Level min</label>
          <select
            id="levelMin"
            bind:value={$filters.levelMin}
            class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
          >
            <option value="" disabled selected>Select</option>
            {#each Array.from({ length: 9 }).map((_, i) => (i + 1) * 100) as lvl}
              <option value={lvl}>{lvl}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label for="levelMax" class="font-medium">Level max</label>
          <select
            id="levelMax"
            bind:value={$filters.levelMax}
            class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
          >
            <option value="" disabled selected>Select</option>
            {#each Array.from({ length: 9 }).map((_, i) => (i + 1) * 100) as lvl}
              <option value={lvl}>{lvl}</option>
            {/each}
          </select>
        </div>
      </div>

      <!-- Credit range -->
      <div class="grid grid-cols-2 gap-4">
        <div class="flex flex-col gap-1">
          <label for="creditMin" class="font-medium">Credits min</label>
          <input
            id="creditMin"
            type="number"
            min="1"
            placeholder="min"
            bind:value={$filters.creditMin}
            class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
          />
        </div>
        <div class="flex flex-col gap-1">
          <label for="creditMax" class="font-medium">Credits max</label>
          <input
            id="creditMax"
            type="number"
            min="1"
            placeholder="max"
            bind:value={$filters.creditMax}
            class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
          />
        </div>
      </div>

      <!-- Last taught -->
      <div class="flex flex-col gap-1">
        <label for="lastTaught" class="font-medium">Last taught</label>
        <select
          id="lastTaught"
          bind:value={$filters.lastTaught}
          class="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-red-600 focus:border-red-600"
        >
          <option value="" disabled selected>Any</option>
          <option value="F24">F24</option>
          <option value="S24">S24</option>
          <option value="U24">U24</option>
        </select>
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
      <span class="text-sm text-gray-500">(top 5 for each skill)</span>
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
          <h3 class="font-semibold text-lg mb-1">{course.subject} {course.level} – {course.title}</h3>
          <p class="text-sm text-gray-600 mb-1">Credits: {course.credit_amount}</p>
          <p class="text-sm text-gray-600">Last taught: {course.last_taught}</p>
        </li>
      {/each}
    </ul>
  </section>
</main>
