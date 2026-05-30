# FAQ

Questions that come up in practice, answered the way they actually get answered — with specifics, not platitudes.

## Setup and structure

### Do I have to use Obsidian?

No. The vault is plain markdown; any editor will read and write the same files. VS Code, Sublime, NeoVim with telescope, iA Writer, even plain TextEdit all work. Obsidian is recommended because its template system, graph view, and link-aware editing match the system’s design — but the engine neither requires it nor knows it exists.

### Can I use a different LLM provider?

Yes, with work. The engine’s LLM integration is isolated in `memex/llm.py` and `memex.llm.LLMClient`. Swapping Anthropic’s Claude for another provider means reimplementing that client against a different SDK and adjusting the prompt files if the new model responds better to a different structure. The retrieval layer, the schema, the CLI surface, and the filesystem contract are provider-agnostic.

### Can I run it on Windows?

Yes. The engine is pure Python 3.12+, uv-managed. Paths are handled via `pathlib` throughout. The cron-scheduling advice in `07-automation.md` is Unix-specific; on Windows, use Task Scheduler with an equivalent invocation.

### What if I already have an Obsidian vault — can I migrate?

Yes, with care. The steps:

- Back up the existing vault (`tar cz` or a git commit) before anything else.

- Add the two core notes (`<your-name>.md`, `memexlab.md`) if missing.

- Run `memex doctor` against the vault. Fix any folder-shape issues it reports.

- Run `memex migrate` (dry-run first, then `--apply`) to bring existing frontmatter up to schema.

- Run `memex lint`. Expect errors in existing notes whose frontmatter predates the schema; fix them one file at a time.

A vault with 500 existing notes takes about a day of focused migration work. A vault with 5,000 takes longer, but the work is incremental — you can keep using the vault during migration.

### Why the two core notes? Isn’t that over-engineered?

The two core notes are in every retrieval. The persona note tells the model who you are — your domains, your framings, your biases. The manifest note tells it how the vault works. Without both, the LLM’s outputs drift toward generic prose; with both, they sound like yours. The cost is five minutes of setup; the return is every LLM output from there forward.

## Daily practice

### How long should the weekly review take?

60–90 minutes. If it takes more than two hours, the inbox is backlogged and the next week should have a light capture diet. If it takes less than 30, you’re probably skipping steps — or the week was unusually light, which is fine.

### What if I can’t run memex lint in the middle of the day?

The scheduled daily lint handles the baseline. Running it manually is useful when you’re about to commit something sensitive (after a batch compile, after a schema change, before declaring a day done). Outside those moments, the daily cron is sufficient.

### Should I use daily notes?

Optional. Daily notes help if you need to trace decisions later — “what did I decide on 2026-02-14?” — and if you actually reread them. If you don’t, they become a chore, and the inbox + weekly review cover the same ground differently. Try two weeks of daily notes; if you’re not rereading any of them, stop.

### How do I decide what to capture?

Capture anything that surprises you, anything you disagree with, anything you find yourself citing in conversation, anything that might answer a question you’ve been circling. Capture is meant to be a low bar. The promotion decision (inbox → raw) is where selectivity happens — and selectivity there is easier because you aren’t choosing between capturing and not capturing, you’re choosing between keeping and deleting.

### What’s the difference between a tag and a wiki-link?

A wiki-link encodes “this note is about that specific thing.” A tag encodes “this note is related to that cross-cutting theme.” When a note references <your-company> specifically, it gets `[[<your-company>]]` — a link. When a note is about a theme <your-company> happens to be involved in, the theme gets a tag. Use both when both apply, but never use a tag where a link would work.

### What do I do with a captured idea I’m not sure about?

Let it sit in the inbox. The weekly review’s “delete” option is not a failure — it’s the system correctly deciding the idea wasn’t as durable as you thought. Three-quarters of inbox captures never deserve promotion. That’s normal.

## Compilation and LLM use

### Why can’t I compile directly from the inbox?

Inbox items are by design low-signal: URLs, half-sentences, fragments. Compiling them would produce low-signal atomic notes. The raw promotion step forces you to fetch full text, add frontmatter, and decide the source is worth keeping. Compile then has something real to work on.

### What if the compile output proposes ten atomic notes and I only want three?

Run the dry-run. Look at the proposed list. Identify the three you want. Either:

- Pre-edit the raw source to remove the sections that spawned the other seven. Re-run compile. Or:

- Apply all ten, then delete the seven unwanted notes immediately. Less elegant; sometimes faster.

Either path is fine. The engine doesn’t penalise re-runs.

### Compile output has a factual error that’s not in the source. Now what?

LLM hallucination. Don’t apply that note. Re-annotate the raw source with the correct fact highlighted, and re-compile. If the model keeps hallucinating the same error, the prompt needs adjusting — edit `prompts/compile.md` to tighten the constraint and test on the same source.

### How do I stop the LLM from making things up?

You don’t stop it entirely; LLMs make things up. You catch it by reading every compile and every output before applying. The engine is optimised for this: dry-runs, explicit apply, citation trails, and lint validation. The defensive posture is baked in.

### Should I edit the prompts?

Yes, over time. The prompts in `prompts/` are designed to be iterated on. If you notice compile consistently producing overly-long bodies, edit `prompts/compile.md` to ask for shorter bodies. If `qa` is citing weak sources too readily, tighten that prompt. Each edit is a versioned change; revert if quality regresses.

### What’s the difference between memex qa and memex index?

`qa` answers a specific question with a short note and inline citations. `index` builds a structured reading path or concept map over a topic area, useful when you want to orient yourself in a domain rather than get one answer. Use `qa` when you have a concrete question; use `index` when you want to see the landscape.

### Why is the essay exporter so much slower than qa?

Essay retrieval pulls a larger context window (~35k tokens vs ~25k for qa), and the generation is longer. Expect 20–40 seconds for an essay vs 5–10 for a qa. This is fine — essays are not a rapid-iteration mode.

## Folders and organisation

### Where does an idea that doesn’t fit anywhere go?

Inbox, always. If by the next weekly review it still doesn’t fit, it goes to `raw/` as a memo, or to `wiki/questions/` if it’s a question, or gets deleted. “Doesn’t fit anywhere” usually means “this isn’t canonical” — and non-canonical ideas are fine; they just live in inbox or raw rather than wiki.

### Should people’s notes go in people/ or be distributed across wiki/?

Both. The person’s note lives in `people/` — one file per entity, containing biography, affiliations, key positions you’ve tracked. The concepts the person discusses get their own atomic notes in `wiki/`, which link back to the entity note in `people/`. So `people/garry-tan.md` is the entity; `wiki/founder-market-fit.md` is a concept, linked from the entity note.

### Do I need all the underscore-prefixed output folders on day one?

No. Create them as needed. The engine will create them on first use anyway. The folders are documented in `03-folder-structure.md` so you know what to expect when you run `memex export essay` for the first time.

### What if an atomic note naturally fits two folders?

It shouldn’t. Atomic notes all live in `wiki/`. Curated entities (people, companies, philosophies, eras) live in their own folders. Projects live in `projects/`. The folder structure is strictly by type, not by topic — topics are handled by tags and links. If a note feels like it belongs in two folders, it probably wants to be split into two notes.

### Can I nest folders inside wiki/?

Possible, but discouraged. The flat-wiki convention keeps slugs globally unique, which makes retrieval and linking simpler. If you feel strongly you need subfolders (`wiki/stablecoins/`, `wiki/islamic-finance/`), you can — but the engine’s retrieval and lint are validated against the flat structure. Expect some rough edges.

## Schema and metadata

### The linter is complaining about a field I just added. How do I fix it?

The schema rejects unknown keys. Options:

- Drop the new field. If the information can live in the body or in a tag, use that instead.

- Add the field to the schema. Edit `memex/schemas.py`, write a migration in `memex/modes/migrate.py`, run `memex migrate`. This is correct for fields that’ll be used across many notes.

The linter is doing its job when it complains. Don’t silence it; either move the information or change the contract.

### Why latticework: [problem-1, problem-2] instead of something named?

The Latticework problems are your personal framing and are already defined in the persona note. Referring to them by number keeps the frontmatter compact; the semantic meaning is carried by the core note. If you want a named equivalent, create `latticework-problems/problem-1-seeing-reality.md` and link from the core note — but the frontmatter still uses the number.

### What date goes in date: for an engine-generated note?

The date of generation. An essay produced today has `date: 2026-04-19`, even if it cites notes from 2024. This matches the timeline chart’s bucketing model — outputs roll up to the date they were written.

### Do I tag curated notes with latticework:?

You can. A `companies/<your-company>.md` note could legitimately have `latticework: [problem-3]` (allocating time and energy — because <your-company> is where a big chunk of your time goes). But the Latticework framing is primarily for atomic wiki notes, where it answers “which of my five operating questions does this note help with?” For entities, the tagging is optional.

## Technical

### Does the engine work offline?

Partially. Deterministic modes — `doctor`, `migrate`, `rollback`, `lint`, `chart` — work entirely offline. LLM-driven modes — `compile`, `qa`, `index`, `export essay`, `export slides` — require network access to the Anthropic API. Everything else (reading, writing, linking in Obsidian) works offline always.

### How much does a month of use cost in API calls?

Depends on volume. A rough estimate:

- Compile: ~$0.10–$0.30 per compile with Claude Opus. 20 compiles a month → $2–$6.

- QA: ~$0.05 each. 50 queries a month → $2–$3.

- Essay: ~$0.30–$0.50 each. Four essays a month → $1.20–$2.

- Slides/index/chart: negligible compared to the above.

Total: probably under $20 a month for moderate use, under $50 for heavy use. The fine-tuning expansion (see `13-future-expansion.md`) would compress this further for the routine operations.

### Can I use Claude Sonnet instead of Opus to save cost?

Yes. Edit `memex/config.py` to change the default model. Expect lower output quality on compile and essay — the trade is real but usable for personal work. QA and index tolerate Sonnet fine. Keep Opus for compile and export essay if you can afford it.

### The engine crashed mid-apply. Is my vault corrupted?

Very unlikely. Every file write is atomic (`tempfile + os.replace`) — either the old content is there, or the new content is, never a half-written file. Every `--apply` migration is snapshotted, so `memex rollback` restores the pre-apply state. Run `memex doctor` and `memex lint` after a crash; if they pass, the vault is fine.

### What if Obsidian’s graph view disagrees with memex lint about links?

Trust the linter. Obsidian’s graph view is permissive about link resolution; the linter is strict. If Obsidian says a link resolves and the linter says it doesn’t, either the target file is missing or its filename has a casefold mismatch (important for Turkish — `İstanbul` vs `istanbul`).

### How do I debug a slow memex qa call?

Look at the log. Every LLM call emits a JSON event with latency:

```
grep llm_call_complete ~/Documents/Obsidian/<your-vault>/.memex/log.jsonl | tail -n 20
```

If latency is >10 seconds, the likely cause is either a large retrieval context (reduce `--limit`) or an API-side slowdown (usually transient; retry in a few minutes).

### Can I version the whole vault in git?

Yes, and you should. The vault is plain text; it diffs beautifully. A weekly `git commit` after the review is a good cadence. Add `.obsidian/workspace.json` and `.memex/log.jsonl` to `.gitignore` to keep the repo clean.

## Edge cases

### What if a raw source is copyrighted and I don’t want it in a git-backed vault?

Two options:

- Keep the extracted text private. Store the full text in a separate, local-only folder outside the vault; link to it by path in the raw note. The raw note’s body contains only fair-use quotes and your notes.

- Don’t quote at all. Summarise the source in your own words in the raw note’s body. The tradeoff is citation fidelity — you can’t pull exact quotes later.

Either way, the concept notes you derive from the source are yours and live in the vault.

### What about sensitive personal information — how do I handle it?

The vault is sensitive by default. Don’t put credentials, PII, or anything under NDA in it. If you need to reason about a sensitive matter, use code names in the notes and keep the mapping elsewhere (a password manager, an encrypted note outside the vault).

### What if I want to share the vault with a specific person one time?

Use the share expansion (see `13-future-expansion.md`) once it’s built. Until then: `git diff` between the shareable slug and `HEAD`, extract just the relevant files, send as a tarball. Or copy the relevant atomic notes into a fresh, clean vault and share that.

### My vault has grown to 3,000 notes and retrieval is slow. What do I do?

Retrieval is O(n) in the vault size. At 3,000 notes, BM25 retrieval should still complete in under a second. If it’s slower, profile: is it BM25 itself or the subsequent LLM call? If BM25, the embedding-based retrieval expansion (see `13-future-expansion.md`) would help. If LLM, your context is too large — reduce `--limit`.

### The LLM refuses to produce an output because the topic is sensitive. Now what?

Decide whether the refusal is legitimate. Anthropic’s models will refuse content that crosses policy boundaries; most users of this system don’t hit those. If you do, and the topic is legitimately sensitive but legitimately yours (internal company strategy, regulatory grey areas), either:

- Rephrase the prompt to be more neutral.

- Edit `prompts/<mode>.md` to provide framing that makes the legitimacy clear.

- Write the output by hand — the vault still surfaces the right context; you draft the prose yourself.

## Philosophy

### Why is so much of the system deliberately manual?

Because trust is load-bearing. A system that auto-promotes, auto-merges, auto-writes would be faster for a month and useless in a year — you’d stop trusting it because you’d stop knowing what was in it. Every manual step is a trust checkpoint.

### Isn’t this slower than just using ChatGPT?

For single questions, yes. For a year of compound thinking in a specific domain, no. ChatGPT forgets you after every session; this system remembers everything and gets smarter every week. The investment is in the first three months; the payoff starts in month six and compounds thereafter.

### Why not a SaaS with a nice UI?

The invariants rule it out. “Plain markdown on your filesystem” is not compatible with “SaaS on someone else’s servers.” The productised expansion (see `13-future-expansion.md`) preserves the invariants by letting users export and run locally; any SaaS-only version would abandon them.

### I don’t want to build this myself. Is there a version I can just buy?

Not today. See `13-future-expansion.md` for what a productised version would look like. Until that ships, the current system is for people willing to run their own infrastructure in exchange for full ownership.

### How do I know if this system is working?

Three signals:

- You can answer questions about your domain faster than before. “What do I think about X?” completes in the vault in under a minute.

- Your outputs sound more like you, more quickly. The first draft from `memex export essay` is 70% there; you used to start from 0%.

- You notice gaps before meetings. Prep reveals “I don’t have a solid position on Y” while there’s still time to develop one.

If after three months none of these are true, either the vault hasn’t reached critical mass (keep going), or the capture-to-compile ratio is off (capture less, compile more), or the system isn’t right for you.

---

[← Future Expansion](14-future-expansion.md) · [Docs index](README.md) · [Quickstart →](quickstart.md)
