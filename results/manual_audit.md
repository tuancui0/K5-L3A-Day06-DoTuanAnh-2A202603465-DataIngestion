# Manual audit — 5 dimensions

## 1) Retrieval accuracy
- Strategy A: 15/15 dev, 5/5 test on Hit@1; 15/15 dev, 5/5 test on Evidence Hit@3
- Strategy B: same
- Strategy C: same
- Conclusion: all strategies satisfy benchmark on this corpus.

## 2) Chunk coherence
- A: fragmented because fixed-size chunks split logical paragraphs
- B/C: higher coherence because paragraph-aware chunks preserve context
- Average coherence: B and C better than A

## 3) Metadata usefulness
- C is strongest because chapter filtering helps restrict retrieval when a question includes a chapter condition
- A/B have metadata but without filter usage
- This is useful in realistic retrieval systems with course/chapter constraints

## 4) Grounding quality
- Top-3 results contain gold evidence for all 5 test questions in each strategy
- No strong evidence failure in the test split
- Grounding is acceptable for this benchmark

## 5) Data strategy impact
- A is simplest but less semantically coherent
- B gives good balance and strong context retention
- C is best production choice because it keeps B’s quality and adds metadata filtering safety
- Limitation: benchmark is small (20 questions) and corpus is curated