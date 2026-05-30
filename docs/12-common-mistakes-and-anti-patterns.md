# Common Mistakes and Anti-Patterns

Every decay mode in this system has been seen in practice. The list below is empirical, not theoretical; each entry is a specific failure pattern with a named fix.

## Over-tagging

Symptom. A note with 11 tags: `#stablecoin #settlement #netting #finance #payments #crypto #web3 #regulation #mica #circle #tether`.

Why it’s a problem. Tags are cheap to add and expensive to retrieve from. A note with 11 tags shows up under 11 filters, most of them noise. The signal-to-noise ratio of every tag drops each time it’s added to a note that doesn’t truly deserve it.

Fix. A note earns a tag only if the tag represents a recurring dimension you’ll filter on. Three tags is typical. Five is a lot. Seven is almost always wrong.

Worked fix. The note above should have been `[[stablecoin-settlement-netting]]` with tags `topic/stablecoin, topic/settlement, sector/fintech` and wiki-links to `[[circle]]`, `[[tether]]`, `[[mica-settlement-implications]]`, `[[netting-risk]]`. The entities are links. Only the cross-cutting domains are tags.

## Low-value atomic notes

Symptom. An atomic note titled “Circle raises $100M” with three sentences of body and no links out.

Why it’s a problem. Atomic notes are for durable concepts, not news. “Circle raises $100M” is news — it will be stale in six months, uninteresting in two years, and wrong in five (the round will be folded into a larger narrative). Durable space shouldn’t hold transient content.

Fix. Capture the news item in `raw/` as a source. If the news signals a concept worth atomizing, create that concept — `[[funding-rounds-as-signal-in-stablecoin-sector]]` — not the event.

Rule of thumb. If you can’t imagine linking to the note from six other notes over the next five years, don’t create it as an atomic note. Capture, cite, move on.

## Weak summaries

Symptom. The body of `wiki/deferred-net-settlement.md` reads: “Deferred net settlement is a settlement method where transactions are netted and settled at intervals rather than continuously. See Bloomberg article.”

Why it’s a problem. That body is a dictionary gloss plus a pointer. It provides no mechanism, no implications, no Latticework framing. Retrieval will find this note and the LLM will produce hollow output from it.

Fix. Replace with prose that does actual work:

Deferred net settlement (DNS) is a settlement architecture in which transactions accumulate during a period and settle at one or more netting intervals, rather than on a per-transaction basis. The core tradeoff is against gross (real-time) settlement: DNS is cheaper and more capital-efficient for participants — they need only fund the net position, not every gross transaction — but it concentrates settlement risk at the netting moment, which is why regulators treat large DNS systems as systemic. For stablecoin rails, the DNS-vs-gross question is reopening: the industry’s original “instant settlement” marketing assumed gross, but at scale the float cost becomes the binding constraint, pushing protocols toward hybrid structures. See `[[gross-settlement]]`, `[[netting-risk]]`, `[[pre-funded-stablecoin-float]]`.

Rule of thumb. An atomic note’s body should answer “what is it, why does it matter, how does it connect” in that order, in prose, in the first paragraph.

## Duplicate concepts under different names

Symptom. The vault has both `stablecoin-float-mechanics.md` and `pre-funded-stablecoin-float.md`. Inbound links to the first number 4; to the second, 3. Neither is canonical.

Why it’s a problem. The graph is split. Retrieval for “stablecoin float” will catch either, not both. Outputs cite whichever happened to rank higher in BM25 that day. Neither note benefits from the thinking in the other.

Fix. Merge. Pick the stronger title (usually the more specific one, if the specificity is durable; here, `pre-funded-stablecoin-float` wins because “pre-funded” captures the mechanism). Copy content. Use Obsidian’s find-and-replace to rewrite every `[[stablecoin-float-mechanics]]` to `[[pre-funded-stablecoin-float]]`. Delete the losing file. Run `memex lint` to confirm no broken links.

Prevention. Search before creating. The weekly review’s lint pass surfaces orphans (zero inbound links), which is the primary signal for latent duplicates.

## Mixing raw and canonical material

Symptom. `wiki/mica-regulation.md` contains a verbatim paste of the MiCA preamble, followed by three paragraphs of your own interpretation.

Why it’s a problem. Wiki notes are supposed to be yours — canonical, compressed, re-readable. Raw material dumped into the wiki bloats the retrieval context and dilutes the canonical signal. The LLM can’t tell which sentences are your positions and which are the source’s.

Fix. Move the verbatim text to `raw/2024-06-09-mica-official-preamble.md`. Keep your three paragraphs of interpretation in `wiki/mica-regulation-key-provisions.md` with `source: 2024-06-09-mica-official-preamble.md` in frontmatter. The canonical note is now compressed; the source is still fully citable.

Rule. The wiki is for your thinking; `raw/` is for sources. Never mix. Every citation in a wiki note should be a `[[link]]` to a raw file, not an inline paste.

## The wiki as dumping ground

Symptom. `wiki/` has 800 files after six months. Most have `status: seed`. A quarter have zero outbound links. Search returns clutter.

Why it’s a problem. At 800 files of uneven quality, the wiki has collapsed into the inbox it was supposed to replace. Retrieval is dominated by noise. Writing outputs becomes harder, not easier.

Fix. A “wiki pruning” pass. For each seed note older than two months with zero inbound links, decide: (a) promote to draft, add links, make it earn its place; (b) merge into a better note; (c) archive. Be ruthless in option (c). The wiki should feel curated, not exhaustive.

Prevention. Don’t create a wiki note unless you can articulate why it will be linked from at least two future notes. If the criterion isn’t met, the content belongs in a raw source’s body or in an inbox note.

## Compiling raw material you haven’t read

Symptom. You compile a 40-page BIS paper into nine atomic notes. The engine’s output looks fluent. You `--apply` without reading the source carefully. A month later, you realise three of the “atomic notes” make claims the paper never made — the LLM hallucinated them.

Why it’s a problem. The engine is as trustworthy as its inputs and your review. Compiling without reading the source yourself removes the one checkpoint that catches hallucination. The distortion compounds every time those notes are retrieved.

Fix. Skim the source before compiling. Read the compile dry-run output in parallel with the source, not in isolation. If a proposed atomic note says something you don’t remember from the source, don’t apply that note. Compile is a cost-saver, not a substitute for reading.

Rule. “I will read everything I let into my wiki” is a non-negotiable commitment. The engine helps you structure reading; it does not replace it.

## Letting project notes become permanent homes for durable knowledge

Symptom. `projects/2026-q2-stablecoin-whitepaper/notes/dns-vs-gross.md` contains a beautiful 600-word explanation of the settlement tradeoff. Q2 ends. The project folder sits untouched. A year later, you want to reference that tradeoff and can’t find it — it lives in a project that’s no longer active.

Why it’s a problem. Project folders are workspaces, not canonical stores. Durable knowledge buried in them is lost to the vault at large.

Fix. At project close-out, do a promotion pass: walk every note in `projects/<slug>/notes/` and either (a) promote to `wiki/` as an atomic note (editing as needed to strip project-specific framing), (b) merge into an existing wiki note, or (c) archive with the project. Close-out is non-optional.

Rule. A closed project’s folder should contain only the project’s unique artefacts — the specific deliverables, the project-specific decisions. Every generalisable note migrates out.

## Chat-scale thinking outside the vault

Symptom. A week of Slack DMs working out a strategic position on Islamic finance compatibility for a stablecoin product. When asked to write it up, you realise none of it made it into the vault.

Why it’s a problem. Chat is a capture surface, not a record. A week’s worth of reasoning in DMs is a week’s worth of reasoning that doesn’t exist for the second brain.

Fix. At the end of any substantive chat exchange, capture the synthesised position. Create a wiki note if it’s durable. Create an inbox note if you aren’t sure yet. The friction of moving from chat to vault is what preserves the thinking.

Rule. If it was worth typing, it’s worth capturing. The vault outlasts every chat tool.

## Treating templates as optional

Symptom. You hand-type frontmatter. Half the time you forget `status:`; a third of the time you use `Date:` (capital D) instead of `date:`.

Why it’s a problem. Manual frontmatter is schema drift waiting to happen. Every lint run fails. Engine behaviour becomes unpredictable.

Fix. Configure Templater’s folder templates (see `09-onboarding.md` step 5). Every new note in `inbox/`, `raw/`, or `wiki/` auto-applies a template with valid frontmatter. You never hand-type YAML again.

Rule. Schema-valid frontmatter is the vault’s load-bearing invariant. Let tools enforce it, not your memory.

## Running --apply mid-workflow to “save the step”

Symptom. You’re halfway through a compile review. Something interrupts you. You run `memex compile ... --apply` to “not lose the work” and close the laptop.

Why it’s a problem. You’ve just written unreviewed content into the wiki. Future retrieval will use it. You’ll forget to go back and review.

Fix. If you’re interrupted mid-review, do nothing. Close the laptop. The dry-run output is ephemeral; that’s fine. You can re-run the compile tomorrow. The cost is trivial; the cost of unreviewed wiki content is not.

Rule. `--apply` means “I have reviewed this and it is correct.” Nothing less is acceptable.

## Skipping snapshots because “it’s a small migration”

Symptom. You’re adding a new field to the schema. You know it’s additive. You skip the snapshot (“nothing could go wrong, it’s just a new optional field”). The migration runs; a bug in the validator invalidates 200 notes. You can’t cleanly roll back.

Why it’s a problem. Snapshots are cheap. Recovery without them is not.

Fix. Never skip snapshots. `memex migrate --apply` always snapshots by default; don’t override. Keep `.memex/snapshots/` forever — disk is cheaper than regret.

Rule. The operator’s mental model is “assume nothing works until proven.” Snapshots are how you prove.

## Shipping prompt changes without testing

Symptom. You edit `prompts/compile.md` to improve the output shape. You don’t test it. The next day, every compile output is malformed. You spend the morning reverting.

Why it’s a problem. Prompts are code. Untested code is a liability.

Fix. Before editing a prompt in-place, copy a representative raw file to a scratch vault. Run `memex compile` with the old prompt; then with the new prompt. Compare. Only commit the prompt change if the new output is strictly better.

Rule. A prompt change is a behaviour change. It goes through the same discipline as a code change.

## The “I’ll catch up on the weekly review later” pattern

Symptom. You skip the weekly review this week (“busy week”). You tell yourself you’ll do two reviews next week. Two weeks pass; the inbox has 47 items; you avoid the vault entirely because opening it now feels overwhelming.

Why it’s a problem. The weekly review is the keel. Without it, the vault drifts. With two weeks of debt, the review becomes unappealing; with four weeks, it becomes abandoned.

Fix. Never skip the weekly review. If the standing block doesn’t work, reschedule within the same week — but do it. If life is genuinely too full, do a 15-minute pass (inbox + lint) rather than skipping entirely.

Rule. Small, regular tending beats heroic catch-ups. The system is designed for the former and punishes the latter.

## Treating engine-written output as authoritative

Symptom. `memex export essay` produces a beautifully-phrased argument for a position you half-agree with. You send it to a colleague as your own view.

Why it’s a problem. The engine wrote the prose; you may not have actually committed to the argument. A week later, in a meeting, you realise you don’t believe half of what your own “essay” said.

Fix. Every engine output is a starting structure. Edit it. Make it yours. If there’s a claim you don’t stand behind, rewrite or remove. Your reputation attaches to what goes out with your name; the engine’s outputs are not signed.

Rule. LLMs produce plausible prose. Only your editing makes it true. Always edit before sharing.

## Recap

The pattern across all these mistakes: they take shortcuts around the friction that is the system. The friction is the feature. An inbox that costs nothing to skip is an inbox that rots. A wiki that accepts unreviewed content is a wiki that degrades. A review that can be postponed is a review that will be postponed. The discipline is not a tax on the system; it is the system.

---

[← Best Practices](11-best-practices.md) · [Docs index](README.md) · [Maintenance →](13-maintenance.md)
