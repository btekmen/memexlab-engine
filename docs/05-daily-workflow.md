# Daily Workflow

A working day has three modes: capture (all day, low friction), process (a focused block, usually mornings), and produce (longer blocks, when you have a specific output in mind). The system supports all three without requiring you to name which mode you are in.

This page walks through a typical day’s workflow, then closes with a worked example against a real source.

## The eight-step flow

```
  capture → ingest → process → compile → link → promote → produce → feedback
```

Each step has a natural resting point; you do not need to go all the way through in one sitting. Captured material can wait overnight in `inbox/`; ingested material can wait days in `raw/` before compilation.

### 1. Capture

Where. `inbox/`. Effort. Under 10 seconds per item.

Open Obsidian. Run the inbox template (Templater hotkey) or paste-to-inbox (custom command). Drop the content. Move on.

Do this. Capture URL + one sentence of why you saved it. Capture raw paragraphs exactly as seen. Capture your half-formed reaction, tagged `reaction/` so you can find your own thinking later.

Do not do this. Do not classify at capture time. Do not decide what folder it belongs in. Do not write a summary. Capture is fast and noisy by design.

### 2. Ingest

Where. `raw/`. Effort. 2–5 minutes per source that survives triage. Cadence. Weekly review, or immediately when you know a source deserves it.

Walk the inbox. For each item, decide:

- Promote to raw. It is a source you want to keep. Fetch the full text (for URLs, `curl` or a reader-mode extract). Create a file in `raw/` using the source template. Delete the inbox item.

- Merge into an existing note. It is a fact or quote that belongs in an atomic note you already have. Paste it in with proper citation. Delete the inbox item.

- Delete. It was captured enthusiasm that no longer earns its space. Delete the inbox item.

Why it matters. An unpromoted inbox item is an unpaid debt. Every unprocessed inbox item makes the inbox itself less trustworthy.

### 3. Process

Where. `raw/`. Effort. 15–30 minutes per source. What happens. You read the source, make margin notes (as comments or highlights inside the raw file — or separately), decide whether it contains compilable material.

Not every raw file needs compilation. Some sources are reference material you want searchable but never want to atomize. A raw source that has been read and judged atomizable gets a `processed: true` frontmatter flag — signals that the next `memex compile` on it is a good next move.

### 4. Compile

Where. `wiki/`. Effort. 5–10 minutes per source. Command.

```
memex compile raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md# (dry run — see the plan)memex compile raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md --apply# (actually write)
```

What happens: the compile mode feeds the raw file’s text plus the two core notes into the LLM. The LLM returns a list of candidate atomic notes: `{title, slug, body, tags, latticework}`. The dry run prints this list. The apply run writes each candidate as `wiki/<slug>.md` with proper frontmatter.

Review the dry-run output carefully. If the LLM wants to make 12 notes from one article and you know the source really only supports 3, re-run with `--apply` only after you have decided those 3 are the right ones. You can always split the source, or edit the wiki notes post-compile; the important discipline is that you actually looked before applying.

### 5. Link

Where. `wiki/`. Effort. A few minutes per new note.

In Obsidian, open each newly compiled note and add at least two outgoing `[[links]]` to related concepts. The concepts may already exist (link to them). If a concept doesn’t yet exist and it should, create the stub note — just a two-sentence placeholder is enough. The linter will flag the stub later, reminding you to develop it.

Do this. Link by slug: `[[deferred-net-settlement]]`, not `[[Deferred Net Settlement]]` (both work in Obsidian, but slug form is stable across renames).

Do not do this. Do not create a new concept page for every noun phrase the atomic note mentions. Link only to concepts that have independent durability.

### 6. Promote

Where. Status transitions inside the note. Effort. Quick, per-note.

Every atomic note carries `status: seed | draft | evergreen`.

- Seed. Just written. Body is present, links are present, but you haven’t revisited it. Default on compile.

- Draft. You’ve re-read it once, edited for clarity, confirmed its links.

- Evergreen. You’ve returned to it at least once weeks after creation, re-validated its claims against newer sources, and expect it to stand for years.

Promote notes as they earn it. An evergreen note is a load-bearing part of the wiki. A seed note is disposable.

### 7. Produce

Where. One of the output folders. Effort. Depends on the output.

When you have a reason to produce — a meeting deck, a blog post draft, a research memo — invoke the relevant engine command:

```
memex qa "What is the current regulatory posture on stablecoin settlement in the EU?"memex index "stablecoin settlement" --type topicmemex export essay "The case for deferred net settlement in cross-border stablecoin rails" --applymemex export slides "Programmable money primer for <your-product> board" --theme gaia --applymemex chart tag-frequency --top 15 --apply
```

Review every output. The engine writes first-class notes inside the vault, but that does not mean the output is done. An output is a first draft; you edit it in Obsidian like any other markdown file.

### 8. Feedback

Where. Back into `wiki/`. Effort. 5–10 minutes per output.

While producing, you will notice gaps: a concept referenced but not defined, a claim that deserves its own note, an open question you hadn’t articulated. Write those notes now, while the context is fresh.

Why it matters. The feedback step is where the vault compounds. Without it, the vault is a static library; with it, each output makes the next output better.

## A worked example — end-to-end

Let’s walk a single source through all eight steps. The source: a hypothetical Bloomberg piece, 2026-03-17, titled “Stablecoin settlement rails face a netting crisis.”

### Step 1 — capture

In Obsidian, you paste the URL and your reaction into `inbox/2026-03-17-11-47-bloomberg-stablecoin-rails.md`:

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>date: 2026-03-17<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>https://www.bloomberg.com/…reaction: the netting-vs-gross-settlement question we've been circling onthe <your-product> roadmap. feels like this is the week it starts mattering.
```

### Step 2 — ingest

Next morning. You’ve decided this one is worth keeping. You extract the full article text and create `raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md`:

```
<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div>title: "Stablecoin settlement rails face a netting crisis"type: sourcesource_url: https://www.bloomberg.com/…publisher: Bloombergauthor: Jane Doepublication_date: 2026-03-17ingested: 2026-03-18status: seedtags: [topic/stablecoin, topic/settlement]latticework: [problem-1, problem-2]<div style="text-align:center;color:#94a3b8;letter-spacing:.4em;">• • •</div><full article text verbatim>
```

Delete the inbox entry.

### Step 3 — process

You read the article. You annotate, maybe in a comment block at the top:

```
<!--key claims worth atomizing:- deferred-net-settlement vs gross settlement tradeoff- the case for pre-funded stablecoin float- Circle's position vs Tether's position- regulatory implications under MiCA-->
```

### Step 4 — compile

```
memex compile raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md
```

The dry run proposes four atomic notes: `deferred-net-settlement`, `pre-funded-stablecoin-float`, `circle-settlement-posture`, `mica-settlement-implications`. You read the plan and approve.

```
memex compile raw/2026-03-17-bloomberg-stablecoin-settlement-rails.md --apply
```

Four new files appear in `wiki/`, each with `source: 2026-03-17-bloomberg-stablecoin-settlement-rails.md` in frontmatter.

### Step 5 — link

You open each new note. `deferred-net-settlement` gets `[[gross-settlement]]`, `[[netting-risk]]`, `[[mica-settlement-implications]]`. `circle-settlement-posture` gets `[[circle]]` (a company entity) and `[[stablecoin-issuer-typology]]`. You notice `netting-risk` doesn’t exist — you create it as a two-sentence stub.

### Step 6 — promote

Today everything stays `status: seed`. You’ll revisit next week.

### Step 7 — produce

Later in the week you need a five-page memo on settlement architecture for a <your-company> strategy conversation.

```
memex export essay "Settlement architecture options for a stablecoin-native banking platform" --apply
```

The essay retrieves over the whole wiki, picks up your new notes plus the relevant existing ones, and drafts the memo with `[[slug]]` citations. You edit it in Obsidian — tightening prose, adding a conclusion the LLM missed, fixing one wrong claim.

### Step 8 — feedback

While editing, you realise:

- You cite `[[intraday-liquidity]]` three times but have no note on it. Create the stub.

- The essay needs an “open question” section about GCC settlement adoption. Create `wiki/questions/does-the-gcc-adopt-wholesale-cbdc-before-2028.md`.

- You discover a duplication: `stablecoin-float-mechanics` and `pre-funded-stablecoin-float` are the same concept. Merge.

Run `memex lint` at the end of the day. The report lands in `_lint/lint-2026-03-24.md`. If it shows zero errors, you’ve closed the loop.

## Time budget, rough

Mode

Daily

Weekly

Monthly

Capture

20–40 min (diffuse, all day)

—

—

Process

30–60 min (focused morning)

—

—

Produce

0–4 hr (variable)

—

—

Review (inbox triage, lint)

—

60–90 min

—

Refactor

—

—

2–3 hr

You can run the system on 30 minutes a day plus a 90-minute weekly review. Everything above that is produce-time, which is optional and goal-driven.

---

[← Folder Structure](04-folder-structure.md) · [Docs index](README.md) · [Templates and Note Types →](06-templates-and-note-types.md)
