# Manuscript evolution (July 2026)

This folder preserves how the study design and paper developed, before any
experiment was run. Files are archival: nothing here is authoritative. The
current manuscript is `paper/manuscript.tex` and the current protocol is
`protocol.lock.yaml` together with `docs/experimental_freeze_document.md`.

Every stage below predates all empirical work. Together with the tagged
`v2.0-pre-experiment` commit, it documents that the design, metrics, and
interpretation rules were fixed before any data could influence them.

## Stages

| Stage | File(s) | What changed and why |
|---|---|---|
| 1a | `01a_proposal_v1.md` | First proposal: LLM trading agents vs. baselines with a sentiment/interpretability angle. A critical review found a data-window contradiction (FNSPID ends 2023, yet the test needed post-cutoff data), no thesis, undefined portfolio construction, and no multiple-testing control. |
| 1b | `01b_proposal_v2.md` | Revised proposal answering that review. It adds the explicit thesis, a two-track data design (Track A historical + Track B out-of-cutoff), the memorization-quantification protocol, the supervised-ML baseline (S4), deflated Sharpe ratio as the primary endpoint, and a pinned open-weight model. |
| 1c | `01c_paper_outline.md` | Paragraph-level outline, fixing each section's purpose, evidence, and word budget before drafting. |
| 2 | `02_section_drafts/` | Section-by-section drafts, each written after literature verification and revised after a peer-review pass. Results, audit, and discussion were drafted as pre-committed frameworks, never as findings. |
| 3 | `03_pre_submission_audit.md` | Audit mapping each research question to its method, metric, interpretation rule, and overclaim guard. It found one gap, the pilot news-density criterion, which was then fixed as frozen metrics M1/M2. |
| 4 | `04_manuscript_integrated_v1.md` | First integrated manuscript (v1.0). |
| 5 | `paper/manuscript.md` → `paper/manuscript.tex` | v2.0, the current version. It adds editorial integration, Amendment A-001 (sampling configuration, not outcome-triggered), the recorded implementation conventions, LaTeX typesetting, and the figures and tables. The v2.0 changes are presentation only; no scientific content changed. |

## Protocol changes after freeze

These are recorded only in the Amendment Log (manuscript appendix and
`protocol.lock.yaml`), never by editing history:

- **A-001** (2026-07-09): temperature 0.0 → 0.7, top_p 1.0 → 0.8, following
  Qwen3 vendor guidance. Not outcome-triggered; no experiments had run.
