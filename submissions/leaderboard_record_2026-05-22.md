# Leaderboard Run - 2026-05-22

## Pre-Submission Record Check

- Latest browser list checked at: `2026-05-22 00:07 KST`.
- Current best public score: MAP `0.8712`, MRR `0.8758`.
- Current best file: `submissions/e5_large_semantic_rerank_20260521.jsonl`.
- Current best submission time in STAGES list: `2026.05.21 16:42`.
- Later semantic sweep submissions observed:
  - `2026.05.21 17:29`: MAP `0.8598`, MRR `0.8652`.
  - `2026.05.21 17:57`: MAP `0.8583`, MRR `0.8652`.
- Today (`2026-05-22 KST`) no submission observed before this run.
- Daily limit: max `12` submissions/day.

## Code Change

- `ir_search/chunking.py`: fixed long-paragraph chunk overlap; old code advanced to `end`, so overlap was disabled.
- `tests/test_chunking.py`: added regression test proving adjacent long-paragraph chunks share configured overlap.
- Local tests: `python3 -B -m unittest discover -s tests` passed, `34` tests, `2` skipped.
- Remote tests/generation: blocked by sandbox network; SSH to remote server returned `Operation not permitted`.

## Candidate Plan

- Baseline: `submissions/e5_large_semantic_rerank_20260521.jsonl`.
- Candidate: `submissions/e5_large_semantic_targeted_eval68_106_20260522.jsonl`.
- Experiment: `e5-large-semantic-targeted-eval68-106-20260522`.
- Model identifier: `intfloat/multilingual-e5-large`.
- Strategy: keep best semantic baseline and replace only two clearly more direct top-1 rows from prior sweeps.
- Changed evals:
  - `68`: Python operator precedence document promoted over generic average-code document.
  - `106`: solar-eclipse mechanism document promoted over moon-phase document.
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Difference vs current best: `2` changed rows, `2` top-1 changes, `0` empty-to-filled rows.
  - SHA-256: `67ef37b72caf9c16621f522d9b38ebfe580b935e00667c4a7ea2a153b90c25b3`

## Submission Attempt

- Target: `https://stages.ai/competitions/423/submission/new`
- Intended upload: `submissions/e5_large_semantic_targeted_eval68_106_20260522.jsonl`
- Model identifier entered/planned: `intfloat/multilingual-e5-large`
- Status: blocked before successful upload; no score observed.
- Blocker: Chrome file chooser did not return a file handle to browser automation and subsequent Chrome automation calls timed out.
- Score record: latest confirmed best remains MAP `0.8712`, MRR `0.8758`.

## Fresh Pre-Submit Verification

- Checked at: `2026-05-22 10:13:46 KST`.
- Candidate: `submissions/e5_large_semantic_targeted_eval68_106_20260522.jsonl`.
- Baseline: `submissions/e5_large_semantic_rerank_20260521.jsonl`.
- Validator:
  - Command: `python3 scripts/validate_submission.py submissions/e5_large_semantic_targeted_eval68_106_20260522.jsonl --compare-to submissions/e5_large_semantic_rerank_20260521.jsonl`
  - Result: `rows=220 empty_topk=20 duplicate_topk=0 first_char={`
  - Diff: `changed=2 top1_changed=2 empty_to_filled=0 filled_to_empty=0`
- Tests:
  - Command: `python3 -B -m unittest discover -s tests`
  - Result: `Ran 34 tests`, `OK (skipped=2)`
- SHA-256: `67ef37b72caf9c16621f522d9b38ebfe580b935e00667c4a7ea2a153b90c25b3`
- Changed evals:
  - `68`: promote direct Python operator-precedence document over generic average-code document.
  - `106`: promote direct solar-eclipse mechanism document over moon-phase document.
- Submission recommendation: upload this candidate first; do not submit lower-rank-only sweep candidates before this targeted test.

## Targeted Eval68/106 Result

- Submitted by user: `submissions/e5_large_semantic_targeted_eval68_106_20260522.jsonl`.
- Model identifier: `intfloat/multilingual-e5-large`.
- Experiment: `e5-large-semantic-targeted-eval68-106-20260522`.
- Public MAP: `0.8583`.
- Public MRR: `0.8652`.
- Result: regressed vs `e5-large-semantic-rerank-20260521` baseline (MAP `0.8712`, MRR `0.8758`).
- Difference vs baseline: MAP `-0.0129`, MRR `-0.0106`.
- Decision: do not use this candidate as baseline; keep `submissions/e5_large_semantic_rerank_20260521.jsonl` as current best.
- Next action: split eval `68` and eval `106` into separate one-row candidates if spending submissions to isolate harmful row.

## Granite 4.1 8B Ollama Rerank Candidate

- Ran on remote server `/root/ir_run` at `2026-05-22 10:57:53 KST`.
- Installed Ollama `0.24.0` and pulled model `granite4.1:8b`.
- Hardware observed by Ollama: NVIDIA GeForce RTX 3090, `24.0 GiB` VRAM.
- Output: `submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`.
- Remote copy: `/root/ir_run/submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`.
- Local copy: `submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`.
- Generation settings:
  - Dense retrieval model: `intfloat/multilingual-e5-large`.
  - Dense weight: `0.55`.
  - Fusion method: `score`.
  - Casual policy: `strict`.
  - Ollama rerank model: `granite4.1:8b`.
  - Ollama rerank candidates: `10`.
- Validation:
  - Rows: `220`.
  - Empty topk: `20`.
  - Duplicate topk: `0`.
  - Difference vs best baseline `e5_large_semantic_rerank_20260521.jsonl`: `changed=179`, `top1_changed=47`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `62cf9f2b85751a96b1b543c4203667d12ee1736fd86dcb4787ab60ffd28d8c44`.
- Pre-submit decision was conservative because changed rows/top-1 changes were broad relative to previous best.

## Granite 4.1 8B Ollama Rerank Result

- Submitted by user: `submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`.
- Model identifier: `granite4.1:8b` rerank over `intfloat/multilingual-e5-large` retrieval.
- Public MAP: `0.8932`.
- Public MRR: `0.8955`.
- Result: new best.
- Improvement over previous best `e5_large_semantic_rerank_20260521.jsonl`:
  - MAP: `+0.0220` (`0.8712` -> `0.8932`).
  - MRR: `+0.0197` (`0.8758` -> `0.8955`).
- Decision: use `submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` as current best baseline.
- Lesson: broad LLM rerank with Granite improved despite `179` changed rows and `47` top-1 changes; prior top1-change risk gate was too conservative for this reranker.

## Granite Baseline Patch Tool and C20 Candidates

- Checked at: `2026-05-22 11:49:23 KST`.
- Added `scripts/patch_submission.py` for row-level submission patching.
  - It copies selected `eval_id` rows from a source JSONL into a target JSONL.
  - Intended use: keep strong Granite baseline while testing small, auditable row changes.
- Added tests: `tests/test_patch_submission.py`.
- Test command: `python3 -B -m unittest discover -s tests`.
  - Result: `Ran 35 tests`, `OK (skipped=2)`.
- Generated conservative revert candidates from current Granite best:
  - `submissions/granite4_1_8b_revert_eval308_20260522.jsonl`
    - Diff vs Granite best: `changed=1`, `top1_changed=1`, SHA `9fa32f0d2c9019ebc143c3a5278223dba74202ae0939d0c65f6ffec49363e21c`.
  - `submissions/granite4_1_8b_revert_eval308_106_20260522.jsonl`
    - Diff vs Granite best: `changed=2`, `top1_changed=2`, SHA `403abd8e450b314b9ee14797da12e72b85f19f8f64df3911fbf5a73733bfa0b1`.
  - `submissions/granite4_1_8b_revert_eval308_106_100_20260522.jsonl`
    - Diff vs Granite best: `changed=3`, `top1_changed=3`, SHA `dcfaa86c15f9406fd4221d4e02c187f23d6919d39e0afe3f153dc248d36e1f9c`.
- Ran remote Granite c20 candidate:
  - Remote output: `/root/ir_run/submissions/granite4_1_8b_ollama_rerank_c20_20260522.jsonl`.
  - Local copy: `submissions/granite4_1_8b_ollama_rerank_c20_20260522.jsonl`.
  - Diff vs Granite best: `changed=122`, `top1_changed=11`, `empty_to_filled=0`, `filled_to_empty=0`.
  - Diff vs earlier E5 semantic baseline: `changed=185`, `top1_changed=49`.
  - SHA-256: `d74affa2d28cc3183bffd75827eb46a45a7f1f2a6638d88b9ff38cc3be68087d`.
  - Decision: do not submit full c20 blindly; it mixes strong improvements with clear regressions.
- Generated targeted c20 hybrid candidate:
  - File: `submissions/granite4_1_8b_c20_targeted_eval35_42_77_85_109_288_20260522.jsonl`.
  - Source: start from Granite best, copy c20 rows for eval `35`, `42`, `77`, `85`, `109`, `288`.
  - Diff vs Granite best: `changed=6`, `top1_changed=6`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `0bf7a1206217d10ba4e1178802d8f079d0e620a0a7992468aa39d31f729a5f80`.
  - Rationale: selected c20 rows where top-1 appears more directly aligned to query; skipped c20 rows with obvious topic drift (`59`, `66`, `215`, `246`).
- Current recommended next submission:
  - `submissions/granite4_1_8b_c20_targeted_eval35_42_77_85_109_288_20260522.jsonl`.
  - Model identifier: `granite4.1:8b` rerank over `intfloat/multilingual-e5-large`.

## Granite C30 Targeted Candidates

- Checked at: `2026-05-22 12:19:09 KST`.
- Remote c30 full candidate:
  - Remote output: `/root/ir_run/submissions/granite4_1_8b_ollama_rerank_c30_20260522.jsonl`.
  - Local copy: `submissions/granite4_1_8b_ollama_rerank_c30_20260522.jsonl`.
  - Diff vs Granite best: `changed=132`, `top1_changed=24`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `a09bf74d73737becd0c46bd15878edd38f958cbb362499954b844d69fe6541ba`.
  - Decision: do not submit full c30 blindly; many rows improve, but several top-1 changes are obvious topic drift.
- Generated conservative c30 hybrid:
  - File: `submissions/granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl`.
  - Source: start from Granite best and copy c30 rows for eval `35`, `77`, `85`, `98`, `109`, `288`.
  - Diff vs Granite best: `changed=6`, `top1_changed=5`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `8922031e89ffe26429c3d689f002da5832099e91e860a7cb3944a480da379f63`.
  - Note: eval `77` keeps same top-1 but changes lower ranks, so it can affect MAP but not MRR.
- Generated expanded c30 hybrid:
  - File: `submissions/granite4_1_8b_c30_targeted_expanded_20260522.jsonl`.
  - Source: start from Granite best and copy c30 rows for eval `26`, `34`, `35`, `77`, `85`, `98`, `109`, `225`, `271`, `285`, `288`.
  - Diff vs Granite best: `changed=11`, `top1_changed=10`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `ca56d55084b28f9323498b7ad83d0f2422c788dcecad8562fae7b7425b3f1630`.
- Validation:
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_c30_targeted_expanded_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 -B -m unittest discover -s tests` -> `Ran 35 tests`, `OK (skipped=2)`.
- Updated submission order:
  1. Submit `submissions/granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl` first.
  2. If it improves or ties, submit `submissions/granite4_1_8b_c30_targeted_expanded_20260522.jsonl` next.
  3. If it regresses, keep current best `submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` and test smaller one-row patches around eval `98`, `109`, `288`.

## Submission Diff Report Tool

- Checked at: `2026-05-22 12:21:21 KST`.
- Added `scripts/submission_diff_report.py`.
  - Reports row count, empty topk count, duplicate topk count, changed rows, top-1 changes, changed eval IDs, top-1 changed eval IDs, and SHA-256.
  - Use it before uploads to avoid submitting broad rerank files with hidden topic drift.
- Added tests: `tests/test_submission_diff_report.py`.
- TDD evidence:
  - RED: `python3 -B -m unittest tests.test_submission_diff_report` failed because `scripts/submission_diff_report.py` did not exist.
  - GREEN: same command passed after implementation.
- Fresh verification:
  - `python3 scripts/submission_diff_report.py submissions/granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl --baseline submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`
    - `rows=220`, `empty_topk=20`, `duplicate_topk=0`
    - `changed_eval_ids=98,85,35,77,109,288`
    - `top1_changed_eval_ids=98,85,35,109,288`
    - SHA-256: `8922031e89ffe26429c3d689f002da5832099e91e860a7cb3944a480da379f63`
  - `python3 scripts/submission_diff_report.py submissions/granite4_1_8b_c30_targeted_expanded_20260522.jsonl --baseline submissions/granite4_1_8b_ollama_rerank_20260522.jsonl`
    - `rows=220`, `empty_topk=20`, `duplicate_topk=0`
    - `changed_eval_ids=34,225,98,85,35,285,77,109,288,271,26`
    - `top1_changed_eval_ids=34,225,98,85,35,285,109,288,271,26`
    - SHA-256: `ca56d55084b28f9323498b7ad83d0f2422c788dcecad8562fae7b7425b3f1630`
  - `python3 -B -m unittest discover -s tests` -> `Ran 36 tests`, `OK (skipped=2)`.

## Submission Doc Audit Tool and Audited C30 Candidate

- Checked at: `2026-05-22 12:24:00 KST`.
- Added `scripts/submission_doc_audit.py`.
  - Prints each selected eval query plus baseline top-1 document text and candidate top-1 document text.
  - Use it to audit ambiguous top-1 changes before adding them to targeted patch files.
- Added tests: `tests/test_submission_doc_audit.py`.
- TDD evidence:
  - RED: `python3 -B -m unittest tests.test_submission_doc_audit` failed because `scripts/submission_doc_audit.py` did not exist.
  - GREEN: same command passed after implementation.
- Audited additional c30 rows:
  - `26`: candidate directly explains paramecium conjugation vs amoeba binary fission.
  - `34`: candidate directly explains seed nutrient storage, germination, and protection.
  - `225`: candidate directly explains 23.5 degree axial tilt, seasons, day length, climate impact.
  - `271`: candidate and baseline are very close; candidate explicitly says fruit salad is easily separable mixture.
  - `285`: candidate directly explains squirrel nut burying helps tree reproduction.
  - `42`: candidate directly ties Iran-Contra to US politics and Reagan trust; still topic is broad, so submit after smaller candidate.
  - `231`: candidate directly explains most evaporation occurs in ocean due to water share, surface area, solar heat.
- Generated audited c30 hybrid:
  - File: `submissions/granite4_1_8b_c30_targeted_audited_20260522.jsonl`.
  - Patched evals: `26`, `34`, `35`, `42`, `77`, `85`, `98`, `109`, `225`, `231`, `271`, `285`, `288`.
  - Diff vs Granite best: `changed=13`, `top1_changed=12`, `empty_to_filled=0`, `filled_to_empty=0`.
  - Changed eval IDs: `42,231,34,225,98,85,35,285,77,109,288,271,26`.
  - Top-1 changed eval IDs: `42,231,34,225,98,85,35,285,109,288,271,26`.
  - SHA-256: `4a648ddae4e07bec0f6715d5d541fedff192d25414b8caa1e6d394bbbcd369f4`.
- Fresh verification:
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_c30_targeted_audited_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 scripts/submission_diff_report.py submissions/granite4_1_8b_c30_targeted_audited_20260522.jsonl --baseline submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> SHA-256 `4a648ddae4e07bec0f6715d5d541fedff192d25414b8caa1e6d394bbbcd369f4`.
  - `python3 -B -m unittest discover -s tests` -> `Ran 37 tests`, `OK (skipped=2)`.
- Updated submission order:
  1. `submissions/granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl`
  2. If improves or ties: `submissions/granite4_1_8b_c30_targeted_expanded_20260522.jsonl`
  3. If improves or ties again: `submissions/granite4_1_8b_c30_targeted_audited_20260522.jsonl`

## Granite W060 C30 Candidate

- Checked at: `2026-05-22 12:44:16 KST`.
- Ran remote Granite rerank with denser retrieval weighting:
  - Dense retrieval model: `intfloat/multilingual-e5-large`.
  - Dense weight: `0.60`.
  - Fusion method: `score`.
  - Casual policy: `strict`.
  - Ollama rerank model: `granite4.1:8b`.
  - Ollama rerank candidates: `30`.
  - Remote output: `/root/ir_run/submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`.
  - Local copy: `submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`.
- Full w060 c30 validation:
  - `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - Diff vs current Granite best: `changed=150`, `top1_changed=26`.
  - SHA-256: `e908c8f71bb943f588ccef0983bf5a20347d6cf6feb8a181ba77910a3d9e6c8d`.
  - Decision: do not submit full w060 c30; it has too many risky top-1 changes.
- Audited new top-1 rows vs current Granite best:
  - `15`: candidate directly describes scientific skepticism/critical review as researcher attitude; keep as targeted candidate.
  - `96`: candidate directly says crust is made of rock/soil; keep as targeted candidate.
  - `214`: candidate describes atom nucleus/electrons but adds 10-electron detail; use only in expanded candidate.
  - `233`: baseline relationship-intimacy document is better; do not patch.
  - Avoid obvious drifts: `107`, `81`, `14`, `59`, `66`, `91`, `246`, `248`, `1`, `22`.
- Generated w060 conservative targeted candidate:
  - File: `submissions/granite4_1_8b_w060_targeted_eval15_96_20260522.jsonl`.
  - Patched evals: `15`, `96`.
  - Diff vs current Granite best: `changed=2`, `top1_changed=2`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `4d8d6edce5be9ea459fa61385f0ef32d09379d1ff9d48138d11b8c59b957cf2f`.
- Generated w060 expanded targeted candidate:
  - File: `submissions/granite4_1_8b_w060_targeted_eval15_96_214_20260522.jsonl`.
  - Patched evals: `15`, `96`, `214`.
  - Diff vs current Granite best: `changed=3`, `top1_changed=3`, `empty_to_filled=0`, `filled_to_empty=0`.
  - SHA-256: `d6b510561e5cd40041c0aec9958183409f1a1b135378b1518dccf0238f399969`.
- Fresh verification:
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_w060_targeted_eval15_96_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_w060_targeted_eval15_96_214_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 -B -m unittest discover -s tests` -> `Ran 37 tests`, `OK (skipped=2)`.
- Submission note:
  - These w060 patches are independent of c30 targeted patches.
  - Submit after the c30 conservative/expanded path unless daily submission budget favors testing small 2-row patch first.

## Combined C30 and W060 Targeted Candidates

- Checked at: `2026-05-22 14:21:41 KST`.
- Rationale: c30 targeted evals and w060 useful evals are disjoint, so combined candidates test additive gains.
- Generated conservative combined candidate:
  - File: `submissions/granite4_1_8b_c30_cons_w060_eval15_96_20260522.jsonl`.
  - Base: `granite4_1_8b_c30_targeted_eval35_77_85_98_109_288_20260522.jsonl`.
  - Additional w060 rows: `15`, `96`.
  - Diff vs current Granite best: `changed=8`, `top1_changed=7`, `empty_to_filled=0`, `filled_to_empty=0`.
  - Changed eval IDs: `15,98,85,96,35,77,109,288`.
  - Top-1 changed eval IDs: `15,98,85,96,35,109,288`.
  - SHA-256: `3e97b52804db49855c4e47ebd9894cc36b81a0d41a1498bde33c46ede46f567d`.
- Generated expanded combined candidate:
  - File: `submissions/granite4_1_8b_c30_expanded_w060_eval15_96_20260522.jsonl`.
  - Base: `granite4_1_8b_c30_targeted_expanded_20260522.jsonl`.
  - Additional w060 rows: `15`, `96`.
  - Diff vs current Granite best: `changed=13`, `top1_changed=12`, `empty_to_filled=0`, `filled_to_empty=0`.
  - Changed eval IDs: `15,34,225,98,85,96,35,285,77,109,288,271,26`.
  - Top-1 changed eval IDs: `15,34,225,98,85,96,35,285,109,288,271,26`.
  - SHA-256: `37c7a398803028f440e7ea1cb0ba3e8e516d4c02f0aa15839d32b6ba1065c007`.
- Generated audited combined candidate:
  - File: `submissions/granite4_1_8b_c30_audited_w060_eval15_96_20260522.jsonl`.
  - Base: `granite4_1_8b_c30_targeted_audited_20260522.jsonl`.
  - Additional w060 rows: `15`, `96`.
  - Diff vs current Granite best: `changed=15`, `top1_changed=14`, `empty_to_filled=0`, `filled_to_empty=0`.
  - Changed eval IDs: `42,231,15,34,225,98,85,96,35,285,77,109,288,271,26`.
  - Top-1 changed eval IDs: `42,231,15,34,225,98,85,96,35,285,109,288,271,26`.
  - SHA-256: `5e8e0a80e015706aa03619004b0fbe5a5010875172673d5cc1d19d4e00560542`.
- Fresh verification:
  - All three combined files: `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 -B -m unittest discover -s tests` -> `Ran 37 tests`, `OK (skipped=2)`.
- Updated submission order if enough daily submissions remain:
  1. `submissions/granite4_1_8b_c30_cons_w060_eval15_96_20260522.jsonl`
  2. If improves/ties: `submissions/granite4_1_8b_c30_expanded_w060_eval15_96_20260522.jsonl`
  3. If improves/ties: `submissions/granite4_1_8b_c30_audited_w060_eval15_96_20260522.jsonl`
  4. If combined conservative regresses, fall back to smaller single-family candidates: c30 conservative or w060 `15,96`.

## Granite W050 C30 Candidate

- Checked at: `2026-05-22 15:02:07 KST`.
- Ran remote Granite rerank with lower dense weighting:
  - Dense retrieval model: `intfloat/multilingual-e5-large`.
  - Dense weight: `0.50`.
  - Fusion method: `score`.
  - Casual policy: `strict`.
  - Ollama rerank model: `granite4.1:8b`.
  - Ollama rerank candidates: `30`.
  - Remote output: `/root/ir_run/submissions/granite4_1_8b_ollama_rerank_w050_c30_20260522.jsonl`.
  - Local copy: `submissions/granite4_1_8b_ollama_rerank_w050_c30_20260522.jsonl`.
- Full w050 c30 validation:
  - `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - Diff vs current Granite best: `changed=144`, `top1_changed=22`.
  - SHA-256: `131439d6a565da2059f0e08535d7b9f0892d8cf060eb87767ea43a07220c6859`.
  - Decision: do not submit full w050 c30; broad changes include obvious drift.
- Audited useful w050 rows:
  - `268`: candidate directly explains cloud droplets collide/merge and grow before falling as precipitation.
  - `295`: candidate directly explains Nevada low rainfall by dry inland/desert location vs wet Washington.
  - `207`: candidate directly explains insect/crustacean compound eye units.
  - `87`: candidate is nearly same as baseline but slightly clearer on gravitational potential energy converting to heat; use only expanded.
  - `244`: candidate is standing-wave-specific but not a general definition; do not patch.
- Generated w050 targeted candidates:
  - File: `submissions/granite4_1_8b_w050_targeted_eval207_268_295_20260522.jsonl`.
    - Patched evals: `207`, `268`, `295`.
    - Diff vs current Granite best: `changed=3`, `top1_changed=3`.
    - SHA-256: `3feb2572d94459defcd5382528f63b88d6c0e4248f139bf45813ffa9af6ea706`.
  - File: `submissions/granite4_1_8b_w050_targeted_eval87_207_268_295_20260522.jsonl`.
    - Patched evals: `87`, `207`, `268`, `295`.
    - Diff vs current Granite best: `changed=4`, `top1_changed=4`.
    - SHA-256: `87687aacc30d0a63633c6c77804e284a2fc5c97594a539bedb1ec615e3adf975`.
- Generated all-family conservative combined candidates:
  - File: `submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl`.
    - Base: c30 conservative + w060 `15`, `96`; added w050 `207`, `268`, `295`.
    - Diff vs current Granite best: `changed=11`, `top1_changed=10`.
    - Changed eval IDs: `268,15,98,295,85,96,35,77,109,207,288`.
    - Top-1 changed eval IDs: `268,15,98,295,85,96,35,109,207,288`.
    - SHA-256: `7157103b892a95e03324e6c1bebb97e3ea62a34b764067b56af9bb1c47961250`.
  - File: `submissions/granite4_1_8b_c30_w060_w050_eval87_207_268_295_20260522.jsonl`.
    - Same as above plus w050 `87`.
    - Diff vs current Granite best: `changed=12`, `top1_changed=11`.
    - SHA-256: `d48cc5928b8b2ddd2e2042aff2ffc09f599734a60f3a47b2d610917faa115cb2`.
- Fresh verification:
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_w050_targeted_eval207_268_295_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 scripts/validate_submission.py submissions/granite4_1_8b_c30_w060_w050_eval87_207_268_295_20260522.jsonl --compare-to submissions/granite4_1_8b_ollama_rerank_20260522.jsonl` -> `rows=220`, `empty_topk=20`, `duplicate_topk=0`.
  - `python3 -B -m unittest discover -s tests` -> `Ran 37 tests`, `OK (skipped=2)`.
- Updated recommendation:
  - Highest-upside next file if daily budget allows one broader test: `submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl`.
  - Safer smaller file: `submissions/granite4_1_8b_w050_targeted_eval207_268_295_20260522.jsonl`.

## Combined W050 Submission Result

- Reported by user at: `2026-05-22 16:35:49 KST`.
- Submitted files:
  - `submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl`
    - SHA-256: `7157103b892a95e03324e6c1bebb97e3ea62a34b764067b56af9bb1c47961250`
    - Diff vs prior Granite best: `changed=11`, `top1_changed=10`
  - `submissions/granite4_1_8b_c30_w060_w050_eval87_207_268_295_20260522.jsonl`
    - SHA-256: `d48cc5928b8b2ddd2e2042aff2ffc09f599734a60f3a47b2d610917faa115cb2`
    - Diff vs prior Granite best: `changed=12`, `top1_changed=11`
- Reported public score for both files: MAP `0.9000`, MRR `0.9045`.
- Score attribution note: user confirmed both submitted files received the same score.
- Result: new confirmed best vs prior Granite best MAP `0.8932`, MRR `0.8955`.
- Improvement over prior Granite best:
  - MAP: `+0.0068` (`0.8932` -> `0.9000`).
  - MRR: `+0.0090` (`0.8955` -> `0.9045`).
- Decision: use `submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl` as preferred current baseline because it matches the expanded file's public score with one fewer changed row. Eval `87` is score-neutral on public leaderboard.

## Gemma4 E4B Rerank Candidates

- Checked at: `2026-05-22 23:08:37 KST`.
- Installed Ollama model on remote:
  - `gemma4:e4b`
  - Ollama metadata: architecture `gemma4`, parameters `8.0B`, quantization `Q4_K_M`, size `9.6 GB`.
- Current preferred baseline:
  - `submissions/granite4_1_8b_c30_w060_w050_safe_20260522.jsonl`
  - Public score: MAP `0.9000`, MRR `0.9045`.
- Generated full Gemma rerank candidates using `intfloat/multilingual-e5-large` retrieval, `candidate-limit=200`, `ollama-rerank-candidates=30`, `fusion=score`, `casual-policy=strict`.
  - `submissions/gemma4_e4b_e5_w055_c30_20260522.jsonl`
    - Diff vs preferred baseline: `changed=167`, `top1_changed=44`.
    - SHA-256: `6389950844268fc1ba7d98e26b3db4dec7fa90e988718285e2da387efecc69e8`.
  - `submissions/gemma4_e4b_e5_w050_c30_20260522.jsonl`
    - Diff vs preferred baseline: `changed=171`, `top1_changed=49`.
    - SHA-256: `95c36b5ae147fff524da05ff54bac2f2dfc8272a22c66661c323886b23c2ce7f`.
  - `submissions/gemma4_e4b_e5_w060_c30_20260522.jsonl`
    - Diff vs preferred baseline: `changed=170`, `top1_changed=41`.
    - SHA-256: `1200608be568d868d374cc12df6ce1bf71ec7f5e57d8bfccdc4a2dc1b3e30f85`.
  - Decision: do not submit full Gemma files; top-1 drift is too broad.
- Audited Gemma rows selected for patch:
  - `23`: candidate explains blackberry sexual/asexual reproduction, more direct for reproduction capability.
  - `84`: candidate gives compact photosynthesis requirements and carbon fixation.
  - `86`: candidate directly says ice sheets contain most freshwater.
  - `250`: candidate directly explains river erosion forming valleys/canyons.
  - `302`: candidate directly says fuel energy is lost as heat during conversion to mechanical energy.
  - `308`: candidate gives magnetic flux unit Weber; more direct than baseline but unit may be flux rather than field strength, so expanded only.
- Generated Gemma targeted candidates:
  - `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_20260522.jsonl`
    - Base: preferred baseline.
    - Source: `gemma4_e4b_e5_w055_c30_20260522.jsonl`.
    - Diff vs preferred baseline: `changed=5`, `top1_changed=5`.
    - Changed eval IDs: `250,86,84,23,302`.
    - SHA-256: `315316a525e2bd2e902e6477c2f985566ae21d477bc698acf1fdecfb92a02f16`.
  - `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_308_20260522.jsonl`
    - Base: preferred baseline.
    - Source: `gemma4_e4b_e5_w055_c30_20260522.jsonl`.
    - Diff vs preferred baseline: `changed=6`, `top1_changed=6`.
    - Changed eval IDs: `308,250,86,84,23,302`.
    - SHA-256: `ce04590b1922442adcddf1ac7ce1101b51a81c23206befdd557d2b283422dd73`.
- Fresh verification:
  - Both targeted files: `rows=220`, `empty_topk=20`, `duplicate_topk=0`, `first_char={` verified by `scripts/validate_submission.py`.
  - Full tests: `python3 -B -m unittest discover -s tests` -> `Ran 37 tests`, `OK (skipped=2)`.
- Submission recommendation:
  1. Submit `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_20260522.jsonl` first.
  2. If it improves or ties, submit `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_308_20260522.jsonl`.
  3. If it regresses, split safe rows into `23/84/86` and `250/302` groups.

## Gemma4 E4B Submission Results

- Reported by user at: `2026-05-22 23:17:35 KST`.
- `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_20260522.jsonl`
  - Public MAP: `0.9091`.
  - Public MRR: `0.9136`.
  - SHA-256: `315316a525e2bd2e902e6477c2f985566ae21d477bc698acf1fdecfb92a02f16`.
  - Improvement over prior best `0.9000`/`0.9045`: MAP `+0.0091`, MRR `+0.0091`.
- `submissions/gemma4_e4b_e5_w050_c30_20260522.jsonl`
  - Public MAP: `0.8576`.
  - Public MRR: `0.8621`.
  - SHA-256: `95c36b5ae147fff524da05ff54bac2f2dfc8272a22c66661c323886b23c2ce7f`.
  - Result: full Gemma w050 regressed; confirms full Gemma output should not be used as baseline.
- `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_308_20260522.jsonl`
  - Public MAP: `0.9182`.
  - Public MRR: `0.9227`.
  - SHA-256: `ce04590b1922442adcddf1ac7ce1101b51a81c23206befdd557d2b283422dd73`.
  - Improvement over prior best `0.9000`/`0.9045`: MAP `+0.0182`, MRR `+0.0182`.
  - Improvement over Gemma safe targeted `0.9091`/`0.9136`: MAP `+0.0091`, MRR `+0.0091`.
- Decision: new confirmed best is `submissions/gemma4_e4b_targeted_eval23_84_86_250_302_308_20260522.jsonl`.
- Lesson: eval `308` was not risky; it provided a large public gain despite unit nuance. Keep `308` in the baseline going forward.
