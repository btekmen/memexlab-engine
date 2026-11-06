# Evals

Two local runners share one harness.

- `scripts/run_benchmark.py` scores the sample query set (`evals/query-set.sample.yml`) for recall@k and MRR. It does not call a model.
- `scripts/eval_arms.py` scores LoCoMo and a private Tekmen-eval file with a mock model by default, or a model you point at an endpoint.

The public LoCoMo file is downloaded at run time. Real Tekmen-eval questions stay outside this repository. Reports are JSONL and markdown on disk.

## Three arms

| Arm | What the model sees |
| --- | --- |
| A | The question, and a one-line instruction to answer in a short phrase. |
| B | The Memex librarian harness. The retrieved-notes block is `(none)`. |
| C | The same harness, plus BM25 hits from the vault (bodies capped at 4000 characters). |

Arm C is the only arm that writes the retrieval meter. Latency is search plus reading the hit bodies. The model call is outside that clock. Retrieved tokens use the same `ceil(utf-8 bytes / 4)` estimate as `memex search`.

```bash
# one arm
python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms A
python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms B
python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms C

# all three
python3 scripts/eval_arms.py locomo --data evals/locomo.sample.json --arms A,B,C
```

`--arms` defaults to `A,B,C`.

## Model access

| Flag | Network |
| --- | --- |
| `--model mock` (default) | None. Unknown questions answer `no information available`. `--mock-answers FILE` is a JSON object of question text to answer. |
| `--model live` | `MEMEX_MODEL_URL` only: an OpenAI-compatible local server (llama.cpp, vLLM, Ollama, LM Studio). `MEMEX_MODEL` overrides the model id. If the URL is unset, the run stops before any socket. |
| `--model live --allow-remote` | The operator's existing provider order (`MEMEX_MODEL_URL`, then GLM, Anthropic, OpenAI). This is the switch that can send prompts off the machine. |

Prompts leave the machine only on the calls that flag makes. The vault is not uploaded anywhere else.

## LoCoMo

The public file is [snap-research/locomo `data/locomo10.json`](https://github.com/snap-research/locomo/blob/main/data/locomo10.json). It is not stored in this repo. A one-conversation synthetic stand-in, `evals/locomo.sample.json`, is what tests use.

```bash
# download once into ~/.cache/memex/locomo/locomo10.json
# (override the path with MEMEX_LOCOMO_CACHE)
python3 scripts/eval_arms.py locomo --fetch --arms A,B,C

# or place the file yourself, outside the repo
curl -L -o "$HOME/.cache/memex/locomo/locomo10.json" \
  https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json
python3 scripts/eval_arms.py locomo --data "$HOME/.cache/memex/locomo/locomo10.json" --model live --arms C
```

`--fetch` is the only dataset download. A file named `locomo10.json` inside the repo is refused. `--limit N` scores the first N questions.

Each conversation is written to a temporary markdown vault under the output directory (session date and speakers are in the note body, because BM25 indexes title and body). That vault is a run artifact.

### Score

The score follows `task_eval/evaluation.py` in the public LoCoMo repo. `accuracy` in the report is the mean of those per-question scores (the aggregate that script prints). The stemmer matches NLTK's default `PorterStemmer`.

| Category id in the file | Name | Score |
| --- | --- | --- |
| 1 | multi-hop | Split the gold answer on commas. For each part, take the best token-F1 against a comma-separated prediction part. Mean those. |
| 2 | temporal | Token F1. |
| 3 | open-domain | Token F1. Gold is cut at the first `;`. |
| 4 | single-hop | Token F1. |
| 5 | adversarial | `1` when the prediction contains `no information available` or `not mentioned`. Otherwise `0`. |

Token F1 lowercases, drops punctuation and the words a/an/the/and, then Porter-stems. Category ids in the JSON are the ones in the table. They are not the numbered list in the paper.

This is the public F1 / abstain score. A separate LLM-judge accuracy is a different number and is not what this runner reports.

### Report

Default output directory: `.memex/eval/locomo` (gitignored). `--out` moves it.

- `report.md` — accuracy per category, median retrieval latency, median and mean retrieved tokens, per arm.
- `report.json` — the same aggregates.
- `results.jsonl` — one object per question per arm (`id`, `arm`, `category`, `question`, `answer`, `prediction`, `score`, `hit`, `retrieval_ms`, `retrieved_tokens`, `cited_slugs`).
- `meter.jsonl` — the local meter, route `eval.locomo`, one line per arm-C question.

`hit` on that meter line is `true` when the official score is at least `--hit-at` (default `0.5`). Arms A and B leave the meter untouched. `memex meter --path <out>/meter.jsonl` summarizes it.

## Tekmen-eval

Questions are reminders, decisions, and company facts. The real file lives outside the repo, usually inside the vault. The committed file `evals/tekmen-eval.example.yml` is a synthetic shape example.

```bash
python3 scripts/eval_arms.py tekmen \
  --vault ~/vault \
  --questions ~/vault/eval/tekmen-eval.yml \
  --arms A
python3 scripts/eval_arms.py tekmen --vault ~/vault --questions ~/vault/eval/tekmen-eval.yml --arms B
python3 scripts/eval_arms.py tekmen --vault ~/vault --questions ~/vault/eval/tekmen-eval.yml --arms C

TEKMEN_EVAL_PATH=~/vault/eval/tekmen-eval.yml \
  python3 scripts/eval_arms.py tekmen --vault ~/vault --arms A,B,C
```

A path inside the repo is refused, except the example fixture. Default results go to `<vault>/.memex/eval/tekmen`. Any other results directory must be outside the repo or under a `.memex` directory.

Arm C reads the operator's vault (it does not build a temporary one). The meter line is appended to that vault's `.memex/meter.jsonl` with route `eval.tekmen`, so `memex meter --vault ~/vault` includes it. `hit` is `true` when every gold token appears in the prediction, or when token F1 is at least `--hit-at`.

`expected_slugs` is optional. `slugs_hit` in `results.jsonl` is true when every expected slug was in the arm-C retrieval. The meter `hit` field follows the answer score, not the slug overlap.

### Question file

YAML or JSON, version 1. A bare list of question objects is also accepted.

```yaml
version: 1
questions:
  - id: sample-reminder-1
    category: reminder          # reminder | decision | company-fact, or your own label
    question: "When is the synthetic launch review?"
    answer: "1 June 2026"
    expected_slugs: ["sample-launch"]   # optional
```

`id` defaults to `q1`, `q2`, … when omitted. `question` and `answer` are required. `category` defaults to `unspecified` and is how the report groups accuracy. `type` may be omitted, or set to `question`.

### Long tasks

A file may also contain `type: long_task` items, mixed with short questions. This is the shape for a long deal: a brief, stated assumptions, conflicting evidence, a deliverable, and a rubric. The committed file `evals/long-task.example.yml` is one fictional task (Sample Harbor Co-op). A real file stays outside the repo, the same way as the short questions.

```bash
python3 scripts/eval_arms.py tekmen \
  --vault ~/vault \
  --questions ~/vault/eval/long-task.yml \
  --arms A
python3 scripts/eval_arms.py tekmen --vault ~/vault --questions ~/vault/eval/long-task.yml --arms B
python3 scripts/eval_arms.py tekmen --vault ~/vault --questions ~/vault/eval/long-task.yml --arms C
python3 scripts/eval_arms.py tekmen --vault ~/vault --questions ~/vault/eval/long-task.yml --arms A,B,C
```

The synthetic example is the one in-repo path that is allowed to load:

```bash
python3 scripts/eval_arms.py tekmen \
  --vault ~/vault \
  --questions evals/long-task.example.yml \
  --arms A
```

Arm A sees the task packet and no notes. Arm B sees the librarian rules and `Retrieved notes: (none)`. Arm C reads every `inputs` slug or vault-relative path first, then fills the remaining budget with BM25 over the title and the brief. The retrieval budget is `--long-k` (default 16, larger than `--k`) and the output budget is `--long-max-tokens` (default 2048). Note bodies in that prompt are capped at 8000 characters. A missing input is recorded on the row and does not stop the run. The meter route for arm C is `eval.long_task`. Arms A and B do not write a meter line.

```yaml
version: 1
questions:
  - type: long_task
    id: sample-harbor-terms          # required
    title: "Sample Harbor Co-op payment terms"
    brief: "Recommend payment terms for the fictional buyer."
    inputs: ["harbor-terms", "harbor-objection"]   # slugs or vault-relative paths
    assumptions:
      - "The launch date in the notes is the only date that counts."
    conflicts:
      - claim: "Sample Harbor already signed net-15."
        sources: ["harbor-objection"]
    deliverable: "A one-page recommendation."
    max_score: 5
    rubric:
      - id: terms
        description: "States the net-45 terms."
        weight: 3
        kind: required               # required | bonus | penalty
        check: "net-45"              # string or list; optional
      - id: unsupported
        description: "Repeating a conflict claim without its source."
        weight: 2
        kind: penalty
        check: unsupported_claims
```

Validation errors name the task id and the field. `assumptions` and `conflicts` may be empty lists. `inputs` and `rubric` may not. Criterion ids are unique. `weight` and `max_score` are numbers greater than 0.

### Rubric grading

The default judge is deterministic (`--judge mock`). It does not call a model.

- A `required` or `bonus` criterion earns its weight when every `check` hint is present. A hint matches as a case-insensitive substring, or as a `[[slug]]` citation of that hint's stem. A criterion with no `check` earns 0 under this grader.
- A `bonus` miss scores 0. It does not subtract.
- A `penalty` subtracts its weight when a hint is present. The hint `unsupported_claims` subtracts when the memo states a conflict `claim` and cites none of that claim's `sources`.
- The weighted total is clamped to `[0, max_score]`. The row `score` is that total divided by `max_score`, so a mixed file still averages with short questions. `hit` follows `--hit-at` on that score.

`--judge live` asks the model for the same table as one JSON object. It uses the same route as `--model live`: `MEMEX_MODEL_URL` only, unless `--allow-remote` is set. Check hints are not sent to the judge. A reply that is not JSON is an error.

`report.md` prints a criterion table per long task per arm (`id`, `kind`, `weight`, `earned`, `detail`) and the weighted total. `report.json` stores that table under `arms.<arm>.long_tasks`. `results.jsonl` adds `type`, `title`, `weighted_total`, `max_score`, `criteria`, `missing_inputs`, and `prediction_slugs` on long-task rows.

## What stays out of git

`.gitignore` ignores `locomo10.json`, `tekmen-eval.local.*`, `long-task.local.*`, `evals/private/`, and `.memex/`. CI runs `python3 scripts/guard_private_eval.py`, which fails the build if any of those names are committed, and also if any other file name contains `long-task` or `long_task`. The three synthetic fixtures are the allowlist:

- `evals/locomo.sample.json`
- `evals/tekmen-eval.example.yml`
- `evals/long-task.example.yml`
