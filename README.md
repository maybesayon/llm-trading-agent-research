# How Much of LLM Trading-Agent Performance Survives Bias-Controlled Evaluation?

Pre-registered-style empirical study: a pre-specified, bias-controlled
evaluation of sentiment-driven LLM trading strategies (six-strategy ladder,
three-condition memorization-quantification protocol, out-of-cutoff
validation, rationale audit) on US large-cap equities.

**Status: pre-experiment.** The protocol is frozen; the pipeline is built and
validated on synthetic data (83 passing tests, engine reconciled against an
independent implementation at 1e-12); the pilot (Phase 3) awaits real-data
execution. No empirical results exist yet, and nothing in this repository
claims any.

## Layout

```
paper/        manuscript.md / manuscript.pdf (v2.0, results-pending)
src/          pipeline: ingestion, integrity, backtest, strategies (S1-S6),
              anonymization, agents (cached LLM client), evaluation
tests/        synthetic-data validation incl. failure-path and leakage tests
configs/      YAML mirrors of the frozen protocol (Appendix D)
scripts/      pilot orchestrator, freeze-value recorder
runbooks/     step-by-step instructions for real-world execution
docs/         freeze document, protocol checklist, audits, proposal, outline
protocol.lock.yaml   machine-readable protocol lock (blocks runs while pending)
```

## Quick start

```
pip install -r requirements.txt
python -m pytest        # 83 tests, no network, no models
```

Real-data execution (downloads, GPU inference): see `runbooks/pilot_runbook.md`.

## Research-integrity design

- Frozen protocol with append-only Amendment Log (`protocol.lock.yaml`, docs/).
- Look-ahead prevention is structural and tested by injection.
- Every LLM call cached as a release artifact; seeds, revisions, and config
  hashes logged per run.
- Interpretation rules for all outcomes pre-committed in the manuscript
  (Sections 5, 7) before any experiment.

## Citation

Upadhyay, S. (2026). *How much of LLM trading-agent performance survives
bias-controlled evaluation? An independent study with a rationale audit.*
Pre-experiment manuscript v2.0.

## Disclaimer

Simulated backtesting only. Nothing here is investment advice.
