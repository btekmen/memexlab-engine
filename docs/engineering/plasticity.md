# Plasticity policies

Local scores for two decisions. Both are weighted means of factors you can read.
Neither edits a note, moves a file, or uses the network.

```text
score = sum(weight * value) / sum(weight)    for weights greater than 0
```

Each factor value is from 0 to 1. The report lists weight, value, contribution
(`weight * value`), and a one-line detail for every factor. `recommend` is true
when `score >= threshold`.

| Policy | Question | What a true recommendation means |
| --- | --- | --- |
| `rps` | Which notes should re-enter a morning brief? | Show the note. |
| `mws` | Should this inbox note be promoted to canonical? | A human might promote it. The file stays in the inbox. |

Weights are the round defaults below. They are not fitted to LoCoMo, Tekmen-eval,
or the sample vault. PFS and CRS are not given formulas here.

## Commands

```bash
memex plasticity --vault ~/vault                 # rps and mws
memex plasticity rps --vault ~/vault             # morning brief
memex plasticity mws --vault ~/vault --format json
```

The MCP tool is `plasticity(policy="all", limit=0)`. `limit` 0 uses the policy
file. The same call is read-only.

An `open_loop` flag is separate from the score. It is true when `status` is
`contested`, when `resolution` is `proposed`, or when a queue item is `pending`.

## Where weights live

Defaults are in [`schemas/plasticity.defaults.yml`](https://github.com/btekmen/memexlab-engine/blob/main/schemas/plasticity.defaults.yml)
and in code. To override, put `plasticity.yml` at the vault root. Omitted keys
keep the default. Unknown keys are an error. A weight of 0 stays in the
breakdown and drops out of the score.

`memex plasticity` reads the same meter file as `memex meter` (`MEMEX_METER_PATH`,
then `meter_path:` in `governance.yml`, then `<vault>/.memex/meter.jsonl`). It
only counts records whose `hit` is true.

## Schema

```yaml
version: 1

rps:
  threshold: 0.5
  limit: 20
  recency_horizon_days: 30
  link_cap: 5
  meter_hit_cap: 3
  weights:
    recency: 1
    contested: 1
    unresolved: 1
    links: 1
    meter_hits: 1

mws:
  threshold: 0.5
  limit: 20
  substance_chars: 400
  link_cap: 3
  weights:
    substance: 1
    provenance: 1
    links: 1
    not_contested: 1
    not_proposal: 1
```

`version` must be 1. `threshold` is from 0 to 1. The integer settings are at
least 1. Weights are numbers at least 0.

## RPS factors

Age comes from `captured_at` when that value is a timestamp, otherwise from the
file's modification time. A future timestamp counts as age 0.

| Factor | Value |
| --- | --- |
| `recency` | `min(1, age_days / recency_horizon_days)`. Older notes are more due to re-enter. |
| `contested` | 1 when `status` is `contested`, otherwise 0. |
| `unresolved` | 1 when `resolution` is `proposed`, otherwise 0. |
| `links` | `min(1, wikilink count / link_cap)`. |
| `meter_hits` | `min(1, records with hit true that cite this slug / meter_hit_cap)`. |

## MWS factors

Only notes in the vault's write dir are scored (default `inbox/`, or `write_dir:`
in `governance.yml`).

| Factor | Value |
| --- | --- |
| `substance` | `min(1, body characters / substance_chars)`. |
| `provenance` | 1 when `sources` or `origin_ref` is set, otherwise 0. |
| `links` | `min(1, wikilinks that resolve to another note / link_cap)`. |
| `not_contested` | 0 when `status` is `contested`, otherwise 1. |
| `not_proposal` | 0 when `resolution` is `proposed`, otherwise 1. |
