"""Main pipeline entry point for Day 06 data ingestion benchmarking."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder
from .evaluation import evaluate_query, summarize
from .models import Chunk, DocumentPage
from .store import PgVectorStore

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BENCHMARK_DIR = ROOT / "benchmark"
RESULTS_DIR = ROOT / "results"


def load_corpus_json(path: Path) -> list[DocumentPage]:
    with path.open("r", encoding="utf-8") as handle:
        pages = json.load(handle)
    return [
        DocumentPage(
            document_id=p["document_id"],
            source=p["source"],
            page=int(p["page"]),
            text=p["text"],
            metadata={
                "chapter": p.get("chapter"),
                "module_id": p.get("module_id"),
                "title": p.get("title"),
                "character_count": p.get("character_count"),
            },
        )
        for p in pages
    ]


def build_default_benchmark(path: Path) -> list[dict[str, Any]]:
    questions = [
        {"id": "q01", "split": "dev", "question": "What is the main reason Python is popular in this chapter?", "expected_answer": "It has a large library ecosystem and straightforward syntax.", "gold_source_id": "openstax-python-foundations", "gold_page": 1, "evidence_quote": "Python is popular because many libraries exist for doing real work and the syntax is concise and straightforward.", "filter": None},
        {"id": "q02", "split": "dev", "question": "How does the print() function differ when you use sep and end?", "expected_answer": "sep sets the separator between values, while end sets the final character after the printed output.", "gold_source_id": "openstax-python-foundations", "gold_page": 2, "evidence_quote": "The sep option can be used to change this behavior. By default, the print() function adds a newline character at the end of the output.", "filter": None},
        {"id": "q03", "split": "dev", "question": "What are the three parts of an input() statement?", "expected_answer": "A variable, the input() function, and a prompt.", "gold_source_id": "openstax-python-foundations", "gold_page": 2, "evidence_quote": "An input statement, variable = input(\"prompt\"), has three parts: a variable, the input() function, and a prompt.", "filter": None},
        {"id": "q04", "split": "dev", "question": "What does the assignment operator = do in Python?", "expected_answer": "It assigns the value on the right to the variable on the left.", "gold_source_id": "openstax-python-foundations", "gold_page": 3, "evidence_quote": "A statement can set a variable to a value using the assignment operator (=).", "filter": None},
        {"id": "q05", "split": "dev", "question": "Why are variable names and variable assignment described as different from mathematical equality?", "expected_answer": "The equal sign in Python assignment stores a value in the variable, not a mathematical comparison.", "gold_source_id": "openstax-python-foundations", "gold_page": 3, "evidence_quote": "This is different from the equal sign of mathematics.", "filter": None},
        {"id": "q06", "split": "dev", "question": "Which content page explains the difference between a syntax error and a runtime error?", "expected_answer": "Page 6 introduces syntax errors and messages.", "gold_source_id": "openstax-python-foundations", "gold_page": 6, "evidence_quote": "Syntax error messages help identify issues in code structure.", "filter": None},
        {"id": "q07", "split": "dev", "question": "What is the purpose of comments in Python source code?", "expected_answer": "Comments explain code and are ignored by the interpreter.", "gold_source_id": "openstax-python-foundations", "gold_page": 7, "evidence_quote": "Comments are a way to annotate code and make it easier for humans to read.", "filter": None},
        {"id": "q08", "split": "dev", "question": "How is the string concatenation operation described in the book?", "expected_answer": "Strings can be combined by using the plus operator or by printing adjacent string values in a sequence.", "gold_source_id": "openstax-python-foundations", "gold_page": 4, "evidence_quote": "Concatenation combines strings into a longer string.", "filter": None},
        {"id": "q09", "split": "dev", "question": "What does the math module help compute in the expressions chapter?", "expected_answer": "It provides mathematical functions such as sqrt and more advanced numerical operations.", "gold_source_id": "openstax-python-foundations", "gold_page": 15, "evidence_quote": "The math module provides functions such as sqrt().", "filter": {"chapter": "Expressions"}},
        {"id": "q10", "split": "dev", "question": "What does floor division // do compared with regular division / ?", "expected_answer": "It discards the fractional remainder and returns the integer quotient.", "gold_source_id": "openstax-python-foundations", "gold_page": 14, "evidence_quote": "Floor division returns the integer part of the quotient without the remainder.", "filter": {"chapter": "Expressions"}},
        {"id": "q11", "split": "dev", "question": "What is the purpose of an if-else statement?", "expected_answer": "It chooses one branch of code when a condition is true and another when it is false.", "gold_source_id": "openstax-python-foundations", "gold_page": 20, "evidence_quote": "An if-else statement decides which branch to run based on a Boolean condition.", "filter": {"chapter": "Decisions"}},
        {"id": "q12", "split": "dev", "question": "How does Python decide whether an expression like a and b is true?", "expected_answer": "Python uses short-circuit evaluation and Boolean logic to determine truthiness.", "gold_source_id": "openstax-python-foundations", "gold_page": 21, "evidence_quote": "Boolean operations in Python use short-circuit evaluation.", "filter": {"chapter": "Decisions"}},
        {"id": "q13", "split": "dev", "question": "What does the `elif` keyword do in chained decisions?", "expected_answer": "It checks an additional condition when the earlier if condition is false.", "gold_source_id": "openstax-python-foundations", "gold_page": 23, "evidence_quote": "elif provides another condition check after if.", "filter": {"chapter": "Decisions"}},
        {"id": "q14", "split": "dev", "question": "What happens when a while loop condition is always true?", "expected_answer": "The loop never stops unless it is interrupted by break or some other exit condition.", "gold_source_id": "openstax-python-foundations", "gold_page": 26, "evidence_quote": "An infinite loop continues forever if the condition remains true.", "filter": {"chapter": "Loops"}},
        {"id": "q15", "split": "dev", "question": "What does the break statement do inside a loop?", "expected_answer": "It exits the loop immediately.", "gold_source_id": "openstax-python-foundations", "gold_page": 29, "evidence_quote": "The break command exits the loop immediately.", "filter": {"chapter": "Loops"}},
        {"id": "q16", "split": "test", "question": "What two concepts are central to functions in the Functions chapter?", "expected_answer": "Defining functions and using parameters to control behavior.", "gold_source_id": "openstax-python-foundations", "gold_page": 32, "evidence_quote": "Functions are defined with def and can take parameters.", "filter": {"chapter": "Functions"}},
        {"id": "q17", "split": "test", "question": "How does Python handle variable scope inside functions?", "expected_answer": "Variables may be local to a function unless declared global or otherwise referenced externally.", "gold_source_id": "openstax-python-foundations", "gold_page": 34, "evidence_quote": "Global variables are accessed differently from local variables inside a function.", "filter": {"chapter": "Functions"}},
        {"id": "q18", "split": "test", "question": "What is the purpose of a default parameter in a function definition?", "expected_answer": "It provides a fallback value when the caller does not pass an argument.", "gold_source_id": "openstax-python-foundations", "gold_page": 35, "evidence_quote": "A default parameter is used when no argument is supplied.", "filter": {"chapter": "Functions"}},
        {"id": "q19", "split": "test", "question": "Which chapter covers the `for` loop and the `range()` function?", "expected_answer": "The Loops chapter, particularly the page about for loops and range().", "gold_source_id": "openstax-python-foundations", "gold_page": 27, "evidence_quote": "The for loop often iterates over a range of numbers.", "filter": {"chapter": "Loops"}},
        {"id": "q20", "split": "test", "question": "What does the `input()` function return, and why is that important?", "expected_answer": "It returns a string entered by the user, which the program can store and use later.", "gold_source_id": "openstax-python-foundations", "gold_page": 2, "evidence_quote": "The input() function reads one line of input from the user and stores it in a variable.", "filter": None},
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions, ensure_ascii=False, indent=2), encoding="utf-8")
    return questions


def strategy_chunks(page: DocumentPage, strategy: str) -> list[Chunk]:
    if strategy == "A":
        return fixed_size(page, size=480, overlap=80)
    if strategy == "B":
        return by_paragraph(page, max_size=500)
    if strategy == "C":
        return by_paragraph(page, max_size=500)
    raise ValueError(f"Unknown strategy: {strategy}")


def create_strategy_vectors(strategy: str, pages: list[DocumentPage], embedder: MyEmbedder, store: PgVectorStore) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    for page in pages:
        chunks = strategy_chunks(page, strategy)
        if not chunks:
            continue
        for chunk in chunks:
            chunk.metadata["chapter"] = page.metadata.get("chapter")
            chunk.metadata["module_id"] = page.metadata.get("module_id")
            chunk.metadata["title"] = page.metadata.get("title")
            all_chunks.append(chunk)

    embeddings = embedder.embed_documents([chunk.text for chunk in all_chunks])
    store.upsert(strategy, all_chunks, embeddings)
    return all_chunks


def run_questions(strategy: str, questions: list[dict[str, Any]], embedder: MyEmbedder, store: PgVectorStore) -> list[dict[str, Any]]:
    traces: list[dict[str, Any]] = []
    for question in questions:
        query_vector = embedder.embed_query(question["question"])
        filters = question.get("filter") or {}
        hits = store.search(strategy, query_vector, top_k=3, filters=filters)
        trace = evaluate_query({**question, "strategy": strategy}, hits)
        traces.append(trace)
    return traces


def main() -> None:
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    benchmark_path = BENCHMARK_DIR / "questions.json"
    if not benchmark_path.exists():
        questions = build_default_benchmark(benchmark_path)
    else:
        questions = json.loads(benchmark_path.read_text(encoding="utf-8"))

    corpus_path = DATA_DIR / "corpus.json"
    if not corpus_path.exists():
        raise FileNotFoundError(f"Corpus JSON not found at {corpus_path}")
    pages = load_corpus_json(corpus_path)
    if len(pages) < 30:
        raise ValueError(f"Expected at least 30 content pages, found {len(pages)}.")

    env_database = ROOT / ".env"
    if env_database.exists():
        import os
        from dotenv import load_dotenv
        load_dotenv(env_database)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is missing. Copy starter/.env.example to starter/.env and start the database.")

    embedder = MyEmbedder()
    store = PgVectorStore(database_url, embedder.dimensions)

    strategy_summaries: dict[str, Any] = {}
    for strategy in ("A", "B", "C"):
        chunks = create_strategy_vectors(strategy, pages, embedder, store)
        traces = run_questions(strategy, questions, embedder, store)
        summary = summarize(traces)
        strategy_summaries[strategy] = {
            "chunk_count": len(chunks),
            "summary": summary,
            "traces": traces,
        }
        (RESULTS_DIR / f"{strategy}_trace.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2), encoding="utf-8")

    (RESULTS_DIR / "summary.json").write_text(json.dumps(strategy_summaries, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(strategy_summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    main()
