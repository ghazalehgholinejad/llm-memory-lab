# LLM Memory Lab

Compare **conversation history and memory selection** with an offline Python lab. Four strategies build inspectable context from synthetic conversations. No API keys or third-party runtime dependencies.

**No model is called.** This tests context selection, not answer quality. Compact means truncated excerpts, not generated summaries; retrieval means lexical overlap, not embeddings.

## Run

Python 3.10+ with SQLite, from this repository:

```bash
python -m memory_lab
python -m memory_lab --budget 450 --query "Which database did we choose?"
python -m unittest discover -s tests -v
```

Optional installation: `python -m pip install .`. Demo data lives in a temporary database that is removed afterwards. Output includes source IDs, evidence, character counts and provider-neutral prompts.

| Method | Selection | Tradeoff |
| --- | --- | --- |
| recent | Latest messages | Can omit old decisions |
| compact | First 100 characters of recent messages | Can omit crucial qualifiers; not a smart summary |
| retrieve | Query-word overlap, newest first on ties | Misses paraphrases and may retrieve outdated facts |
| hybrid | Alternate relevant and recent messages | Balances continuity and relevance without guaranteeing correctness |

Candidates that do not fit are skipped. Results are deduplicated and returned chronologically. The budget counts **Unicode characters in serialized evidence JSON**, including metadata, not model tokens or the whole prompt. Instructions, question, tools and output need additional model-specific budgeting.

The synthetic example changes a database choice from PostgreSQL to SQLite. Compare whether each strategy includes the old decision, the correction, both or neither. This small example does not prove one strategy superior.

## Persistent history

```python
from memory_lab.core import History, select, build_prompt
history = History('history.sqlite3')
history.append('demo', 'user', 'Use SQLite for the local demo.')
selection = select(history.messages('demo'), 'Which database?', 'hybrid', 800)
print(build_prompt('Which database?', selection))
history.forget('demo')
```

Session labels isolate queries; they are not authentication. This is a single-user local prototype with plaintext storage. Deletion removes records logically, not backups or disk remnants. History is never destructively compacted. There is no automatic profile extraction, TTL or cross-session fact memory.

Historical content is passed as data with provenance, not promoted to system instructions. This is not a guarantee against prompt injection. Retrieved claims can be wrong, stale or contradictory; an assistant's earlier claim is not user confirmation.

## Learning

- [Persian lesson and exercises](docs/LEARN_FA.md)
- [Design and extension roadmap](docs/DESIGN.md)
- `memory_lab/core.py`: store, selectors and prompt builder
- `tests/test_memory.py`: persistence, isolation, deletion, budgets and conflict retention

## References

- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — context selection, compaction and structured notes.
- [Python sqlite3 documentation](https://docs.python.org/3/library/sqlite3.html) — parameterized SQL and transactions.

Implementation and synthetic examples are original. Future work: embedding retrieval, source-grounded model summaries, user-confirmed facts with expiry, and separate answer-quality evaluation.
