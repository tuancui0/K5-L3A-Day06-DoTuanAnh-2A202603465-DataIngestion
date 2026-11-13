"""Evaluate retrieved evidence and preserve per-query traces."""
from __future__ import annotations

from typing import Any


def _matches_gold(question: dict[str, Any], hit: dict[str, Any]) -> bool:
    gold_source = question.get("gold_source_id") or question.get("source_id")
    gold_pages = question.get("gold_page")
    if isinstance(gold_pages, list):
        gold_page_values = {int(p) for p in gold_pages}
    elif gold_pages is None:
        gold_page_values = set()
    else:
        gold_page_values = {int(gold_pages)}

    hit_source = hit.get("source") or hit.get("metadata", {}).get("source") or hit.get("document_id")
    hit_page = hit.get("page")
    hit_text = (hit.get("text") or "").lower()

    source_match = bool(gold_source) and (gold_source == hit_source or gold_source == hit.get("document_id"))
    page_match = bool(gold_page_values) and int(hit_page) in gold_page_values
    evidence_match = False
    evidence_quote = (question.get("evidence_quote") or "").strip().lower()
    if evidence_quote:
        evidence_match = evidence_quote in hit_text

    return source_match or page_match or evidence_match


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    """Check source/page and enough gold evidence; keep hit@1 and hit@3 trace."""
    trace = {
        "question_id": question.get("id"),
        "strategy": question.get("strategy"),
        "split": question.get("split"),
        "hit@1": False,
        "evidence_hit@3": False,
        "matched_hit": None,
        "top_hits": [],
    }

    if not hits:
        return trace

    for index, hit in enumerate(hits[:3]):
        trace["top_hits"].append(hit.get("chunk_id"))
        if _matches_gold(question, hit):
            trace["matched_hit"] = hit.get("chunk_id")
            if index == 0:
                trace["hit@1"] = True
            trace["evidence_hit@3"] = True
            break

    if hits and _matches_gold(question, hits[0]):
        trace["hit@1"] = True
    return trace


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate Hit@1 and Evidence Hit@3 by strategy and split."""
    summary: dict[str, Any] = {}
    for trace in traces:
        strategy = trace.get("strategy")
        split = trace.get("split")
        key = (strategy, split)
        if key not in summary:
            summary[key] = {"count": 0, "hit1": 0, "hit3": 0}
        summary[key]["count"] += 1
        if trace.get("hit@1"):
            summary[key]["hit1"] += 1
        if trace.get("evidence_hit@3"):
            summary[key]["hit3"] += 1

    final = {}
    for (strategy, split), values in summary.items():
        total = values["count"]
        final[f"{strategy}:{split}"] = {
            "count": total,
            "hit1": values["hit1"],
            "hit3": values["hit3"],
            "hit1_rate": values["hit1"] / total if total else 0.0,
            "hit3_rate": values["hit3"] / total if total else 0.0,
        }
    return final
