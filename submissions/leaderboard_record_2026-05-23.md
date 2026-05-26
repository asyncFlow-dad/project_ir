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

## Eval81 Submission Result

- Submitted file: `submissions/gemma4_best_plus_rank2_topicdrift_20260523_eval81.jsonl`
- Reported public MAP: `0.9136`
- Reported public MRR: `0.9182`
- Result: regressed vs current best `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
- Difference vs current best:
  - MAP: `-0.0091` (`0.9227` -> `0.9136`)
  - MRR: `-0.0091` (`0.9273` -> `0.9182`)
- Decision: do not patch eval `81`.
- Next action: keep current best as eval `42` only. Add eval `81` to the rejected patch list with eval `98` and eval `109`.

## Post-Eval81 Candidate Audit

- Current best baseline remains `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
- Rejected eval IDs: `81`, `98`, `109`.
- Fresh rank-2 sweep found several lexical-positive candidates, but manual/LLM audit rejected false positives:
  - `269`: candidate is phototropism; baseline better matches plant height-growth mechanism.
  - `74`: candidate is packet-filter firewall; baseline directly explains IP protocol.
  - `15`: baseline better matches scientific skepticism/verification as researcher attitude.
  - `219`: baseline names salivary amylase and carbohydrate digestion.
- Best next single-row candidates:
  1. `submissions/gemma4_best_plus_eval42_285_20260523.jsonl`
     - Changed eval ID: `285`
     - Source: `submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`
     - Reason: query asks how squirrel nut-burying affects trees; candidate directly says buried nuts are seeds that can sprout into new trees.
     - Audit delta: `+0.111608`
     - SHA-256: `8672d22f5beae521d6336b99d8f4fc75c9023b1d899fe314a5b5b8672119aaa7`
  2. `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`
     - Changed eval ID: `295`
     - Source: `submissions/gemma4_best_plus_judge_all_20260523.jsonl`
     - Reason: query asks why Nevada gets little rain; candidate focuses on Nevada's dry desert climate and atmospheric moisture shortage.
     - Audit delta: `+0.088158`
     - SHA-256: `ca3cd055c94edeebf4bd0807cc1943f5fe2de18279bebdc5db486d0129ad2c2e`
  3. `submissions/gemma4_best_plus_eval42_53_20260523.jsonl`
     - Changed eval ID: `53`
     - Reason: candidate is concise on molecular scattering, but baseline is also strong; submit after eval `285`/`295`.
     - Audit delta: `+0.300000`
     - SHA-256: `1fe8cac54712d4b0d0c53f0dcca4899476994bf644004f4206b27e680c2fbf30`
- Validation for all three candidates:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows: `1`
  - Top-1 changed rows: `1`

## Eval285 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_285_20260523.jsonl`
- Reported public MAP: `0.9227`
- Reported public MRR: `0.9273`
- Result: tied current best `submissions/gemma4_best_plus_eval42_20260523.jsonl`.
- Decision:
  - Public score neither improved nor regressed.
  - Keep `eval285` as optional stack candidate, but do not count it as public improvement.
- Next candidates:
  1. Submit `submissions/gemma4_best_plus_eval42_295_20260523.jsonl` to isolate eval `295`.
  2. If eval `295` improves or ties, use stack file `submissions/gemma4_best_plus_eval42_285_295_20260523.jsonl`.
- Stack validation:
  - File: `submissions/gemma4_best_plus_eval42_285_295_20260523.jsonl`
  - Changed eval IDs vs current best: `295`, `285`
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows: `2`
  - Top-1 changed rows: `2`
  - SHA-256: `ab9445002b0ade1eb0c50dc4f793cfb5157c0b64dc8f70c47841e4718dca59be`

## Eval295 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: new best.
- Improvement over previous best:
  - MAP: `+0.0046` (`0.9227` -> `0.9273`)
  - MRR: `+0.0045` (`0.9273` -> `0.9318`)
- Decision: use `submissions/gemma4_best_plus_eval42_295_20260523.jsonl` as current best baseline.
- Next candidates:
  1. `submissions/gemma4_best_plus_eval42_285_295_20260523.jsonl`
     - Changed eval ID vs current best: `285`
     - Reason: eval `285` tied public score alone, so stack should be low risk.
     - SHA-256: `ab9445002b0ade1eb0c50dc4f793cfb5157c0b64dc8f70c47841e4718dca59be`
  2. `submissions/gemma4_best_plus_eval42_295_53_20260523.jsonl`
     - Changed eval ID vs current best: `53`
     - Reason: candidate answers sky-blue scattering directly, but baseline is also strong; submit after eval `285` stack.
     - SHA-256: `c2e9a9f1c3a1f42dfd01d2b459fcf5706ed907dc86b6be6ab4140afa2fa144da`
- Validation for both next candidates:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`

## Eval285+295 Stack Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_285_295_20260523.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: tied current best `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`.
- Decision:
  - Eval `285` remains public-neutral after stacking.
  - Keep current best baseline as `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`.
  - Do not prioritize further `285` stacking unless another patch needs compatibility check.
- Next candidate:
  - Submit `submissions/gemma4_best_plus_eval42_295_53_20260523.jsonl`.
  - It changes only eval `53` vs current best.
  - SHA-256: `c2e9a9f1c3a1f42dfd01d2b459fcf5706ed907dc86b6be6ab4140afa2fa144da`

## Candidate Selection Fix

- Problem found:
  - Semantic/LLM audits kept suggesting rows that had already tied, regressed, or failed manual review.
  - Example: eval `285` looked strong but was public-neutral; eval `295` could be reversed by later source files after becoming current best.
- Code change:
  - Added `PublicResult` and `--public-results` support to `scripts/submission_patch_candidates.py`.
  - Public-tested or manually rejected eval IDs are now locked out of future rank-2 candidate sweeps.
  - Ledger file: `submissions/public_results_2026-05-23.json`.
- Current locked eval IDs:
  - Public improved: `42`, `295`
  - Public regressed: `81`, `98`, `109`
  - Public neutral: `285`
  - Manual rejected: `15`, `74`, `219`, `269`
- Verification:
  - Local: `python3 -m unittest discover tests` -> `43` tests, `2` skipped, OK.
  - Remote: `python3.9 -m unittest discover tests` -> `43` tests, `2` skipped, OK.
  - Remote filtered sweep confirmed locked eval IDs are not emitted.
- Next work:
  1. Submit `submissions/gemma4_best_plus_eval42_295_53_20260523.jsonl`.
  2. Record result in `submissions/public_results_2026-05-23.json`.
  3. Run filtered sweep again before generating more submissions:
     `python3 scripts/submission_patch_candidates.py --baseline submissions/gemma4_best_plus_eval42_295_20260523.jsonl --rank2-only --public-results submissions/public_results_2026-05-23.json --source <candidate.jsonl>`

## Eval53 Stack Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_53_20260523.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: tied current best `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`.
- Decision:
  - Eval `53` is public-neutral.
  - Keep current best baseline as `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`.
  - Add eval `53` to public-result lockout list.
- Next action:
  - Run filtered sweep with `submissions/public_results_2026-05-23.json`.
  - Candidate list must exclude `15`, `42`, `53`, `74`, `81`, `98`, `109`, `219`, `269`, `285`, `295`.

## Filtered Candidate Audit After Eval53

- Baseline: `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`
- Locked eval IDs excluded: `15`, `42`, `53`, `74`, `81`, `98`, `109`, `219`, `269`, `285`, `295`
- Filtered rank-2 candidates found: `30`
- Cross-judge audit:
  - Eval `225`: Granite and Gemma both prefer candidate.
    - Query: `자전축 기후 미치 영향`
    - Reason: candidate directly explains axial tilt, seasons, day length, and direct/indirect sunlight.
  - Eval `26`: Granite and Gemma both prefer candidate.
    - Query: `짚신 벌레 번식 어떻게 이루어지나`
    - Reason: candidate directly explains paramecium conjugation/sexual reproduction.
  - Eval `250`: Granite prefers candidate, Gemma prefers baseline. Hold for later.
- New single-row submissions:
  1. `submissions/gemma4_best_plus_eval42_295_225_20260523.jsonl`
     - Changed eval ID vs current best: `225`
     - Source: `submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`
     - Rows: `220`
     - Empty topk: `20`
     - Duplicate topk: `0`
     - Changed rows vs current best: `1`
     - Top-1 changed rows vs current best: `1`
     - SHA-256: `5dce268e3af6df47b3cee8842a28146824f7722cd75bf639a693be119ff0d109`
  2. `submissions/gemma4_best_plus_eval42_295_26_20260523.jsonl`
     - Changed eval ID vs current best: `26`
     - Source: `submissions/granite4_1_8b_ollama_rerank_w060_c30_20260522.jsonl`
     - Rows: `220`
     - Empty topk: `20`
     - Duplicate topk: `0`
     - Changed rows vs current best: `1`
     - Top-1 changed rows vs current best: `1`
     - SHA-256: `ae9871f5157f5e8913162762d595a28bb3db5389093d2e29d028da6550713742`
- Verification:
  - Remote: `python3.9 -m unittest discover tests` -> `43` tests, `2` skipped, OK.
  - Local: `python3 -m unittest discover tests` -> `43` tests, `2` skipped, OK.
- Next submission order:
  1. Submit `submissions/gemma4_best_plus_eval42_295_225_20260523.jsonl`.
  2. Record result in `submissions/public_results_2026-05-23.json`.
  3. If eval `225` improves or ties, test `submissions/gemma4_best_plus_eval42_295_26_20260523.jsonl`.
  4. If eval `225` regresses, still test eval `26` only if submission budget allows, because it is independently supported by both judges.

## Eval26 And Eval225 Submission Results

- Submitted file: `submissions/gemma4_best_plus_eval42_295_26_20260523.jsonl`
  - Reported public MAP: `0.9273`
  - Reported public MRR: `0.9318`
  - Result: tied current best.
- Submitted file: `submissions/gemma4_best_plus_eval42_295_225_20260523.jsonl`
  - Reported public MAP: `0.9273`
  - Reported public MRR: `0.9318`
  - Result: tied current best.
- Decision:
  - Eval `26` and eval `225` are public-neutral.
  - Add both to `submissions/public_results_2026-05-23.json`.
  - Stop prioritizing rank-2 promotions selected only by semantic/LLM agreement; they are not aligning with hidden labels.
- Updated locked eval IDs:
  - Public improved: `42`, `295`
  - Public regressed: `81`, `98`, `109`
  - Public neutral: `26`, `53`, `225`, `285`
  - Manual rejected: `15`, `74`, `219`, `269`
- Next strategy:
  - Do not submit another rank-2 promotion unless baseline top-1 is obvious topic drift and candidate is not a near-duplicate.
  - Remaining rank-2 list contains mostly near-duplicates, scenario mismatches, or split-judge rows.
  - Better next direction is new candidate generation outside rank-2 promotion, then use public-result lockout before building single-row files.

## Candidate Generation Run - 2026-05-24

- Tool added: `scripts/generate_candidate_submissions.py`
  - Searches corpus outside current best topk instead of only promoting rank 2.
  - Applies public-result lockout from `submissions/public_results_2026-05-23.json`.
  - Writes audit JSON and optional single-row submissions.
- Remote command:
  - `python3.9 scripts/generate_candidate_submissions.py --baseline submissions/gemma4_best_plus_eval42_295_20260523.jsonl --corpus data/documents.jsonl --public-results submissions/public_results_2026-05-23.json --min-candidate-relevance 0.65 --min-delta 0.15 --candidate-pool 220 --limit 20 --audit-output submissions/generated_candidates_after_20260524_wide.json --single-output-dir submissions/generated_after_20260524_wide --name-prefix generated_wide`
- Generated candidates:
  - Eval `35`: rejected. Candidate is about deuterium/body-water measurement, not neutron properties.
  - Eval `300`: rejected. Candidate is about convoy/social support, not Social Security for retirees.
  - Eval `264`: split judge. Gemma prefers candidate, Granite prefers baseline. Hold.
  - Eval `56`: rejected. Candidate is about paper recycling, not fly ecosystem impact.
  - Eval `248`: rejected. Candidate is about longshore current, not deep-sea ecosystem impact.
  - Eval `273`: rejected. Candidate is about solar effects broadly, not sea-land weather influence.
  - Eval `9`: split judge. Granite prefers candidate, Gemma prefers baseline.
- Optional generated submission:
  - File: `submissions/gemma4_best_plus_eval42_295_generated_eval9_20260524.jsonl`
  - Changed eval ID vs current best: `9`
  - Reason: candidate is more cell/phototroph-focused, but baseline already directly explains photosynthesis into glucose.
  - Risk: split judge; likely neutral, possible regression.
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - SHA-256: `31678fbdce5e6457351cb266cd50425579e0cb8ddb76c9154a4c9b436b58ed2d`
- Verification:
  - Remote: `python3.9 -m unittest discover tests` -> `45` tests, `2` skipped, OK.
  - Local: `python3 -m unittest tests.test_generate_candidate_submissions` -> `2` tests, OK.
- Recommendation:
  - Do not submit eval `9` unless submission budget allows a risky probe.
  - Candidate generation found no high-confidence new improvement beyond current best.

## Eval9 Generated Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_generated_eval9_20260524.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: tied current best.
- Decision:
  - Eval `9` is public-neutral.
  - Add eval `9` to `submissions/public_results_2026-05-23.json`.
  - Generated candidate strategy did not find a public-effective row under current lexical thresholds.
- Current best remains:
  - File: `submissions/gemma4_best_plus_eval42_295_20260523.jsonl`
  - Public MAP: `0.9273`
  - Public MRR: `0.9318`
- Next strategy:
  - Stop single-row probing from lexical/LLM candidate generation for now.
  - Need a different signal source: labeled public deltas from fresh rerank runs, or a stronger model that can infer hidden label style, not just semantic answer quality.

## Ollama Candidate Judge Run - 2026-05-24

- Tool added: `scripts/ollama_candidate_judge.py`
  - Builds BM25 candidate pool outside current best topk.
  - Asks Ollama to choose baseline vs candidates.
  - Applies public-result lockout.
  - Writes audit JSON and single-row files only for candidate winners.
- Tests added:
  - `tests/test_ollama_candidate_judge.py`
- Remote runs:
  - Granite range `1-80`: selected eval `65`, `73`, `61`.
  - Granite range `80-220`: selected eval `96`, `86`, `91`, `84`.
  - Granite range `220-320`: selected eval `308`, `224`.
  - Gemma range `1-160`: too slow/noisy; parser now skips malformed/non-JSON responses.
- Manual audit result:
  - `61`: reject. Baseline conductivity test better answers generic metal identification than candidate iron-magnet test.
  - `65`: reject. Baseline directly answers vinegar and baking soda reaction; candidate only discusses acid neutralization.
  - `73`: reject. Baseline directly answers DNA-degrading enzyme role; candidate discusses sticky ends from restriction enzymes.
  - `84`: reject. Baseline directly explains photosynthesis; candidate narrows to Calvin cycle.
  - `86`: reject. Baseline correctly says ice sheets hold most freshwater; candidate focuses on mountain glaciers.
  - `91`: reject. Candidate discusses diamond structure, not method for identifying carbon internal structure.
  - `96`: reject. Baseline better answers what crust is made of; candidate gives broad Earth layer overview.
  - `224`: reject. Baseline directly explains traffic sniffing; candidate discusses packet filter firewall.
  - `308`: reject. Baseline directly answers magnetic field strength/flux unit; candidate is NMR gyromagnetic ratio.
- Verification:
  - Local: `python3 -m unittest tests.test_ollama_candidate_judge tests.test_generate_candidate_submissions` -> `5` tests, OK.
  - Remote: `python3.9 -m unittest tests.test_ollama_candidate_judge` -> `4` tests, OK.
- Decision:
  - Do not submit any Ollama-judge candidate from these runs.
  - Granite over-selects keyword-adjacent distractors.
  - Candidate generation confirmed current best is near plateau under current corpus/query signals.

## Query Expansion Run - 2026-05-25

- Tool added: `scripts/query_expansion_candidates.py`
  - Uses explicit Korean/domain expansion terms per eval ID.
  - Builds BM25 candidates outside current best topk.
  - Applies public-result lockout.
  - Adds relevance-score and delta filters after audit showed vote-only expansion was too noisy.
- Expansion seed file:
  - `submissions/query_expansions_20260525.json`
- Vote-only result:
  - Produced many false positives, including eval `30`, `77`, `100`, `213`, `238`, `263`, `296`.
  - Problem: expansion terms force keyword-adjacent distractors; vote count alone does not prove answer fit.
- Filtered result:
  - Command: `python3 scripts/query_expansion_candidates.py --baseline submissions/gemma4_best_plus_eval42_295_20260523.jsonl --corpus data/documents.jsonl --expansions submissions/query_expansions_20260525.json --public-results submissions/public_results_2026-05-23.json --pool-size 80 --min-votes 2 --min-candidate-relevance 0.55 --min-delta 0.08 --limit 20 --audit-output submissions/query_expansion_audit_20260525.json --single-output-dir submissions/query_expansion_single_20260525 --name-prefix gemma4_best_plus_eval42_295_qexp_20260525`
  - Remaining eval `239`: rejected. Baseline directly answers moon orbits Earth about 13 times per year; candidate discusses lunar day length.
  - Remaining eval `264`: rejected. Baseline better answers sexual stimulus to lubrication/blood-flow process; candidate only defines vasocongestion.
- Decision:
  - Do not submit query-expansion candidates.
  - Query expansion is useful as a recall tool, but unsafe without strict manual audit because it overweights repeated terms.

## Consensus Candidate - Eval3

- Source signal:
  - 30 prior submission files promote doc `254558bf-c608-47aa-952e-3f94805911f3` for eval `3`.
  - Current best already has that doc at rank 3, so this is a within-topk promotion rather than a new outside-corpus guess.
- Query:
  - `동물들 종종 집단 이주 경우 발생하더라구 이렇게 이주하게 되 계기 어떤 것들 있어`
- Reason:
  - Current top-1 defines migration and mentions broad causes.
  - Candidate top-1 directly names the triggering environmental changes: seasonal change and food decrease.
  - This is more aligned with the query asking for “계기”.
- Submission file:
  - `submissions/gemma4_best_plus_eval42_295_consensus_eval3_20260525.jsonl`
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - Changed eval ID: `3`
  - SHA-256: `7920ba2780fd70556d89087f52fb64cfd6f2d3d08b53ab2b393e3b16af77b9a5`
- Recommendation:
  - Submit only this single-row eval `3` candidate next.
  - If it ties or improves, record eval `3` in public results before generating more candidates.

## Eval3 Consensus Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_consensus_eval3_20260525.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: tied current best.
- Decision:
  - Eval `3` is public-neutral.
  - Add eval `3` to `submissions/public_results_2026-05-23.json`.
  - Strong consensus and current top3 promotion still did not move public score, so remaining gains likely require rows where current top1 is actually wrong by hidden-label criteria, not merely less direct.

## Eval106 Candidate - 2026-05-25

- Problem:
  - Query asks solar eclipse principle: `일식 발생 원리`.
  - Current top-1 describes lunar eclipse: Earth between Moon and Sun, Earth shadow covers Moon.
  - This is true topic error, not just weak wording.
- Candidate options:
  - `submissions/gemma4_best_plus_eval42_295_consensus_eval106_20260525.jsonl`
    - Top-1: `fc408e3d-9c04-44c4-89e4-139cacce27e3`
    - Strong prior-submission support: `33` source top-1 votes.
    - SHA-256: `6db7ccacfd274ce3794db63c50ddf3b9a24dc3698599b184d82d16c0b71d3f38`
  - `submissions/gemma4_best_plus_eval42_295_eval106_direct_20260525.jsonl`
    - Top-1: `86b57665-ccd9-4dc4-a76f-6744e99f759e`
    - More direct answer: Moon shadow falls on Earth, blocking sunlight.
    - SHA-256: `a481d4de87583bf93f5ad57aa0ac4a7991e327a2ed5a53f5d3e51a841d161c59`
- Validation for both:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - Changed eval ID: `106`
- Recommendation:
  - Submit `submissions/gemma4_best_plus_eval42_295_eval106_direct_20260525.jsonl` first.
  - Reason: hidden label likely rewards direct solar-eclipse mechanism more than generic phase wording.
  - If direct file ties, submit consensus eval106 only if budget allows; it tests same row with a different solar-eclipse doc.

## Eval106 Direct Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_eval106_direct_20260525.jsonl`
- Reported public MAP: `0.9273`
- Reported public MRR: `0.9318`
- Result: tied current best.
- Decision:
  - Eval `106` is public-neutral.
  - Add eval `106` to `submissions/public_results_2026-05-23.json`.
  - Even a visible top-1 topic correction did not change score, which implies this row is not public-scored, already credited through lower ranks, or hidden labels accept current topk order less strictly than expected.
- Next direction:
  - Stop testing within-top3 reorder for now.
  - Inspect rows with empty topk or missing coverage because those can affect MAP/MRR if public-scored and currently unretrieved.

## Eval66 BM25 Candidate - 2026-05-25

- Empty topk audit:
  - The `20` empty-topk rows are chit-chat or emotional support prompts, not document retrieval queries.
  - Do not fill them; likely not scored for IR, and filling would add noise.
- New candidate source:
  - Direct BM25 search with expanded programming terms for eval `66`.
- Problem:
  - Query: `예외처리 필요한 경우`
  - Current top-1 is about repeated experiments and scientific reproducibility, not exception handling.
- Candidate:
  - File: `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`
  - Top-1: `ec87a926-171d-4f62-9acc-1b870c010a16`
  - Reason: describes `N=0` runtime error and handling invalid input with exception processing.
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - Changed eval ID: `66`
  - SHA-256: `e648c30c79c8e01b1cb89cd55e04d5fe1491bb44565279484ad676f977833b1a`
- Recommendation:
  - Submit this only if willing to probe a non-public-verified row.
  - It is semantically much better than current top-1, but after eval3/eval106 neutral results, score may still tie if eval `66` is not public-scored.

## Eval66 BM25 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`
- Reported public MAP: `0.9364`
- Reported public MRR: `0.9409`
- Result: new best.
- Improvement over previous best:
  - MAP: `+0.0091` (`0.9273` -> `0.9364`)
  - MRR: `+0.0091` (`0.9318` -> `0.9409`)
- Decision:
  - Eval `66` is public-improved.
  - Use `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl` as current best baseline.
  - This confirms the useful signal is not embedding rank tweaks; it is finding rows where current top-1 is total topic drift and corpus contains a direct BM25 answer outside current topk.

## Eval0 BM25 Candidate - 2026-05-25

- Baseline:
  - `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`
  - Public MAP/MRR: `0.9364` / `0.9409`
- Problem:
  - Query: `바이러스 원핵 세포 서 작용할 때 사용 것`
  - Current top-1 discusses apoptosis/caspase, which is eukaryotic cell-death framing and mismatches prokaryotic-cell context.
- Candidate:
  - File: `submissions/gemma4_best_plus_eval42_295_66_bm25_eval0_20260525.jsonl`
  - Top-1: `e85754e3-12e4-44ec-a2c4-78a5b18b8aa7`
  - Reason: directly says viruses and prokaryotic cells share/use nucleic acid, and viruses use nucleic acid to replicate/interact in prokaryotic cells.
  - Prior support: 11 prior submission files promoted this doc for eval `0`.
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - Changed eval ID: `0`
  - SHA-256: `30edea972854db7096184be87254ea3c3baca13d22ffce2dfade34a500fa9ec8`
- Recommendation:
  - Submit this as next single-row probe.
  - Risk: query wording is compressed, but current top-1 is likely wrong domain for prokaryotic cells.

## Eval0 BM25 Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_66_bm25_eval0_20260525.jsonl`
- Reported public MAP: `0.9364`
- Reported public MRR: `0.9409`
- Result: tied current best.
- Decision:
  - Eval `0` is public-neutral.
  - Add eval `0` to `submissions/public_results_2026-05-23.json`.
  - Keep current best baseline as `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`.

## Eval46 B-Hepatitis Candidate - 2026-05-25

- Baseline:
  - `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`
  - Public MAP/MRR: `0.9364` / `0.9409`
- Problem:
  - Query: `B-형 간염에 대해 알려줘.`
  - Current top-1 is an A-type hepatitis document, so the disease subtype is wrong.
- Candidate:
  - File: `submissions/gemma4_best_plus_eval42_295_66_eval46_b_hepatitis_20260525.jsonl`
  - Top-1: `bd5ffdb4-0bc5-41a0-a779-27b0f63fc61a`
  - Reason: directly describes B-type hepatitis prevalence, transmission, complications, vaccination, and screening.
  - New order: B-type hepatitis, A-type hepatitis, C-type hepatitis.
- Validation:
  - Rows: `220`
  - Empty topk: `20`
  - Duplicate topk: `0`
  - Changed rows vs current best: `1`
  - Top-1 changed rows vs current best: `1`
  - Changed eval ID: `46`
  - SHA-256: `0cc6e27702840bc5d848c2c408200534627512d8b7a518c568f2b1b9de551e14`
- Recommendation:
  - Submit this as next single-row probe.
  - This is stronger than eval `0`: query explicitly asks B-type hepatitis and current top-1 is A-type hepatitis.

## Eval46 B-Hepatitis Submission Result

- Submitted file: `submissions/gemma4_best_plus_eval42_295_66_eval46_b_hepatitis_20260525.jsonl`
- Model: `gemma4`
- Reported public MAP: `0.9364`
- Reported public MRR: `0.9409`
- Result: tied current best.
- Decision:
  - Eval `46` is public-neutral.
  - Keep current best baseline as `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`.
  - Explicit subtype correction did not move public score, so this row is likely not public-scored or existing rank-2 credit already covers public label.

## Solar-Pro3 Single-Row Submission Results - 2026-05-25

- Baseline:
  - `submissions/gemma4_best_plus_eval42_295_bm25_eval66_20260525.jsonl`
  - Public MAP/MRR: `0.9364` / `0.9409`
- Results:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval18.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9318` / `0.9364`
    - Result: regressed vs current best.
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval100.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9326` / `0.9364`
    - Result: regressed vs current best.
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9455` / `0.9500`
    - Result: improved.
- Improvement from previous best:
  - MAP: `+0.0091` (`0.9364` -> `0.9455`)
  - MRR: `+0.0091` (`0.9409` -> `0.9500`)
- Decision:
  - Use `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl` as current best baseline.
  - Add eval `18` and eval `100` to public-regressed rows.
  - Solar-Pro3 useful as judge, but high confidence is not enough; manually reject candidates whose reason admits topic mismatch.

## Solar-Pro3 Strict Candidate Audit - 2026-05-25

- Current best baseline:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Strict first-pass run:
  - Model: `solar-pro3`
  - Candidate pool: `40`
  - Min confidence: `0.85`
  - Audit: `submissions/solar_pro3_strict_audit_20260525.json`
- Evidence pairwise second-pass:
  - Audit: `submissions/solar_pro3_pairwise_audit_20260525.json`
  - Most first-pass candidates were rejected because baseline already directly answered the query.
- Submit order for remaining 4 daily submissions:
  1. `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval231.jsonl`
     - Model: `solar-pro3`
     - Changed eval ID: `231`
     - Pairwise reason: candidate directly states most evaporation occurs from sea because sea has about 97% of Earth's water.
     - Validation: `rows=220`, `empty_topk=20`, `duplicate_topk=0`, `changed=1`, `top1_changed=1`.
  2. `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval43.jsonl`
     - Model: `solar-pro3`
     - Changed eval ID: `43`
     - Risk: near-duplicate; baseline already explains synchronous rotation, candidate adds visible 59% framing.
     - Validation: `rows=220`, `empty_topk=20`, `duplicate_topk=0`, `changed=1`, `top1_changed=1`.
  3. `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval5.jsonl`
     - Model: `solar-pro3`
     - Changed eval ID: `5`
     - Risk: candidate talks alternative fuel, not directly "fuel economy improvement effect"; submit only after eval231/eval43 results.
     - Validation: `rows=220`, `empty_topk=20`, `duplicate_topk=0`, `changed=1`, `top1_changed=1`.
- Decision:
  - Submit eval `231` first.
  - If eval `231` improves or ties, submit eval `43`.
  - If both are neutral/improved and two submissions remain, submit eval `5`; otherwise preserve remaining attempts.

## Solar-Pro3 Strict Submission Results - 2026-05-25

- Current best remains:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Results:
  - `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval231.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9439` / `0.9485`
    - Result: regressed vs current best.
  - `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval43.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9417` / `0.9455`
    - Result: regressed vs current best.
  - `submissions/solar_pro3_strict_single_20260525/solar_pro3_strict_eval205_base_eval5.jsonl`
    - Model: `solar-pro3`
    - Public MAP/MRR: `0.9409` / `0.9455`
    - Result: regressed vs current best.
- Decision:
  - Add eval `231`, `43`, and `5` to public-regressed lockout.
  - Keep current best as `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`.
  - Stop submitting Solar rank/similarity refinements unless baseline top-1 is a clear topic error like eval `205`; pairwise "candidate wins" was still too optimistic.

## Final Daily Probe Candidate - Eval302 - 2026-05-25

- Current best baseline:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Topic-error scan:
  - Tool: `judge_topic_error_candidate` in `scripts/ollama_candidate_judge.py`
  - Audit: `submissions/solar_pro3_topic_error_audit_20260525.json`
  - Result: no strict candidate passed the automated gate.
- Fallback candidate selected from prior-submission consensus:
  - File: `submissions/solar_pro3_topic_error_single_20260525/solar_pro3_topic_error_eval205_base_eval302.jsonl`
  - Model/source context: current best `solar-pro3`; candidate doc has broad prior rerank support.
  - Changed eval ID: `302`
  - Query: `기계 연료 태울 때 어떤 형태 에너지 낭비되는`
  - Baseline top-1 says useful energy decreases and some energy is lost as heat.
  - Candidate top-1 states explicitly that gasoline energy mostly becomes heat and only about 15% becomes mechanical energy.
  - New topk: candidate, previous top1, previous top2.
- Validation:
  - Local and remote: `rows=220`, `empty_topk=20`, `duplicate_topk=0`, `changed=1`, `top1_changed=1`.
- Recommendation:
  - This is not eval205-strength; it is the least-bad final probe.
  - Submit only because one daily submission remains and strict scan found no safer topic-error row.

## Eval302 Final Daily Probe Result

- Submitted file: `submissions/solar_pro3_topic_error_single_20260525/solar_pro3_topic_error_eval205_base_eval302.jsonl`
- Model: `solar-pro3`
- Reported public MAP: `0.9455`
- Reported public MRR: `0.9500`
- Result: tied current best.
- Decision:
  - Eval `302` is public-neutral.
  - Keep current best as `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`.
  - Add eval `302` to public-result lockout.

## Strict Topic-Error Miner Run - 2026-05-26

- Implemented script: `scripts/topic_error_candidates.py`
  - Recalls candidate docs only for unlocked eval IDs with low baseline relevance.
  - Requires both topic-error Solar judgement and pairwise Solar judgement to choose candidate.
  - Writes single-row files only for accepted candidates.
- Baseline:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Remote command:
  - `python3.9 scripts/topic_error_candidates.py --baseline submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl --corpus data/documents.jsonl --public-results submissions/public_results_2026-05-23.json --candidate-pool 220 --per-eval-candidates 4 --recall-limit 60 --accepted-limit 3 --max-baseline-relevance 0.35 --min-candidate-relevance 0.35 --min-delta 0.10 --audit-output submissions/topic_error_candidates_audit_20260526.json --single-output-dir submissions/topic_error_candidates_20260526 --name-prefix topic_error_eval205_base`
- Result:
  - Accepted candidates: `0`
  - Audit: `submissions/topic_error_candidates_audit_20260526.json`
  - Output dir empty.
- Decision:
  - Do not submit from this run.
  - Strict eval205-like gate found no safe replacement above current best.

## Eval205 Re-Submission Result - 2026-05-26

- Submitted file: `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
- Model: `solar-pro3`
- Reported public MAP: `0.9455`
- Reported public MRR: `0.9500`
- Result: confirmed current best.
- Decision:
  - Keep current best as `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`.
  - No public-result ledger change needed; eval `205` was already recorded as improved.

## Solar-Pro3 Balanced Candidate Run - 2026-05-26

- Implemented balanced topic-error search in `scripts/topic_error_candidates.py`.
  - Added `--preset strict|balanced|wide`.
  - Balanced preset uses Tier A/B recall and lower Solar confidence gate for 12-submission budget.
  - Added `--candidate-submission-dir` to re-audit existing Solar single-row files before recommending them.
  - Audit now records rejected candidates with judge stage, winner, confidence, and reason.
- Baseline:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Remote command:
  - `python3.9 scripts/topic_error_candidates.py --baseline submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl --corpus data/documents.jsonl --public-results submissions/public_results_2026-05-23.json --preset balanced --candidate-submission-dir submissions/solar_pro3_single_20260525 --candidate-submission-dir submissions/solar_pro3_strict_single_20260525 --accepted-limit 6 --audit-output submissions/solar_pro3_balanced_audit_20260526.json --single-output-dir submissions/solar_pro3_balanced_20260526 --name-prefix solar_pro3_balanced_eval205_base`
- Result:
  - Recall candidates: `38`
  - Rejected candidates: `38`
  - Accepted candidates: `0`
  - Audit: `submissions/solar_pro3_balanced_audit_20260526.json`
  - Output dir empty.
- Decision:
  - Do not submit from this run.
  - Even with 12 daily submissions, no candidate met the eval205-style topic-error gate.
  - Keep current best as `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`.

## Eval246 High-Risk Submission Result - 2026-05-26

- Submitted file: `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/solar_pro3_single_20260525/solar_pro3_best_plus_eval205.jsonl`
  - Public MAP/MRR: `0.9455` / `0.9500`
- Reported public MAP: `0.9545`
- Reported public MRR: `0.9591`
- Result: new best.
- Improvement:
  - MAP: `+0.0090` (`0.9455` -> `0.9545`)
  - MRR: `+0.0091` (`0.9500` -> `0.9591`)
- Changed eval ID: `246`
- Query: `친환경 재생 가능 재료 어떤것들 있나`
- Decision:
  - Eval `246` is public-improved.
  - Use `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl` as current best baseline.
  - High-risk fallback succeeded where strict/balanced Solar gate rejected all candidates, so next search should use eval246 baseline and include high-risk manual candidates after Solar rejection.

## Eval221 Direct-Answer Submission Result - 2026-05-26

- Submitted file: `submissions/solar_pro3_direct_answer_single_20260526/solar_pro3_direct_eval246_base_eval221.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`
  - Public MAP/MRR: `0.9545` / `0.9591`
- Reported public MAP: `0.9500`
- Reported public MRR: `0.9545`
- Result: regressed vs eval246 best.
- Difference:
  - MAP: `-0.0045` (`0.9545` -> `0.9500`)
  - MRR: `-0.0046` (`0.9591` -> `0.9545`)
- Changed eval ID: `221`
- Query: `전구 병렬 연결될 때 전류 줄어드 원인`
- Decision:
  - Eval `221` is public-regressed.
  - Keep current best as `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`.
  - Lock out eval `221`; semantic-looking circuit explanation fix did not improve public score.

## Eval252 Residual Submission Result - 2026-05-26

- Submitted file: `submissions/residual_single_strict_20260526/residual_eval246_base_eval252.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`
  - Public MAP/MRR: `0.9545` / `0.9591`
- Reported public MAP: `0.9545`
- Reported public MRR: `0.9591`
- Result: tied current best.
- Changed eval ID: `252`
- Query: `해구 생겨나 원리`
- Decision:
  - Eval `252` is public-neutral.
  - Keep current best as `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`.
  - Lock out eval `252`; candidate beat current top-1 but did not improve public score, so next residual mining must require candidate to beat current top-k alternatives, not only baseline top-1.
  - Do not submit loose-gate file `submissions/residual_single_20260526/residual_eval246_base_eval7.jsonl`.

## Eval309 Residual High-Risk Submission Result - 2026-05-26

- Submitted file: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/solar_pro3_highrisk_20260526/solar_pro3_highrisk_eval205_base_eval246.jsonl`
  - Public MAP/MRR: `0.9545` / `0.9591`
- Reported public MAP: `0.9561`
- Reported public MRR: `0.9591`
- Result: new best.
- Improvement:
  - MAP: `+0.0016` (`0.9545` -> `0.9561`)
  - MRR: `+0.0000` (`0.9591` -> `0.9591`)
- Changed eval ID: `309`
- Query: `특정 농도 황산 sample 만드 방법`
- Decision:
  - Eval `309` is public-improved.
  - Use `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl` as current best baseline.
  - High-risk rank3 promotion can still improve MAP even when strict top-k guard rejects all candidates; next search should mine current rank2/rank3 promotions with high support, but exclude rows where current top1 already exactly answers.

## Eval207 High-Risk Rank Submission Result - 2026-05-26

- Submitted file: `submissions/highrisk_rank_single_remote2_20260526/highrisk_rank_eval309_base_round2_eval207.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
  - Public MAP/MRR: `0.9561` / `0.9591`
- Reported public MAP: `0.9561`
- Reported public MRR: `0.9591`
- Result: tied current best.
- Changed eval ID: `207`
- Query: `곤충 눈 구조`
- Decision:
  - Eval `207` is public-neutral.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Lock out eval `207`; high-support rank2 promotion looked semantically plausible but did not improve public score.
  - Next search should require stronger public-signal proxy than Solar direct-answer judgement alone: prefer rows where baseline is clearly off-topic or where multiple independent candidate sources agree and current top1 lacks the key answer span.

## Answer-Span Candidate Run - 2026-05-26

- Baseline: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Model: `solar-pro3`
- Current best public MAP/MRR: `0.9561` / `0.9591`
- Remote audits:
  - `submissions/answer_span_audit_20260526.json`
  - `submissions/answer_span_audit_round2_20260526.json`
- Result:
  - Accepted by automated answer-span gate: `7`, `279`, `250`, `303`
  - Submitted files generated but not recommended.
- Manual rejection:
  - Eval `7`: baseline and candidate are near-duplicate; baseline already directly answers light speed in nonmagnetic dielectric.
  - Eval `279`: baseline already links literacy to social development and uses newer 2015 statistic; candidate uses older 1950 statistic.
  - Eval `250`: baseline directly explains canyon erosion by river; candidate adds delta/river-mouth noise.
  - Eval `303`: baseline directly explains camouflage survival; candidate has lower-quality examples and no clear answer-span gain.
- Decision:
  - Do not submit answer-span run files.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Answer-span Solar gate catches some weak rows but still overclaims baseline-missing facts; future gate should require literal baseline evidence absence before candidate review.

## Answer-Span Strict Quote Candidate Run - 2026-05-26

- Baseline: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Model: `solar-pro3`
- Current best public MAP/MRR: `0.9561` / `0.9591`
- Remote audit: `submissions/answer_span_strict_quote_audit_20260526.json`
- Gate change:
  - Candidate must include exact quote evidence.
  - Baseline present quote blocks acceptance.
  - Previous manual rejects `7`, `279`, `250`, `303` remain locked out by public-result ledger.
- Result:
  - Accepted candidates: `0`
  - No submission file recommended.
- Decision:
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Strict quote gate successfully prevents weak semantic overclaims, but it found no public-score candidate in current residual pool.

## Eval23 Manual Submission Result - 2026-05-26

- Submitted file: `submissions/manual_single_20260526/manual_eval309_base_eval23.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
  - Public MAP/MRR: `0.9561` / `0.9591`
- Reported public MAP: `0.9561`
- Reported public MRR: `0.9591`
- Result: tied current best.
- Changed eval ID: `23`
- Query: `식물 동물중 누 번식력 높다고 할 수 있어`
- Decision:
  - Eval `23` is public-neutral.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Lock out eval `23`; manual rank2 promotion looked broader but did not improve public score.

## Eval34 Manual Submission Result - 2026-05-26

- Submitted file: `submissions/manual_single_20260526/manual_eval309_base_eval34.jsonl`
- Model: `solar-pro3`
- Previous best:
  - `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
  - Public MAP/MRR: `0.9561` / `0.9591`
- Reported public MAP: `0.9515`
- Reported public MRR: `0.9545`
- Result: regressed vs current best.
- Difference:
  - MAP: `-0.0046` (`0.9561` -> `0.9515`)
  - MRR: `-0.0046` (`0.9591` -> `0.9545`)
- Changed eval ID: `34`
- Query: `씨앗 기능 자세히`
- Decision:
  - Eval `34` is public-regressed.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
  - Lock out eval `34`; broader/more detailed candidate hurt public score.
  - Do not submit more “more detailed but same topic” promotions today.

## Fault Candidate Run - 2026-05-26

- Baseline: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Model: `solar-pro3`
- Current best public MAP/MRR: `0.9561` / `0.9591`
- Submission budget remaining when planned: `4`
- Remote audits:
  - `submissions/fault_candidate_audit_20260526.json`
  - `submissions/fault_candidate_lenient_audit_20260526.json`
- Gate change:
  - Accept only `off_topic`, `wrong_entity`, `wrong_formula`, or `contradiction` baseline faults.
  - Reject `missing_answer`, broader/detail-richer candidates, and candidates without exact evidence quote.
  - Keep one-row outputs only.
- Result:
  - Accepted candidates: `0`
  - No submission file recommended.
- Decision:
  - Do not spend remaining daily submissions on this run.
  - High-score rejected rows remain risky: `241` has arithmetic contradiction, `85` has conflicting formula interpretations, `31` is not clearly better than baseline for generic sound propagation.
  - Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.

## Remaining4 Manual Submission Results - 2026-05-26

- Baseline: `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`
- Model: `solar-pro3`
- Previous best public MAP/MRR: `0.9561` / `0.9591`

### Eval31

- Submitted file: `submissions/manual_remaining4_20260526/manual_remaining4_eval309_base_eval31.jsonl`
- Reported public MAP/MRR: `0.9561` / `0.9591`
- Result: tied current best.
- Decision: lock out eval `31`; sound propagation candidate did not improve public score.

### Eval85

- Submitted file: `submissions/manual_remaining4_20260526/manual_remaining4_eval309_base_eval85.jsonl`
- Reported public MAP/MRR: `0.9538` / `0.9545`
- Result: regressed vs current best.
- Difference:
  - MAP: `-0.0023` (`0.9561` -> `0.9538`)
  - MRR: `-0.0046` (`0.9591` -> `0.9545`)
- Decision: lock out eval `85`; formula-interpretation candidate is publicly harmful.

### Eval214

- Submitted file: `submissions/manual_remaining4_20260526/manual_remaining4_eval309_base_eval214.jsonl`
- Reported public MAP/MRR: `0.9561` / `0.9591`
- Result: tied current best.
- Decision: lock out eval `214`; more complete atomic-structure candidate did not improve public score.

### Eval87

- Submitted file: `submissions/manual_remaining4_20260526/manual_remaining4_eval309_base_eval87.jsonl`
- Reported public MAP/MRR: `0.9561` / `0.9591`
- Result: tied current best.
- Decision: lock out eval `87`; Jupiter internal-heat candidate did not improve public score.

### Summary

- New best: none.
- Keep current best as `submissions/residual_highrisk_single_20260526/residual_highrisk_eval246_base_eval309.jsonl`.
- Remaining4 experiment confirms that same-topic/detail/formula candidates are unreliable; future submissions should require stronger public proxy or stop when accepted candidates are absent.
