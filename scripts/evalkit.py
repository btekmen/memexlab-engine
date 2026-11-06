"""LoCoMo scoring, the three-arm comparison, and the private Tekmen-eval.

No network unless the operator asks for it:

- ``--model mock`` (the default) never calls a model.
- ``--model live`` talks only to ``MEMEX_MODEL_URL`` (OpenAI-compatible,
  local vLLM / llama.cpp / Ollama / LM Studio).
- ``--allow-remote`` is the only switch that may send prompts to a hosted
  provider already configured in the environment.
- ``--fetch`` is the only switch that downloads the public LoCoMo file.

The public LoCoMo score matches snap-research/locomo ``task_eval/evaluation.py``:
token F1 (Porter stem, articles dropped) for categories 1–4, and an abstain
check for category 5. ``accuracy`` in the report is the mean of those
per-question scores — the number that script aggregates.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "memex-cli" / "src"
if SRC.is_dir() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memex_cli.meter import (  # noqa: E402
    annotate_hits,
    estimate_tokens,
    line_count,
    record as meter_record,
)
from memex_cli.search import search as vault_search  # noqa: E402
from memex_cli.vault import Vault  # noqa: E402

import yaml  # noqa: E402

ABSTAIN = "no information available"
LOCOMO_URL = "https://raw.githubusercontent.com/snap-research/locomo/main/data/locomo10.json"
NOTE_CHAR_CAP = 4000
EXAMPLE_QUESTIONS = (ROOT / "evals" / "tekmen-eval.example.yml").resolve()
ARMS = ("A", "B", "C")
ARM_LABEL = {
    "A": "model only",
    "B": "model + harness, no vault retrieval",
    "C": "model + harness + Memex retrieval",
}

# Integer ids in locomo10.json. The paper's numbered list is a different order.
CATEGORIES = {
    1: "multi-hop",
    2: "temporal",
    3: "open-domain",
    4: "single-hop",
    5: "adversarial",
}
_NAME_TO_ID = {name: num for num, name in CATEGORIES.items()}

# NLTK's default PorterStemmer (NLTK_EXTENSIONS), which LoCoMo calls.
# ``alli`` is applied first and the result is run through step 2 again.
_STEP2 = (
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"), ("anci", "ance"),
    ("izer", "ize"), ("bli", "ble"), ("alli", "al"), ("entli", "ent"),
    ("eli", "e"), ("ousli", "ous"), ("ization", "ize"), ("ation", "ate"),
    ("ator", "ate"), ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
    ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"), ("biliti", "ble"),
    ("fulli", "ful"), ("logi", "log"),
)
_IRREGULAR = {
    "skies": "sky", "sky": "sky", "dying": "die", "lying": "lie", "tying": "tie",
    "news": "news", "innings": "inning", "inning": "inning",
    "outings": "outing", "outing": "outing", "cannings": "canning",
    "canning": "canning", "howe": "howe", "proceed": "proceed",
    "exceed": "exceed", "succeed": "succeed",
}
_STEP3 = (
    ("icate", "ic"), ("ative", ""), ("alize", "al"), ("iciti", "ic"),
    ("ical", "ic"), ("ful", ""), ("ness", ""),
)
_STEP4 = (
    "ement", "ance", "ence", "able", "ible", "ment", "ant", "ent",
    "ism", "ate", "iti", "ous", "ive", "ize", "ion", "al", "er", "ic", "ou",
)


def _cons(word: str, i: int) -> bool:
    ch = word[i]
    if ch in "aeiou":
        return False
    if ch == "y":
        return i == 0 or not _cons(word, i - 1)
    return True


def _measure(word: str) -> int:
    n = i = 0
    length = len(word)
    while i < length and _cons(word, i):
        i += 1
    while i < length:
        while i < length and not _cons(word, i):
            i += 1
        if i >= length:
            break
        while i < length and _cons(word, i):
            i += 1
        n += 1
    return n


def _has_vowel(word: str) -> bool:
    return any(not _cons(word, i) for i in range(len(word)))


def _double_cons(word: str) -> bool:
    return len(word) >= 2 and word[-1] == word[-2] and _cons(word, len(word) - 1)


def _cvc(word: str) -> bool:
    """Porter ``*o``. NLTK also treats a two-letter VC stem as ``*o``."""
    if (len(word) >= 3 and _cons(word, len(word) - 3)
            and not _cons(word, len(word) - 2) and _cons(word, len(word) - 1)
            and word[-1] not in "wxy"):
        return True
    return len(word) == 2 and not _cons(word, 0) and _cons(word, 1)


def _step2(word: str) -> str:
    if word.endswith("alli") and _measure(word[:-4]) > 0:
        return _step2(word[:-4] + "al")
    for suf, repl in _STEP2:
        if word.endswith(suf):
            stem = word[:-len(suf)]
            # ``logi`` measures the stem plus the leading ``l`` (NLTK).
            ok = _measure(word[:-3]) > 0 if suf == "logi" else _measure(stem) > 0
            if ok:
                word = stem + repl
            break
    return word


def porter_stem(word: str) -> str:
    """Porter stemmer in NLTK's default mode, which LoCoMo uses."""
    word = word.lower()
    if word in _IRREGULAR:
        return _IRREGULAR[word]
    if len(word) <= 2:
        return word
    # Step 1a. Four-letter ``ies`` keeps the ``e`` (``ties`` → ``tie``).
    if word.endswith("ies") and len(word) == 4:
        word = word[:-1]
    elif word.endswith("sses"):
        word = word[:-2]
    elif word.endswith("ies"):
        word = word[:-2]
    elif word.endswith("ss"):
        pass
    elif word.endswith("s"):
        word = word[:-1]

    # Step 1b. ``ied`` is replaced outright; it does not take the ``ed`` tidy-up.
    if word.endswith("ied"):
        word = word[:-1] if len(word) == 4 else word[:-2]
    elif word.endswith("eed"):
        if _measure(word[:-3]) > 0:
            word = word[:-1]
    else:
        for suf in ("ed", "ing"):
            if word.endswith(suf):
                stem = word[:-len(suf)]
                if _has_vowel(stem):
                    word = stem
                    if word.endswith(("at", "bl", "iz")):
                        word += "e"
                    elif _double_cons(word) and word[-1] not in "lsz":
                        word = word[:-1]
                    elif _measure(word) == 1 and _cvc(word):
                        word += "e"
                break

    # Step 1c. ``y`` → ``i`` only after a consonant, and not on a one-letter stem.
    if word.endswith("y") and len(word) > 2 and _cons(word, len(word) - 2):
        word = word[:-1] + "i"

    word = _step2(word)
    for suf, repl in _STEP3:
        if word.endswith(suf):
            stem = word[:-len(suf)]
            if _measure(stem) > 0:
                word = stem + repl
            break
    for suf in _STEP4:
        if word.endswith(suf):
            stem = word[:-len(suf)]
            if suf == "ion" and (not stem or stem[-1] not in "st"):
                continue
            if _measure(stem) > 1:
                word = stem
            break
    if word.endswith("e"):
        stem = word[:-1]
        m = _measure(stem)
        if m > 1 or (m == 1 and not _cvc(stem)):
            word = stem
    if word.endswith("ll") and _measure(word[:-1]) > 1:
        word = word[:-1]
    return word


def normalize_answer(text: str) -> str:
    """LoCoMo ``normalize_answer``: lower, drop punctuation and a/an/the/and."""
    text = str(text).replace(",", "")
    text = text.lower()
    text = "".join(ch for ch in text if ch not in "\"#$%&'()*+-./:;<=>?@[\\]^_`{|}~!")
    text = re.sub(r"\b(a|an|the|and)\b", " ", text)
    return " ".join(text.split())


def _tokens(text: str) -> list[str]:
    return [porter_stem(w) for w in normalize_answer(text).split()]


def f1_score(prediction: str, ground_truth: str) -> float:
    pred = _tokens(prediction)
    gold = _tokens(ground_truth)
    if not pred or not gold:
        return 0.0
    common = Counter(pred) & Counter(gold)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0
    precision = num_same / len(pred)
    recall = num_same / len(gold)
    return (2 * precision * recall) / (precision + recall)


def f1_multi(prediction: str, ground_truth: str) -> float:
    """Category 1: comma-split, then mean of the best F1 for each gold part."""
    predictions = [p.strip() for p in str(prediction).split(",")]
    golds = [g.strip() for g in str(ground_truth).split(",")]
    if not golds:
        return 0.0
    scores = [max((f1_score(pred, gt) for pred in predictions), default=0.0) for gt in golds]
    return sum(scores) / len(scores)


def token_recall(prediction: str, ground_truth: str) -> float:
    pred = _tokens(prediction)
    gold = _tokens(ground_truth)
    if not gold:
        return 1.0 if not pred else 0.0
    common = Counter(pred) & Counter(gold)
    return sum(common.values()) / len(gold)


def category_id(value) -> int:
    if isinstance(value, bool):
        raise ValueError(f"bad LoCoMo category: {value!r}")
    if isinstance(value, int) and value in CATEGORIES:
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text.isdigit() and int(text) in CATEGORIES:
            return int(text)
        if text in _NAME_TO_ID:
            return _NAME_TO_ID[text]
    raise ValueError(f"bad LoCoMo category: {value!r}")


def score_locomo(category, prediction: str, answer: str) -> float:
    """One official per-question score. Category 3 gold is cut at the first ``;``."""
    cid = category_id(category)
    prediction = "" if prediction is None else str(prediction)
    answer = "" if answer is None else str(answer)
    if cid == 3:
        answer = answer.split(";", 1)[0].strip()
    if cid == 1:
        return f1_multi(prediction, answer)
    if cid in (2, 3, 4):
        return f1_score(prediction, answer)
    lowered = prediction.lower()
    if ABSTAIN in lowered or "not mentioned" in lowered:
        return 1.0
    return 0.0


def score_tekmen(prediction: str, answer: str, hit_at: float) -> tuple[float, bool]:
    """F1 plus a hit when every gold token is present or F1 clears ``hit_at``."""
    score = f1_score(prediction or "", answer or "")
    hit = token_recall(prediction or "", answer or "") == 1.0 or score >= hit_at
    return score, hit


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        return False


def assert_tekmen_questions_allowed(path: Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"question file not found: {resolved}")
    if _inside_repo(resolved) and resolved != EXAMPLE_QUESTIONS:
        raise PermissionError(
            "Tekmen-eval questions must live outside this repository "
            f"(refusing {resolved}). Copy the shape of evals/tekmen-eval.example.yml "
            "into the vault and pass that path via --questions or TEKMEN_EVAL_PATH."
        )
    return resolved


def assert_locomo_data_allowed(path: Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    if resolved.name == "locomo10.json" and _inside_repo(resolved):
        raise PermissionError(
            "refusing to read locomo10.json from inside the repo. "
            "Download it with --fetch or pass --data pointing outside the repo."
        )
    if not resolved.is_file():
        raise FileNotFoundError(f"LoCoMo file not found: {resolved}")
    return resolved


def assert_output_dir_allowed(path: Path, source: str) -> Path:
    resolved = Path(path).expanduser().resolve()
    if source == "tekmen" and _inside_repo(resolved) and ".memex" not in resolved.parts:
        raise PermissionError(
            "Tekmen-eval results stay local: write them outside the repo "
            "or under a .memex directory (gitignored)."
        )
    return resolved


def default_locomo_cache() -> Path:
    env = os.environ.get("MEMEX_LOCOMO_CACHE", "").strip()
    if env:
        return Path(env).expanduser()
    return Path.home() / ".cache" / "memex" / "locomo" / "locomo10.json"


def fetch_locomo(dest: Path, force: bool = False) -> Path:
    """Download the public dataset. Called only from ``--fetch``."""
    dest = Path(dest)
    if dest.is_file() and not force:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(LOCOMO_URL, headers={"User-Agent": "memexlab-eval"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())
    return dest


def load_locomo(path: Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("samples") or data.get("data") or []
    if not isinstance(data, list):
        raise ValueError("LoCoMo file must be a list of conversations")
    return data


def load_tekmen(path: Path) -> list[dict]:
    raw = Path(path).read_text(encoding="utf-8")
    if Path(path).suffix == ".json":
        data = json.loads(raw)
    else:
        data = yaml.safe_load(raw) or {}
    questions = data if isinstance(data, list) else (data.get("questions") or [])
    if not isinstance(questions, list):
        raise ValueError("question file needs a questions list")
    out = []
    for i, item in enumerate(questions):
        if not isinstance(item, dict) or not str(item.get("question") or "").strip():
            raise ValueError(f"question {i} needs a question string")
        if item.get("answer") is None or str(item.get("answer")).strip() == "":
            raise ValueError(f"question {item.get('id', i)} needs an answer")
        slugs = item.get("expected_slugs") or []
        if not isinstance(slugs, list):
            raise ValueError(f"question {item.get('id', i)} expected_slugs must be a list")
        out.append({
            "id": str(item.get("id") or f"q{i + 1}"),
            "category": str(item.get("category") or "unspecified"),
            "question": str(item["question"]).strip(),
            "answer": str(item["answer"]),
            "expected_slugs": [str(s) for s in slugs],
        })
    return out


def _slug(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(text).casefold()).strip("-")
    return (slug[:60] or "sample").strip("-")


def materialize_sample(sample: dict, root: Path) -> Vault:
    """Write one LoCoMo conversation into a fresh markdown vault. Local files only."""
    root = Path(root)
    if root.exists():
        shutil.rmtree(root)
    session_dir = root / "sessions"
    session_dir.mkdir(parents=True)
    conv = sample.get("conversation") or {}
    sample_id = str(sample.get("sample_id") or "sample")
    keys = sorted(
        (k for k in conv if re.fullmatch(r"session_\d+", k)),
        key=lambda k: int(k.split("_", 1)[1]),
    )
    for key in keys:
        turns = conv.get(key) or []
        if not isinstance(turns, list):
            continue
        n = key.split("_", 1)[1]
        when = str(conv.get(f"{key}_date_time") or "")
        lines = []
        if when:
            lines.append(f"Session date: {when}")
        speakers = [conv.get("speaker_a"), conv.get("speaker_b")]
        named = [str(s) for s in speakers if s]
        if named:
            lines.append("Speakers: " + ", ".join(named))
        lines.append("")
        for turn in turns:
            if not isinstance(turn, dict):
                continue
            dia = turn.get("dia_id") or ""
            speaker = turn.get("speaker") or ""
            text = str(turn.get("text") or "").strip()
            line = f"[{dia}] {speaker}: {text}".rstrip()
            caption = turn.get("blip_caption")
            if caption:
                line += f" (image: {caption})"
            lines.append(line)
        slug = _slug(f"locomo-{sample_id}-s{n}")
        front = {
            "title": f"{sample_id} session {n}" + (f" — {when}" if when else ""),
            "type": "source",
            "sample_id": sample_id,
            "session": n,
        }
        body = "\n".join(lines).rstrip() + "\n"
        (session_dir / f"{slug}.md").write_text(
            "---\n" + yaml.safe_dump(front, sort_keys=False, allow_unicode=True) + "---\n\n" + body,
            encoding="utf-8",
        )
    return Vault(root)


def _system_prompt(arm: str, notes: str) -> str:
    if arm == "A":
        return (
            "Answer the question in a short phrase. "
            f"If you do not know, say exactly: {ABSTAIN}."
        )
    rules = (
        "You are the Memex librarian, answering from a local vault.\n"
        "Rules:\n"
        "- Use only the notes in this prompt. Do not invent vault facts.\n"
        "- Cite a note you use as [[slug]].\n"
        f"- If the notes do not contain the answer, say exactly: {ABSTAIN}.\n"
        "- Do not claim a note was edited. Capture never overwrites an existing note.\n"
    )
    if arm == "B":
        return rules + "\nRetrieved notes:\n(none)\n"
    return rules + "\nRetrieved notes:\n" + (notes or "(none)") + "\n"


def _retrieve(vault: Vault, question: str, k: int, meter_path: Path, route: str) -> dict:
    start = line_count(meter_path)
    t0 = time.perf_counter()
    hits = vault_search(vault, question, limit=k)
    blocks = []
    slugs = []
    for hit in hits:
        note = vault.read(hit["path"])
        slugs.append(hit["slug"])
        blocks.append(f"[[{hit['slug']}]]\n{(note.get('body') or '')[:NOTE_CHAR_CAP].strip()}")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    text = "\n\n---\n\n".join(blocks)
    meter_record(
        vault.root, route=route, text=text, cited_slugs=slugs, query=question, path=meter_path,
    )
    return {
        "ms": elapsed_ms,
        "tokens": estimate_tokens(text),
        "slugs": slugs,
        "text": text,
        "meter_start": start,
    }


def build_complete(mode: str, *, allow_remote: bool = False, mock_answers: str | None = None,
                   env: dict | None = None, max_tokens: int = 256):
    """Return ``complete(system, user, max_tokens) -> str``. Mock is the default."""
    env = os.environ if env is None else env
    if mode == "mock":
        table = {}
        if mock_answers:
            table = json.loads(Path(mock_answers).read_text(encoding="utf-8"))
            if not isinstance(table, dict):
                raise ValueError("--mock-answers must be a JSON object of question -> answer")

        def complete(system, user, max_tokens=max_tokens, _table=table):
            return str(_table.get(user, ABSTAIN))

        complete.route = "mock"
        return complete

    if mode != "live":
        raise ValueError("model must be mock or live")

    if not allow_remote:
        url = (env.get("MEMEX_MODEL_URL") or "").strip()
        if not url:
            raise RuntimeError(
                "live model needs MEMEX_MODEL_URL, an OpenAI-compatible local endpoint "
                "(llama.cpp, vLLM, Ollama, LM Studio). "
                "Pass --allow-remote only if you intend to send prompts to a hosted provider."
            )
        from memex_cli.llm import complete as live_complete
        provider = {
            "kind": "openai", "url": url.rstrip("/"), "key": "",
            "model": (env.get("MEMEX_MODEL") or "").strip() or "default", "route": "local",
        }

        def complete(system, user, max_tokens=max_tokens, _p=provider):
            return live_complete(_p, system, user, max_tokens=max_tokens)["text"]

        complete.route = "local"
        return complete

    from memex_cli.llm import complete as live_complete, resolve_provider
    provider = resolve_provider(env)

    def complete(system, user, max_tokens=max_tokens, _p=provider):
        return live_complete(_p, system, user, max_tokens=max_tokens)["text"]

    complete.route = provider["route"]
    return complete


def _hit_from_score(score: float, hit_at: float) -> bool:
    return score >= hit_at


def _run_one(arm: str, item: dict, *, vault: Vault | None, complete, k: int,
             meter_path: Path | None, route: str, hit_at: float, kind: str,
             max_tokens: int) -> dict:
    question = item["question"]
    gold = item["answer"]
    retrieved = None
    if arm == "C":
        if vault is None or meter_path is None:
            raise RuntimeError("arm C needs a vault and a meter path")
        retrieved = _retrieve(vault, question, k, meter_path, route)
        system = _system_prompt("C", retrieved["text"])
    else:
        system = _system_prompt(arm, "")
    prediction = complete(system, question, max_tokens)
    if kind == "locomo":
        score = score_locomo(item["category"], prediction, gold)
        hit = _hit_from_score(score, hit_at)
        category = CATEGORIES[category_id(item["category"])]
    else:
        score, hit = score_tekmen(prediction, gold, hit_at)
        category = item["category"]
    if retrieved is not None:
        annotate_hits(meter_path, retrieved["meter_start"], hit)
    expected = item.get("expected_slugs") or []
    got = retrieved["slugs"] if retrieved else []
    return {
        "id": item["id"],
        "arm": arm,
        "category": category,
        "question": question,
        "answer": gold,
        "prediction": prediction,
        "score": round(score, 4),
        "hit": hit,
        "retrieval_ms": None if retrieved is None else round(retrieved["ms"], 3),
        "retrieved_tokens": None if retrieved is None else retrieved["tokens"],
        "cited_slugs": got,
        "expected_slugs": expected,
        "slugs_hit": bool(expected) and set(expected).issubset(set(got)),
    }


def _aggregate(rows: list[dict]) -> dict:
    by: dict[str, list[float]] = {}
    for row in rows:
        by.setdefault(row["category"], []).append(row["score"])
    cats = {}
    for name, scores in sorted(by.items()):
        cats[name] = {"n": len(scores), "accuracy": round(sum(scores) / len(scores), 4)}
    lats = [r["retrieval_ms"] for r in rows if r["retrieval_ms"] is not None]
    toks = [r["retrieved_tokens"] for r in rows if r["retrieved_tokens"] is not None]
    accuracy = round(sum(r["score"] for r in rows) / len(rows), 4) if rows else None
    return {
        "questions": len(rows),
        "accuracy": accuracy,
        "by_category": cats,
        "median_retrieval_ms": None if not lats else round(_median(lats), 3),
        "median_retrieved_tokens": None if not toks else round(_median(toks), 1),
        "mean_retrieved_tokens": None if not toks else round(sum(toks) / len(toks), 1),
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Eval report",
        "",
        f"Source: {report['source']}",
        f"Model route: {report['model_route']}",
        "",
        "Accuracy is the mean of the per-question scores.",
        "LoCoMo uses the public task_eval score (token F1, or the abstain check for adversarial).",
        "Retrieval time and tokens are measured only on arm C, and tokens come from the local meter.",
        "",
    ]
    for arm in report["arm_order"]:
        agg = report["arms"][arm]
        lines += [
            f"## Arm {arm} — {ARM_LABEL[arm]}",
            "",
            f"- questions: {agg['questions']}",
            f"- accuracy: {agg['accuracy']}",
            f"- median retrieval latency (ms): {agg['median_retrieval_ms']}",
            f"- median retrieved tokens: {agg['median_retrieved_tokens']}",
            f"- mean retrieved tokens: {agg['mean_retrieved_tokens']}",
            "",
            "| category | n | accuracy |",
            "| --- | ---: | ---: |",
        ]
        if not agg["by_category"]:
            lines.append("| (none) | 0 |  |")
        for cat, slot in agg["by_category"].items():
            lines.append(f"| {cat} | {slot['n']} | {slot['accuracy']} |")
        lines.append("")
    lines += [
        "Every question is one line in `results.jsonl`.",
        f"Meter file: `{report['meter_path']}` (`hit` filled from the score).",
        "",
    ]
    return "\n".join(lines)


def write_outputs(out: Path, report: dict, rows: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (out / "results.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    (out / "report.md").write_text(render_markdown(report), encoding="utf-8")


def _locomo_items(samples: list[dict], limit: int | None) -> list[tuple[dict, dict]]:
    pairs = []
    for sample in samples:
        qas = sample.get("qa") or []
        sample_id = str(sample.get("sample_id") or "sample")
        for i, qa in enumerate(qas):
            if not isinstance(qa, dict) or not str(qa.get("question") or "").strip():
                continue
            item = {
                "id": f"{sample_id}:{i}",
                "category": qa.get("category"),
                "question": str(qa["question"]).strip(),
                "answer": "" if qa.get("answer") is None else str(qa["answer"]),
                "expected_slugs": [],
                "_sample": sample,
            }
            pairs.append((sample, item))
            if limit is not None and len(pairs) >= limit:
                return pairs
    return pairs


def run_locomo(samples: list[dict], *, arms: list[str], complete, out: Path, k: int = 6,
               limit: int | None = None, hit_at: float = 0.5, max_tokens: int = 256,
               work: Path | None = None) -> dict:
    out = assert_output_dir_allowed(out, "locomo")
    meter_path = out / "meter.jsonl"
    work = Path(work) if work is not None else out / "vault"
    pairs = _locomo_items(samples, limit)
    if not pairs:
        raise ValueError("no LoCoMo questions to score")
    rows = []
    vaults: dict[str, Vault] = {}
    for sample, item in pairs:
        sid = str(sample.get("sample_id") or "sample")
        if sid not in vaults:
            vaults[sid] = materialize_sample(sample, work / _slug(sid))
        vault = vaults[sid]
        for arm in arms:
            rows.append(_run_one(
                arm, item, vault=vault, complete=complete, k=k, meter_path=meter_path,
                route="eval.locomo", hit_at=hit_at, kind="locomo", max_tokens=max_tokens,
            ))
    return _finish("locomo", arms, complete, rows, out, meter_path)


def run_tekmen(vault: Vault, questions: list[dict], *, arms: list[str], complete, out: Path,
               k: int = 6, hit_at: float = 0.5, max_tokens: int = 256,
               meter_path: Path | None = None) -> dict:
    out = assert_output_dir_allowed(out, "tekmen")
    meter_path = Path(meter_path) if meter_path is not None else (vault.root / ".memex" / "meter.jsonl")
    if not questions:
        raise ValueError("no Tekmen-eval questions to score")
    rows = []
    for item in questions:
        for arm in arms:
            rows.append(_run_one(
                arm, item, vault=vault, complete=complete, k=k, meter_path=meter_path,
                route="eval.tekmen", hit_at=hit_at, kind="tekmen", max_tokens=max_tokens,
            ))
    return _finish("tekmen", arms, complete, rows, out, meter_path)


def _finish(source: str, arms: list[str], complete, rows: list[dict], out: Path,
            meter_path: Path) -> dict:
    grouped = {arm: [r for r in rows if r["arm"] == arm] for arm in arms}
    report = {
        "cmd": "eval-arms",
        "source": source,
        "model_route": getattr(complete, "route", "unknown"),
        "arm_order": list(arms),
        "arms": {arm: _aggregate(grouped[arm]) for arm in arms},
        "meter_path": str(meter_path),
        "ok": True,
    }
    write_outputs(out, report, rows)
    report["out"] = str(out)
    report["rows_file"] = str(out / "results.jsonl")
    return report


def parse_arms(text: str) -> list[str]:
    arms = [part.strip().upper() for part in str(text).split(",") if part.strip()]
    if not arms:
        raise ValueError("pass at least one arm: A, B, or C")
    bad = [a for a in arms if a not in ARMS]
    if bad:
        raise ValueError(f"unknown arm {bad[0]!r} (use A, B, C)")
    return arms
