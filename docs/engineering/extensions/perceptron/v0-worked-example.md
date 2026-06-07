
# Network Perceptron (V0)

**The one-shot proof for the [[perceptron]] reasoning layer.**

A worked example: how a single operator with a single goal can convert two decades of
accumulated contacts (LinkedIn + Mac Contacts + Twitter) into a fully-scored, fully-tagged,
agent-queryable subgraph in a single session — using nothing but the MemexLab Engine,
~300 lines of Python, and a 60-label active-learning round.

## Status

`active` · `v0` shipped May 2026 · the scored network is live in the operator's vault,
indexed, embedded, and queryable via the `network-perceptron` tag family. Superseded
in scope by the [[perceptron]] V1 product spec.

## Problem

An operator with ~21K accumulated contacts across two decades of building faces a
sales/BD scaling crisis: which contacts matter for **which vertical product line**,
today? The example vertical:

1. **Premium tier** (high-net-worth individuals, founders, owners)
2. **Mid-market** (mid-sized operators)
3. **Early-stage** (founders / CEOs of new ventures)
4. **Enterprise** (C-suite at large multinationals / public-listed)

— each demand a different ICP and outreach motion. Unranked CSV exports do not answer:
*"Who in my 21K-person network is a strong-tie enterprise executive worth a meeting
this week?"* This V0 answered that.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│ INGEST                                                           │
│  - LinkedIn Connections.csv                  (~14K contacts)     │
│  - Mac Contacts .abbu (SQLite)               (~11K contacts)     │
│  - Twitter archive                                               │
│    · following.js + follower.js              (~3.6K / ~8.4K)     │
│    · contact.js (phones synced to X)         (~4.3K)             │
│    · direct-message-headers.js               (~75 DM partners)   │
└──────────────────────────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ CONSOLIDATE & DEDUPE                                             │
│  - Cross-source identity reconciliation                          │
│    (email > phone > last-10-digits > name+company)               │
│  - Output: master_contacts.csv  (~21K unique people)             │
│  - ~1K strong-tie contacts (on both LinkedIn AND in phone)       │
└──────────────────────────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ ENGINEER FEATURES (19 → 15 after collinearity pruning)           │
│  - Seniority parse (multi-locale keywords)                       │
│  - Founder / Owner flag                                          │
│  - Target-company-tier match (curated lookup list)               │
│  - Multinational / public-listed flags                           │
│  - Vertical-fit heuristic (industry/stage keywords)              │
│  - Per-product fit vector (4 dims)                               │
│  - Relationship strength (source-diversity + signals)            │
│  - Reach proxy (seniority × company tier)                        │
└──────────────────────────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ LABEL & TRAIN                                                    │
│  - Stratified sample of 60 contacts (top + mid + low bands)      │
│  - Interactive HTML labeling tool (localStorage progress)        │
│  - Operator labels: 55 positive / 5 negative                     │
│  - Augment with 50 pseudo-negatives (source-distribution         │
│    matched against positives — avoids source bias)               │
│  - Pure-numpy logistic-regression perceptron, L2-regularized     │
│  - 5-fold CV AUC: 0.82                                           │
└──────────────────────────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ BLEND & SCORE                                                    │
│  - final_score = 0.30 × perceptron + 0.70 × heuristic            │
│  - 60 labels was too few to fully trust the perceptron;          │
│    the heuristic encodes domain knowledge correctly (a senior    │
│    enterprise executive IS a top prospect regardless of training)│
│  - Verified by hand on named bluechip contacts                   │
└──────────────────────────────────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│ MATERIALIZE INTO MEMEX                                           │
│  - ~21K person entities → <vault>/people/<slug>.md               │
│  - ~500 company entities → <vault>/companies/<slug>.md           │
│  - CuratedFrontmatter conformant (multi-iteration schema fixes)  │
│  - Locale-aware slugs (Turkish ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c)     │
│  - Aliases for wikilink resolution                               │
│  - Tag taxonomy: 4 product lines, 5 score bands, plus           │
│    #perceptronintegration on every auto-generated entity         │
└──────────────────────────────────────────────────────────────────┘
```

## Output

| Layer | Artifact | Location |
|---|---|---|
| Raw | `master_contacts.csv` · `features.csv` · `scores.csv` | workspace |
| Model | `feature_weights.json` · `model_report.txt` | workspace + vault |
| Excel workbook | 6 sheets — top targets, all scored, per-product tabs, model info | workspace |
| Interactive dashboard | top-5K embedded, Chart.js, filterable | workspace |
| Memex entities | ~21K persons + ~500 companies | `<vault>/people/`, `<vault>/companies/` |

## Key results

**Brain expansion (representative numbers from the operator's vault):**

| Metric | Before | After |
|---|---:|---:|
| Total entities | ~1.8K | **~24K** |
| Person entities | ~32 | **~21.6K** |
| Company entities | ~0 | **~550** |
| Edges | ~4.2K | **50,000+** |
| Aliases | ~1.1K | **~1.3K** |

**Score distribution** (over ~21K deduped contacts):

- High value (score > 0.7): **~5%**
- Consider (0.4–0.7): **~16%**
- Lower (< 0.4): **~79%**

**Strong ties** (LinkedIn ∩ Phone): **~1K** contacts — the highest-relationship subset.

**Top-of-rank validation pattern.** Named bluechip executives (senior-title at the
operator's curated list of target companies) consistently appeared in the top-100.
Stealth-mode AI founders did NOT dominate the top — the heuristic+model blend kept
strategic enterprise targets ranked appropriately.

## Engineering decisions worth remembering

1. **Heuristic + perceptron blend > perceptron alone.** At 60 labels with a 55:5
   imbalance, the perceptron collapsed onto "founder + AI startup" patterns. Blending
   30/70 against a hand-crafted heuristic re-surfaced enterprise targets.
   *Lesson: in small-data regimes, encode domain knowledge as a regularizer.*

2. **Source-bias-matched pseudo-negatives.** Naively sampling negatives from
   low-heuristic contacts (mostly Mac Contacts only, no LinkedIn) taught the model
   "on-LinkedIn = good". The fix: match the source-distribution of positives when
   drawing negatives.
   *Lesson: PU learning needs negatives that span the same feature regions as
   positives.*

3. **Locale-aware slugify is mandatory.** A dotless `ı` doesn't decompose under NFKD,
   so default Python slug routines silently drop it. `Türkiye İş Bankası` →
   `turkiye-is-bankas` (wrong) vs `turkiye-is-bankasi` (right). This broke wikilink
   resolution for ~60 entities until fixed.
   *Lesson: a knowledge base in a non-English-dominant region needs locale-aware
   identity handling at the slug layer.*

4. **Pydantic `extra="forbid"` is unforgiving.** Memex's `CuratedFrontmatter` rejected
   files for missing `source:` inside provenance entries; `AtomicFrontmatter` uses a
   single `date:` field instead of `created:`+`updated:`. Both required schema rounds.
   *Lesson: validate against the actual schema before bulk-generating 21K files.*

5. **Folder is destiny, not type.** Memex classifies by top-level folder, not by the
   `type:` field. A file with `type: person` in `<vault>/my-custom-folder/` is silently
   excluded. It has to live in `<vault>/people/` to be a person.

## Use in the Memex Engine

This project is the V0 of the [[perceptron]] product — the first **ML extension** to
the [MemexLab Engine](https://btekmen.github.io/memexlab-engine/). It does not modify
the engine — it produces vault-conformant content that the engine indexes, embeds, and
exposes via its standard tooling:

- `memex reindex` → registers all ~22K new entities
- `memex reembed` → vector coverage at 100%
- `memex resolve` → wikilink resolution including the locale-specific corpus
- MCP server (`memex mcp`) → query via `search_brain`, `resolve_link`, `read_entity`
  from any Claude agent

The engine's existing **type system** (`person`, `company`, `project`) absorbed the
output cleanly with proper locale-aware slugs + aliases. Atomic-class index pages are
the entry points for human and agent retrieval.

## Connections

- [[perceptron]] — the V1 product spec that generalizes V0
- [[memexlab-engine]] — the substrate this extends
- [[infrastructure-control]] — the architectural conviction (engine = rails,
  perceptron = cargo)
- [[speed-of-execution]] — V0 built end-to-end in one session, including six schema
  iterations

## Source material (anonymized)

- LinkedIn Connections export
- Mac Contacts archive (.abbu SQLite bundle)
- Twitter archive (includes contact.js + direct-message-headers.js)
- Operator's internal board & management roster
- Operator's internal cap-table file
- MemexLab Engine docs (`0.2.0-harness-preview`)

## Roadmap

- **Twitter DM resolution** — DM partner Twitter IDs identified; manual mapping to
  names would unlock the highest-relationship-strength signal currently unmodeled.
- **Embedder upgrade** — Memex defaults to `hashed-ngram-256` (TF-IDF-style, shallow).
  A real semantic embedder (sentence-transformers / OpenAI) would lift abstract
  paraphrase queries from B to A.
- **Re-train with 200+ labels** — current model is heuristic-dominated (70%); a richer
  labeled set would let the perceptron carry more weight.
- **Active learning loop** — surface high-uncertainty contacts for fresh labeling
  whenever the operator opens the dashboard.
- **Outreach integration** — pipe top-scored, strong-tie, product-matched contacts
  into a CRM motion (Apollo / HubSpot / Close) automatically.

These items are V0.5 / V1 work in [[perceptron]].

---

*This document is a worked example for the engine's extension docs. Generic
placeholders (`<vault>`, `<operator>`) stand in for personal data, following the
convention in the engine's main documentation.*
