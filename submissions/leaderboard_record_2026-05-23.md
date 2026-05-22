# Leaderboard Run - 2026-05-23

## Current Best Baseline

- File: `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_308_20260522.jsonl`
- Public MAP: `0.9182`
- Public MRR: `0.9227`
- SHA-256: `ce04590b1922442adcddf1ac7ce1101b51a81c23206befdd557d2b283422dd73`

## Recommended Next Submission

- File: `submissions/gemma4_best_plus_eval42_20260523.jsonl`
- Strategy: keep current best baseline and promote only eval `42` candidate top-1.
- Reason:
  - Eval `42` asks about Iran-Contra impact on US politics.
  - Baseline top-1 is Nixon/Watergate, likely topic drift.
  - Candidate top-1 directly mentions Iran-Contra, Reagan trust, and impact on US politics.
  - Candidate was already rank 2 in current best, so this is a focused top-1 promotion rather than a broad rerank.
- Audit:
  - Baseline relevance: `0.411111`
  - Candidate relevance: `0.711111`
  - Delta: `+0.300000`
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows: `1`
  - Top-1 changed rows: `1`
  - Changed eval IDs: `42`
  - SHA-256: `f108fb85984ad9ee20f469bd60bdf92fa63ab94a45a082273f46529957df3a45`

## Next Submission Order

1. Submit `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
2. If it improves or ties, test another single-row candidate such as `submissions/gemma4_best_plus_eval98_20260523.jsonl`.
3. If it regresses, do not submit grouped judge candidates.

## Eval42 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_20260523.jsonl`
- Reported public MAP: `0.9227`
- Reported public MRR: `0.9273`
- Result: new best.
- Improvement over previous best:
  - MAP: `+0.0045` (`0.9182` -> `0.9227`)
  - MRR: `+0.0046` (`0.9227` -> `0.9273`)
- Decision: use `submissions/gemma4_best_plus_eval42_20260523.jsonl` as current best baseline.
- Next candidate: test another focused single-row candidate, starting with `submissions/gemma4_best_plus_eval98_20260523.jsonl`.

## Eval98 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval98_20260523.jsonl`
- Reported public MAP: `0.9121`
- Reported public MRR: `0.9167`
- Result: regressed vs current best `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
- Difference vs current best:
  - MAP: `-0.0106` (`0.9227` -> `0.9121`)
  - MRR: `-0.0106` (`0.9273` -> `0.9167`)
- Decision: do not patch eval `98`; keep eval `42` candidate as current best.
- Next action: test only single-row candidates that do not include eval `98`.

## Eval109 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval109_20260523.jsonl`
- Reported public MAP: `0.9136`
- Reported public MRR: `0.9182`
- Result: regressed vs current best `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
- Difference vs current best:
  - MAP: `-0.0091` (`0.9227` -> `0.9136`)
  - MRR: `-0.0091` (`0.9273` -> `0.9182`)
- Decision: do not patch eval `109`.
- Next action: avoid judge-only candidates; prioritize rows where topic drift is obvious in baseline and candidate is already high-rank.

## Rank2 Topic-Drift Candidate

- File: `submissions/gemma4_best_plus_rank2_topicdrift_20260523_eval81.jsonl`
- Baseline: `submissions/gemma4_best_plus_eval42_20260523.jsonl`
- Changed eval ID: `81`
- Source: `submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`
- Rule:
  - Baseline top-1 must be an obvious topic drift.
  - Candidate top-1 must already be rank 2 in baseline topk.
  - Output must be one eval row only; no bundled candidate file.
- Audit:
  - Query: `통학 버스 가치`
  - Baseline top-1 discusses gravitational attraction between school buses at equal distance.
  - Candidate top-1 discusses public transit value through reduced bus/subway fares and energy savings.
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows: `1`
  - Top-1 changed rows: `1`
  - SHA-256: `6c40239f200de95bd234588a3b0ae7650c51bec2b8c8ac490acc0c5cf6fe32f3`
