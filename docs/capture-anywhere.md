# Capture Anywhere

The single most common capture friction: you see something worth keeping, and the
vault is too many taps away. This page gives you a one-gesture capture path on every
device — **without a cloud in the middle**. Every path below lands a plain-markdown
stub in your vault's `inbox/`; the weekly review promotes what earns it, same as any
capture.

There are four paths, cheapest first. All of them assume your vault is synced across
devices — set that up once with the [vault sync guide](vault-sync.md).

## 1. The CLI (terminal, scripts, agents)

```bash
memex ingest url https://example.com/essay --vault ~/vault --apply
```

Fetches the page, extracts readable markdown locally, files it with provenance
(`source_url`, `captured_via`, capture time), and skips URLs you already captured.
Also available: `ingest kindle`, `ingest readwise`, `ingest rss`, `ingest
youtube-feed`, `ingest feeds`, `ingest youtube`. See
[`memex-cli/`](https://github.com/btekmen/memexlab-engine/tree/main/memex-cli).

## 2. Desktop browser — the bookmarklet

Zero install: a bookmark whose URL is JavaScript. It opens Obsidian with a
pre-filled inbox note carrying the page title, URL, and whatever text you had
selected.

Create a new bookmark, name it `→ inbox`, and paste this as the URL — replacing
`YOURVAULT` with your Obsidian vault's name (URL-encode spaces as `%20`):

```
javascript:(()=>{const t=document.title,u=location.href,s=String(window.getSelection()).trim();location.href='obsidian://new?vault=YOURVAULT&file=inbox%2F'+encodeURIComponent(t.replace(/[\\/:*?"<>|#^[\]]/g,'-').slice(0,60).trim())+'&content='+encodeURIComponent('---\ntitle: "'+t.replace(/"/g,"'")+'"\nstatus: inbox\ncaptured_via: bookmarklet\nsource_url: '+u+'\n---\n\n'+(s?'> '+s.replace(/\n/g,'\n> ')+'\n\n':'')+u+'\n');})()
```

What it does, exactly: builds an `obsidian://new` URI — the note is created by
*your* Obsidian, in *your* vault, on *your* disk. No extension, no permissions, no
server. Works in every desktop browser.

- Select a passage first and the capture arrives as a quote block.
- Want the full article text too? Capture the stub now, run
  `memex ingest url <url> --apply` later — the stub and the full capture meet in
  your weekly review.

## 3. iPhone/iPad — a share-sheet Shortcut (5 steps, no code)

Build once in the Shortcuts app; afterwards "→ inbox" appears in every share sheet
(Safari, YouTube, X, anywhere that shares a URL):

1. New Shortcut → tap the info panel → enable **Show in Share Sheet**; set input
   types to **URLs, Safari web pages, Text**.
2. Add **Text** action:

   ```
   ---
   title: "Shortcut Input"
   status: inbox
   captured_via: shortcut
   source_url: Shortcut Input
   ---

   Shortcut Input
   ```

   (Insert the magic variable *Shortcut Input* in the three places shown; for the
   title line use the variable's **Name** if offered.)
3. Add **Save File** action → toggle **Ask Where to Save** OFF → pick your synced
   vault's `inbox/` folder (works with the Obsidian folder via iCloud/Working
   Copy — see the [sync guide](vault-sync.md) mobile section).
4. In Save File, set the file name to `capture-` + *Current Date* (custom format
   `yyyyMMdd-HHmmss`) so names never collide.
5. Name the Shortcut `→ inbox`. Done — share anything to it.

## 4. Android

Easiest: **Obsidian's own share target** — share any URL/text to Obsidian, and set
Obsidian's "Default location for new notes" to `inbox/`. The note carries the shared
text; add the URL if the app didn't.

Power users can replicate the iOS recipe with Tasker/Automate (receive share →
write file into the synced vault's `inbox/`) — community-supported territory.

## Why not a browser extension?

Deliberately deferred: the paths above cover the job with zero binaries to trust,
zero store reviews, and zero maintenance surface. If real usage shows the
bookmarklet is the bottleneck, an extension earns its roadmap slot — the criterion
is written in the roadmap, not vibes.

## The contract, restated

Whatever the path: the capture is a plain markdown file in `inbox/`, with
provenance frontmatter, created by tools you control. Nothing is proxied, nothing
leaves your devices, and the LLM is nowhere in the loop.

---

[Docs index](README.md) · [Vault Sync](vault-sync.md) · [Daily Workflow](05-daily-workflow.md)
