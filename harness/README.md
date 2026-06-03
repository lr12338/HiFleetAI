# Harness

Harness-driven evaluation for HiFleetAI Agent behavior.

Structure:

- `cases/`: JSONL evaluation cases
- `fixtures/`: local fixtures for docs and images
- `runners/`: eval runners
- `judges/`: deterministic judges first, LLM judges later
- `reports/`: generated reports, ignored by Git except this README

P0-06 provides the first executable skeleton:

```bash
python3 harness/runners/run_eval.py --list-cases
python3 harness/runners/run_eval.py --category faq
```

When the Agent API is unavailable, the runner writes structured failed results to
`harness/reports/latest.json` and `harness/reports/latest.md` instead of
pretending the case passed.
