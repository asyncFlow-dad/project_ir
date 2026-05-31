# Leaderboard Record - 2026-05-30

## Eval47 Pre-Submit Candidate

- Current best baseline: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Current best public MAP/MRR: `0.9561` / `0.9591`
- Candidate file: `submissions/eval47_single_20260530/eval47_atomic_number_base_eval309.jsonl`
- Model: `solar-pro3`
- Source row: `submissions/gemma4_best_plus_consensus_eval42_47_53_295_20260523.jsonl`
- Changed eval ID: `47`
- Query: `원자번호 원자내 어떤 소립자 관계 있는`
- Rationale:
  - Eval `47` was not found in the public-result ledger or prior result records.
  - Candidate top-1 directly states that atomic number represents the number of protons in the nucleus.
  - Baseline top-1 is a copper-specific example; still relevant, but less general for the query.
  - Local relevance score improved from `0.160714` to `0.392857`.
- Validation:
  - Local: `rows=220`, `empty_topk=20`, `duplicate_topk=0`
  - Local diff vs baseline: `changed=1`, `top1_changed=1`, `empty_to_filled=0`, `filled_to_empty=0`
  - Remote: `rows=220`, `empty_topk=20`, `duplicate_topk=0`
  - Remote diff vs baseline: `changed=1`, `top1_changed=1`, `empty_to_filled=0`, `filled_to_empty=0`
  - SHA-256: `7f9f4bca82af99aa685d480b3e8e96b839c87737a34a10c402832a5b59f7893a`
- Test:
  - Local: `python3 -B -m unittest tests.test_submission_doc_audit tests.test_patch_submission tests.test_submission_diff_report` passed.
  - Remote: `/opt/conda/bin/python -B -m unittest tests.test_submission_doc_audit tests.test_patch_submission tests.test_submission_diff_report` passed.

## Submission Order

1. Submit `submissions/eval47_single_20260530/eval47_atomic_number_base_eval309.jsonl`.
2. Model name: `solar-pro3`.
3. If score improves, use this as current baseline and record result before creating branch/PR.
4. If score ties or regresses, lock out eval `47`; do not stack it with other residual candidates.

## Eval47 Submission Result

- Submitted file: `submissions/eval47_single_20260530/eval47_atomic_number_base_eval309.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
  - Public MAP/MRR: `0.9561` / `0.9591`
- Reported public MAP: `0.9561`
- Reported public MRR: `0.9591`
- Result: tied current best.
- Decision:
  - Eval `47` is public-neutral.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Lock out eval `47`; do not stack it with other residual candidates.
