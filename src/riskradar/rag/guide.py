"""Due-diligence policy assistant: BM25 over parsed policy rules, with citations."""

from __future__ import annotations

import functools
import re

from rank_bm25 import BM25Plus

from riskradar.settings import get_config, resolve_path


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def parse_guide(markdown: str) -> list[dict]:
    rules = []
    for block in re.split(r"^## ", markdown, flags=re.MULTILINE)[1:]:
        head, _, body = block.partition("\n")
        rules.append({"rule_id": head.strip(), "body": body.strip()})
    return rules


@functools.lru_cache(maxsize=1)
def _index() -> tuple[list[dict], BM25Plus, set[str], dict[str, str]]:
    cfg = get_config()["rag"]
    markdown = resolve_path(cfg["guide_path"]).read_text(encoding="utf-8")
    rules = parse_guide(markdown)
    docs = [_tokenize(f"{r['rule_id']} {r['body']}") for r in rules]
    vocab = {token for doc in docs for token in doc}
    by_id = {r["rule_id"]: r["body"] for r in rules}
    return rules, BM25Plus(docs), vocab, by_id


def rule_body(rule_id: str) -> str:
    _, _, _, by_id = _index()
    return by_id.get(rule_id, "")


def ask(question: str, top_k: int | None = None) -> dict:
    cfg = get_config()["rag"]
    top_k = top_k or cfg["top_k"]
    rules, bm25, vocab, _ = _index()
    # unseen terms carry a uniform BM25+ delta; drop them so junk scores zero
    tokens = [t for t in _tokenize(question) if t in vocab]
    if not tokens:
        return {"question": question, "matched": False, "rules": []}
    scores = bm25.get_scores(tokens)
    order = scores.argsort()[::-1][:top_k]
    hits = [
        {
            "rule_id": rules[i]["rule_id"],
            "score": round(float(scores[i]), 2),
            "body": rules[i]["body"],
        }
        for i in order
        if scores[i] >= cfg["min_score"]
    ]
    return {"question": question, "matched": bool(hits), "rules": hits}
