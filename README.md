# How Much of LLM Trading-Agent Performance Survives Bias-Controlled Evaluation?

## 📄 [**Read the paper (PDF) →**](paper/manuscript.pdf)

**Pre-registered study, v2.0 (pre-experiment).** The protocol was frozen and
time-stamped (tag `v2.0-pre-experiment`) before any empirical run, so the
manuscript contains the full design and pre-committed interpretation rules, and
its result sections are deliberately empty placeholders. No results are claimed.

[![Paper](https://img.shields.io/badge/paper-PDF-b31b1b)](paper/manuscript.pdf)
[![Status](https://img.shields.io/badge/status-pre--experiment-orange)](#research-integrity-design)
[![Tests](https://img.shields.io/badge/tests-85%20passing-brightgreen)](#quick-start)

Pre-registered-style empirical study: a pre-specified, bias-controlled
evaluation of sentiment-driven LLM trading strategies (six-strategy ladder,
three-condition memorization-quantification protocol, out-of-cutoff
validation, rationale audit) on US large-cap equities.

**Status: pre-experiment.** The protocol is frozen; the pipeline is built and
validated on synthetic data (85 passing tests, engine reconciled against an
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
python -m pytest        # 85 tests, no network, no models
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

## Authorship and contributors

**Author:** Sayon Upadhyay (Dept. of Computer Science, University of North
Texas; independent student research). The study design, protocol, and
research decisions are the author's.

**Contributor:** Claude (AI assistant, Anthropic) assisted with implementation,
data-pipeline work, and drafting under the author's direction. The author
reviews and is responsible for all content.

## Disclaimer

Simulated backtesting only. Nothing here is investment advice.
