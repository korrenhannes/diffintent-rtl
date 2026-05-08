# DiffIntent-RTL Final Report

**Course:** Deep Learning Project  
**Project:** DiffIntent-RTL  
**Team members:** `[fill in]`, `[fill in]`

## 1. Motivation and Problem Definition

This project studies whether a neural model can understand *why* an RTL change was made and whether the change appears *complete* when given a real SystemVerilog diff from OpenTitan history.

We define two supervised tasks over a single file-level change example:

1. **Change intent classification**
   - `bug_fix`
   - `feature_or_behavior_change`
   - `refactor_cleanup`
   - `configuration_timing`
2. **Implementation-hole detection**
   - `complete`
   - `synthetic_hole`

The motivation is practical. Hardware repositories contain many small RTL changes involving resets, guards, parameters, state machines, and assertions. A useful model should be able to distinguish semantic categories of changes and also recognize suspicious diffs that look incomplete, such as a removed guard, a missing reset assignment, or a dropped added line.

The central research question is whether an explicitly **diff-aware hierarchical model** that knows which lines were added, deleted, or kept as context provides measurable value over simpler bag-of-words and flat sequence baselines.

## 2. Related Work

The project is inspired by prior work on learning from code changes rather than only from final source snapshots.

- **CC2Vec** learns distributed representations of code changes from added and removed code. Its main relevance here is the idea that the *change itself* should be the primary learning object.
- **PatchNet** models patches hierarchically. This directly motivates our file -> line -> token structure for unified diffs.
- **DeepJIT** predicts defect-prone commits from code changes and commit metadata. Our hole-detection task is similar in spirit, although we use controlled synthetic holes instead of post-hoc defect labels.
- **CodeReviewer** treats diffs as structured inputs for downstream tasks. This supports using diff-aware encoders rather than plain file-level text classification.

Our adaptation is specific to RTL. Instead of natural-language or general software patches, we focus on SystemVerilog unified diffs, preserve line types such as `ADD` and `DEL`, and use a multi-task setup that jointly optimizes intent prediction and hole detection.

## 3. Data Description

### 3.1 Source and Mining Policy

All examples are mined from the OpenTitan repository:

```bash
git clone https://github.com/lowRISC/opentitan.git external/opentitan
```

We kept changes touching `hw/**/rtl/*.sv` and excluded paths containing:

```text
/dv/ /test/ /tests/ /vendor/ /third_party/ /generated/ /build/ /out/
```

We also filtered commits to avoid merge commits, pure revert commits, empty commit messages, and overly large diffs. The mining pipeline prefers one changed RTL file per commit and falls back to at most three RTL files, yielding one file-level example per changed file.

### 3.2 Weak Intent Labels

Intent labels are inferred from commit-message keyword groups:

- `bug_fix`: `fix`, `bug`, `wrong`, `regression`, `incorrect`, `issue`, `repair`, `fail`, `failure`
- `feature_or_behavior_change`: `add`, `implement`, `support`, `enable`, `introduce`, `new`, `feature`
- `refactor_cleanup`: `refactor`, `cleanup`, `rename`, `move`, `style`, `tidy`, `simplify`, `remove unused`
- `configuration_timing`: `clock`, `reset`, `timing`, `param`, `parameter`, `width`, `config`, `fsm`, `latency`

Ambiguous examples are discarded if multiple label groups match strongly. This step removed a large fraction of mined candidates, which is important for interpreting the final results.

### 3.3 Synthetic Hole Construction

Each accepted real example is labeled `complete`. A paired `synthetic_hole` example is then generated using controlled mutations inside the changed region only:

1. remove an added guard/assertion line
2. remove a reset/default assignment line
3. drop one added line
4. drop one added hunk from a multi-hunk diff
5. flip comparison operators
6. flip logical operators
7. flip simple binary constants

Pairs are preserved during chronological splitting so the original example and its mutation never cross train, validation, and test boundaries.

### 3.4 Final Full Dataset

The executed full pipeline produced:

- `5903` raw file-level RTL candidates in [../data/raw/opentitan_rtl_commits.jsonl](../data/raw/opentitan_rtl_commits.jsonl)
- `2843` weak-labeled real examples in [../data/processed/opentitan_real_examples.jsonl](../data/processed/opentitan_real_examples.jsonl)
- `5500` total examples after synthetic hole generation in [../data/processed/opentitan_with_holes.jsonl](../data/processed/opentitan_with_holes.jsonl)
- `2843` pair groups for chronological splitting

Weak-label filtering discarded:

- `2713` examples with no keyword match
- `347` ambiguous examples with multiple maximal label groups

The final split sizes from [../outputs/metrics/dataset_stats.json](../outputs/metrics/dataset_stats.json) are:

- train: `3873` examples
- validation: `830` examples
- test: `797` examples

The final dataset is moderately imbalanced on intent but nearly balanced on hole labels:

- `feature_or_behavior_change`: `2240` (`40.7%`)
- `bug_fix`: `1861` (`33.8%`)
- `configuration_timing`: `934` (`17.0%`)
- `refactor_cleanup`: `465` (`8.5%`)
- `complete`: `2843` (`51.7%`)
- `synthetic_hole`: `2657` (`48.3%`)

This class skew already suggests that `refactor_cleanup` will be a difficult class.

### 3.5 Preprocessing

Unified diffs are normalized into typed lines:

```text
<FILE> path
<HUNK> @@ ...
<CTX> ...
<DEL> ...
<ADD> ...
```

The tokenizer is SystemVerilog-aware and preserves identifiers, keywords, width literals, operators, punctuation, and macros. Vocabulary is built from the training set only. The full run uses these limits:

- `max_lines_per_diff = 128`
- `max_tokens_per_line = 64`
- `max_total_tokens_flat = 2048`

When truncation is necessary, the pipeline keeps added/deleted lines first, then nearby context.

## 4. Models and Training Setup

### 4.1 Models

We compare four main models.

| Model | Main idea | Key executed settings |
| --- | --- | --- |
| `full_tfidf_lr` | Separate TF-IDF + logistic regression classifiers for intent and hole | word n-grams `1-2`, char n-grams `3-5`, `50k` max features, `class_weight=balanced` |
| `full_mlp` | Embedding -> mean pooling -> 2-layer MLP -> two heads | embedding `128`, hidden `256`, dropout `0.2`, batch `128`, lr `1e-3`, epochs `6` |
| `full_bigru` | Embedding -> BiGRU -> attention pooling -> two heads | embedding `128`, hidden `128`, 1 layer, dropout `0.2`, batch `128`, lr `1e-3`, epochs `6` |
| `full_hierarchical_transformer` | token embedding + line encoder + line-type embedding + line-level Transformer | token emb `128`, line-type emb `32`, line hidden `128`, 2 layers, 4 heads, FF `512`, dropout `0.2`, batch `32`, lr `5e-4`, epochs `6` |

The proposed hierarchical model uses:

1. token embeddings with token-position embeddings
2. a bidirectional GRU line encoder over tokens inside each diff line
3. optional line-type embeddings for `ADD`, `DEL`, `CTX`, `HUNK`, `FILE`, `PAD`
4. a 2-layer Transformer encoder over line representations
5. attention pooling over encoded lines
6. two output heads sharing the same representation

### 4.2 Optimization

All neural models are implemented in PyTorch and optimized with **AdamW** by gradient-based learning. Each task head uses **cross-entropy loss**. In multitask mode the loss is:

```text
L = L_intent + 1.0 * L_hole
```

For single-task ablations, only the corresponding loss is optimized. Validation checkpoint selection uses:

- `intent macro-F1` for `intent_only`
- `hole F1` for `hole_only`
- `intent macro-F1 + hole F1` for multitask runs

Early stopping patience in the executed full run is `2` epochs. This shorter budget is the *actual executed configuration* used to complete the full end-to-end sweep on the available Apple MPS machine; all exact run configs are saved under `outputs/checkpoints/*_config.yaml`.

### 4.3 Ablations

The final full run includes:

- `full_hierarchical_no_line_type` across seeds `13`, `42`, `123`
- `full_hierarchical_no_context` on reference seed `13`
- `full_hierarchical_no_multitask_intent` on reference seed `13`
- `full_hierarchical_no_multitask_hole` on reference seed `13`
- `full_tfidf_message_only` on reference seed `13`

The primary scientific ablation is `no_line_type`, because it directly tests the claimed architectural contribution.

## 5. Experiments

### 5.1 Evaluation Protocol

The repository uses chronological train/validation/test splits with pair preservation. Test data is never used for model selection. Metrics are:

- **Intent:** accuracy, macro-F1, weighted-F1, per-class precision/recall/F1, confusion matrix
- **Hole detection:** accuracy, precision, recall, F1, AUROC, PR-AUC, confusion matrix

Main runs use seeds `13`, `42`, and `123`. Auxiliary ablations were kept at one reference seed to keep the full sweep finishable end to end on local hardware.

### 5.2 Reproducibility

The end-to-end run is driven by:

```bash
bash scripts/run_full_experiment.sh
```

Unit tests were also executed successfully:

```bash
python3 -m pytest tests
```

Saved artifacts include metrics, predictions, checkpoints, figures, and logs under `outputs/`. The relevant final tables are [../outputs/metrics/main_results.csv](../outputs/metrics/main_results.csv) and [../outputs/metrics/ablation_results.csv](../outputs/metrics/ablation_results.csv).

## 6. Results

### 6.1 Main Results

The following table is copied from [../outputs/metrics/main_results.csv](../outputs/metrics/main_results.csv).

| setting_name | num_runs | intent_accuracy_mean | intent_macro_f1_mean | intent_macro_f1_std | hole_accuracy_mean | hole_f1_mean | hole_f1_std | hole_auroc_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_bigru | 3 | 0.3998327059807612 | 0.30228705169172704 | 0.028341893057717824 | 0.5821831869510665 | 0.4204336776177931 | 0.0677365845589627 | 0.5942169335611959 |
| full_hierarchical_transformer | 3 | 0.4065244667503137 | 0.300679108210622 | 0.022897752394201207 | 0.6725219573400251 | 0.602924109721289 | 0.022635862693944832 | 0.7351942106040467 |
| full_mlp | 3 | 0.40485152655792556 | 0.2960697769628042 | 0.05502621351111561 | 0.5529067335842744 | 0.32928079585018266 | 0.1418530272467224 | 0.5488237652172079 |
| full_tfidf_lr | 3 | 0.5131744040150564 | 0.41973380330967003 | 0.0 | 0.5734002509410289 | 0.543010752688172 | 0.0 | 0.6122982467244762 |

### 6.2 Ablation Results

The following table is copied from [../outputs/metrics/ablation_results.csv](../outputs/metrics/ablation_results.csv).

| setting_name | num_runs | intent_accuracy_mean | intent_macro_f1_mean | intent_macro_f1_std | hole_accuracy_mean | hole_f1_mean | hole_f1_std | hole_auroc_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_hierarchical_no_context | 1 | 0.47051442910915936 | 0.2676813961225539 | 0.0 | 0.6599749058971142 | 0.5937031484257871 | 0.0 | 0.7125957339072093 |
| full_hierarchical_no_line_type | 3 | 0.4094521120869929 | 0.30279830178943146 | 0.031031430161490438 | 0.589293182768716 | 0.47243304633690975 | 0.004770552986079231 | 0.6293583982108573 |
| full_hierarchical_no_multitask_hole | 1 | 0.29109159347553326 | 0.18127922210388553 | 0.0 | 0.6587202007528231 | 0.6353887399463807 | 0.0 | 0.7162795113614786 |
| full_hierarchical_no_multitask_intent | 1 | 0.45294855708908405 | 0.3192835120979899 | 0.0 | 0.4742785445420326 | 0.5797392176529589 | 0.0 | 0.49469903158427747 |
| full_tfidf_message_only | 1 | 0.9849435382685069 | 0.9854909069297515 | 0.0 | 0.5294855708908407 | 0.43609022556390975 | 0.0 | 0.5450250015823785 |

### 6.3 Immediate Takeaways

Three conclusions are already clear from the final tables.

1. **Intent classification is won by TF-IDF, not by the neural models.**  
   `full_tfidf_lr` reaches the best intent macro-F1 (`0.4197`), comfortably above the neural models (`0.2961` to `0.3023`).

2. **Hole detection is won by the hierarchical Transformer.**  
   `full_hierarchical_transformer` reaches the best hole F1 (`0.6029`) and the best hole AUROC (`0.7352`).

3. **Line-type embeddings matter specifically for hole detection.**  
   The main ablation `full_hierarchical_no_line_type` reduces hole F1 from `0.6029` to `0.4724` and AUROC from `0.7352` to `0.6294`, while intent macro-F1 stays essentially unchanged (`0.3007` vs. `0.3028`).

## 7. Analysis

Because the final tables average across seeds while confusion matrices and predictions are saved per run, the detailed analysis below uses **seed 13** as a representative checkpoint. For the main hierarchical model, seed 13 is close to the 3-seed mean: intent macro-F1 `0.2965` vs. mean `0.3007`, hole F1 `0.6208` vs. mean `0.6029`, and hole AUROC `0.7441` vs. mean `0.7352`.

Representative artifacts inspected for this section:

- [full_tfidf_lr_seed13_intent_confusion_matrix.png](../outputs/figures/full_tfidf_lr_seed13_intent_confusion_matrix.png)
- [full_tfidf_lr_seed13_hole_confusion_matrix.png](../outputs/figures/full_tfidf_lr_seed13_hole_confusion_matrix.png)
- [full_hierarchical_transformer_seed13_intent_confusion_matrix.png](../outputs/figures/full_hierarchical_transformer_seed13_intent_confusion_matrix.png)
- [full_hierarchical_transformer_seed13_hole_confusion_matrix.png](../outputs/figures/full_hierarchical_transformer_seed13_hole_confusion_matrix.png)
- [full_hierarchical_no_line_type_seed13_hole_confusion_matrix.png](../outputs/figures/full_hierarchical_no_line_type_seed13_hole_confusion_matrix.png)
- [full_hierarchical_transformer_seed13_test_predictions.jsonl](../outputs/predictions/full_hierarchical_transformer_seed13_test_predictions.jsonl)
- [full_tfidf_lr_seed13_test_predictions.jsonl](../outputs/predictions/full_tfidf_lr_seed13_test_predictions.jsonl)

### 7.1 Intent Classification Behavior

The intent task is dominated by lexical patterns from commit messages and short diff phrases rather than by deeper structural reasoning over RTL diffs.

The strongest intent model is TF-IDF. In its representative seed-13 confusion matrix:

- `feature_or_behavior_change` is the easiest class with F1 `0.6387`
- `configuration_timing` is moderate with F1 `0.4650`
- `bug_fix` is weaker with F1 `0.4111`
- `refactor_cleanup` is hardest with F1 only `0.1642`

The hierarchical Transformer does **not** improve this task. In the representative seed-13 matrix it reaches macro-F1 `0.2965`, and the main failure mode is class collapse:

- `feature_or_behavior_change` still has decent F1 `0.6188`
- `configuration_timing` falls to F1 `0.2114`
- `bug_fix` falls to F1 `0.3557`
- `refactor_cleanup` collapses entirely to F1 `0.0`

The confusion matrices make the reason clear. In seed 13:

- `92 / 188` true `configuration_timing` examples are predicted as `feature_or_behavior_change`
- `50 / 102` true `refactor_cleanup` examples are predicted as `bug_fix`
- `48 / 102` true `refactor_cleanup` examples are predicted as `feature_or_behavior_change`

This behavior is consistent with the class distribution. `refactor_cleanup` is only `8.5%` of the full dataset, and its keyword-based labels are intrinsically noisy because words like `move`, `simplify`, and `remove unused` overlap with bug fixes and behavior changes.

Prediction-file inspection confirms that several `configuration_timing` commits are linguistically close to feature additions:

- `[top_darjeeling,soc_proxy] Add AON clock and reset` in `soc_proxy.sv` is a true `configuration_timing` example but is predicted as `feature_or_behavior_change`
- `[pwrmgr] Take external SoC reset into account in FSM` is also true `configuration_timing` and is again predicted as `feature_or_behavior_change`
- `[hw,mbx,rtl] Rename set/clear signals for better meaning` is a true `refactor_cleanup` example that the hierarchical model predicts as `feature_or_behavior_change` or `bug_fix`

These examples show that the intent categories are semantically entangled at the diff level.

The strongest warning sign comes from the `message_only` ablation. `full_tfidf_message_only` reaches macro-F1 `0.9855`. That is far above every diff-based model and indicates that the weak label is almost recoverable directly from the commit message that generated it. Therefore, the current intent benchmark is useful for repository-scale experimentation, but it is **not yet a clean test of pure code-diff understanding**.

### 7.2 Hole Detection Behavior

The hole-detection task tells a different story. Here the hierarchical Transformer is clearly better than the flat neural models and better than TF-IDF.

The seed-13 hole confusion matrices show the main mechanism:

- TF-IDF: `[[255, 172], [168, 202]]`
- Hierarchical Transformer: `[[346, 81], [167, 203]]`

The two models recover almost the same number of synthetic holes (`202` vs. `203` true positives), but the hierarchical model drastically reduces false alarms on real complete diffs (`81` false positives instead of `172`). This is why the hierarchical model gets much stronger hole accuracy, F1, AUROC, and PR-AUC.

This result is scientifically meaningful. The proposed model is not merely overfitting lexical cues; it is learning a more conservative and better-structured notion of what a suspicious incomplete diff looks like.

### 7.3 What the Ablations Show

#### Line-type embeddings

This is the main architectural result of the project.

Across three seeds:

- full model hole F1: `0.6029`
- no-line-type hole F1: `0.4724`
- full model hole AUROC: `0.7352`
- no-line-type hole AUROC: `0.6294`

The seed-13 confusion matrices explain the drop even more clearly:

- full model hole matrix: `[[346, 81], [167, 203]]`
- no-line-type hole matrix: `[[346, 81], [233, 137]]`

The entire first row is unchanged. The ablation keeps the same number of true negatives and false positives, but it loses `66` true positives on synthetic holes. In other words, **line-type embeddings mainly help the model recognize that an addition, deletion, or context line plays a different role in the diff**, which is exactly the architectural hypothesis we wanted to test.

#### Context lines

Removing context lines yields:

- intent macro-F1 `0.2677`
- hole F1 `0.5937`
- hole AUROC `0.7126`

Compared with the representative full model, hole detection degrades only slightly, while intent degrades more noticeably. The seed-13 no-context intent confusion matrix heavily overpredicts `feature_or_behavior_change`, including `165 / 188` true `configuration_timing` examples sent to that class. This suggests that context lines are more helpful for inferring *why* a change was made than for detecting whether an added/deleted change looks incomplete.

#### Multi-task learning

The auxiliary single-task ablations do **not** show a clear multitask advantage on the reference seed:

- full seed-13 intent macro-F1: `0.2965`
- intent-only seed-13 macro-F1: `0.3193`
- full seed-13 hole F1: `0.6208`
- hole-only seed-13 hole F1: `0.6354`

However, this conclusion is weaker than the line-type result for two reasons:

1. the auxiliary ablations were run on only one seed
2. the non-target head metrics in these runs are not meaningful, because that head is not optimized

So the correct conclusion is modest: **the executed reference-seed run does not provide evidence that multitask learning helped**.

### 7.4 Mutation-Type Breakdown

The test set for hole detection is dominated by a single mutation family:

- `drop_added_line`: `304 / 370` synthetic examples (`82.2%`)
- `remove_added_guard_or_assertion`: `58 / 370` (`15.7%`)
- `flip_binary_constant`: `6 / 370` (`1.6%`)
- `remove_reset_or_default_assignment`: `2 / 370` (`0.5%`)

There are **no** test examples for `drop_hunk`, `flip_comparison_operator`, or `flip_logical_operator`, so the final evaluation cannot say much about those operators.

Using the representative prediction file for the hierarchical Transformer, hole recall by mutation type is:

| Mutation type | Test support | Hole recall |
| --- | ---: | ---: |
| `drop_added_line` | 304 | 0.6086 |
| `remove_added_guard_or_assertion` | 58 | 0.2931 |
| `flip_binary_constant` | 6 | 0.0000 |
| `remove_reset_or_default_assignment` | 2 | 0.5000 |

This explains why the model can achieve a strong overall hole F1 while still missing subtle semantic bugs. Removing a whole added line is comparatively easy to detect. Missing guards, missing assertions, and tiny constant flips are much harder because the diff remains lexically plausible.

### 7.5 Qualitative Error Analysis From Predictions

The saved prediction files reveal recurring error patterns.

| Case | Example | Observation |
| --- | --- | --- |
| High-confidence false positive on `complete` | `chip_darjeeling_cw310.sv`, commit `[darjeeling,ast,rtl] Disable clock bypass` | The hierarchical model predicts `synthetic_hole` with probability `0.9730`. Small clock/reset-related edits appear risky to the model even when they are valid complete changes. |
| High-confidence false positive on `complete` | `rom_ctrl.sv`, commit `[hw,rom_ctrl,rtl] Remove unused CLK_WAIT_BOUNDS definition` | A cleanup removal is predicted as a hole with probability `0.9720`, suggesting that deleting configuration-related lines is often treated as suspicious. |
| High-confidence false negative on `synthetic_hole` | `rom_ctrl_compare.sv`, synthetic `drop_added_line`, commit `[rom_ctrl,rtl] Use the PossibleActions parameter in rom_ctrl_compare` | The mutated example is predicted `complete` with hole probability only `0.0772`. Parameter/configuration edits are especially hard when a missing line does not destroy superficial diff coherence. |
| High-confidence false negative on `synthetic_hole` | `tlul_assert.sv`, synthetic `remove_added_guard_or_assertion`, commit `[tl] Move assertions in tlul_assert to the posedge` | Removed assertions are frequently missed; the representative model assigns hole probability only `0.1128`. |

These examples match the mutation breakdown: the model is strongest on obvious missing-line patterns and weakest on semantically subtle guard or assertion edits.

### 7.6 Overall Interpretation

The project therefore produces a mixed but meaningful outcome:

- For **Task A (intent)**, the weak labels are too tightly coupled to commit-message keywords. A simple lexical baseline is strongest, and a message-only ablation is almost perfect. This is a useful negative result.
- For **Task B (hole detection)**, the proposed hierarchical model is genuinely helpful. It achieves the best full-run hole metrics and the main ablation supports the claim that explicit line-type modeling matters.

That is a scientifically valid result even though the intended “deep model wins on everything” story did not happen.

## 8. Limitations and Future Work

The main limitations are:

1. **Weak-label leakage in intent classification.**  
   Since intent labels are generated from commit-message keywords, the message-only control almost solves the task. Future work should manually relabel a subset or derive labels from issue trackers or review metadata instead of from the same text channel used for supervision.

2. **Synthetic holes are dominated by dropped added lines.**  
   More than four-fifths of test synthetic examples are `drop_added_line`. This biases the task toward visibly incomplete diffs. Future work should increase the frequency of operator flips, missing resets, and hunk-level omissions.

3. **Some mutation families are too rare to evaluate.**  
   In the executed test split there are no held-out examples for `drop_hunk`, `flip_comparison_operator`, or `flip_logical_operator`.

4. **`refactor_cleanup` is both rare and noisy.**  
   It is only `8.5%` of the dataset and is often semantically close to bug fixes and behavior changes. Better labels or targeted sampling would likely help.

5. **Repository-path filtering is imperfect.**  
   The explicit exclusions remove `/dv/`, but repository conventions such as `pre_dv/.../rtl/...` can still leave borderline collateral in the dataset if it lives under an RTL path.

6. **Auxiliary ablations were executed on one seed.**  
   The main comparison is replicated across three seeds, but `no_context`, `message_only`, and `no_multitask` are reference-seed analyses rather than full multi-seed sweeps.

Future work should focus on manual label validation, broader hole operators, richer HDL-specific structure, and perhaps graph or compiler-informed representations that can better distinguish cleanup from semantic behavior change.

## 9. Team Contribution Placeholders

- Team member 1: `[fill in]`
- Team member 2: `[fill in]`

## 10. References

1. lowRISC. **OpenTitan**. GitHub repository. https://github.com/lowRISC/opentitan
2. **CC2Vec: Distributed Representations of Code Changes**.
3. **PatchNet: Hierarchical Deep Learning-Based Representation of Source Code Changes**.
4. **DeepJIT: An End-to-End Deep Learning Framework for Just-in-Time Defect Prediction**.
5. **CodeReviewer: Pre-Training for Automating Code Review Activities**.
