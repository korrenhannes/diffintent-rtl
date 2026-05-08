
# DiffIntent-RTL: End-to-End Deep Learning Project Execution Plan

**Course:** Deep Learning Project  
**Project type:** Applied + algorithmic deep learning project  
**Domain:** Code understanding / NLP for hardware design automation  
**Main repository:** [`lowRISC/opentitan`](https://github.com/lowRISC/opentitan)  
**Main language scope:** SystemVerilog RTL files (`hw/**/rtl/*.sv`)  
**Implementation framework:** PyTorch  
**Team members:** `[Full Name 1]`, `[Full Name 2]`

---

## 1. Project Summary

This project studies whether a deep learning model can understand the intent and possible incompleteness of a hardware code change by comparing two versions of the same SystemVerilog file.

Given:

```text
old version of file
new version of file
unified git diff
commit message
file path
```

the model will predict two targets:

1. **Change intent**  
   A multi-class label describing why the change was made.

2. **Implementation-hole risk**  
   A binary label estimating whether the change appears complete or whether it may contain an incomplete implementation pattern.

The core research idea is to build a **diff-aware hierarchical PyTorch model** that explicitly distinguishes added lines, deleted lines, and unchanged context lines. The model will be compared against simpler baselines and evaluated through quantitative metrics, ablation studies, and qualitative error analysis.

---

## 2. Alignment With Course Requirements

| Course requirement | How this project satisfies it |
|---|---|
| Practical, systematic, and deep implementation | Full data pipeline, PyTorch training, model comparison, and analysis |
| PyTorch implementation | All neural models will be implemented in PyTorch |
| Substantial model training | The project trains a bag-of-tokens MLP, BiGRU, and hierarchical Transformer |
| Clear baseline | TF-IDF + logistic regression, PyTorch MLP, and PyTorch BiGRU |
| Appropriate metrics | Macro-F1, per-class F1, AUROC, PR-AUC, confusion matrices |
| Comparison between models | Baselines vs. proposed model vs. ablations |
| Deep result analysis | Error taxonomy, examples, class-level failures, label-noise discussion |
| Final report reproducibility | GitHub repository, scripts, config files, seed control, run instructions |
| Scientific relevance | Builds on CC2Vec, PatchNet, DeepJIT, and CodeReviewer-style change modeling |
| Planned novelty | Diff-aware line-type embeddings + multi-task learning for RTL code changes |

---

## 3. Research Questions

### RQ1 — Change Intent Classification

Can a neural model classify the intent of an RTL code change from the old/new file versions and the unified diff?

Target labels:

```text
bug_fix
feature_or_behavior_change
refactor_cleanup
configuration_timing
```

### RQ2 — Implementation-Hole Detection

Can a neural model detect suspicious incomplete changes generated from real accepted commits?

Target labels:

```text
complete
synthetic_hole
```

### RQ3 — Architecture Contribution

Does explicitly modeling diff structure — added lines, deleted lines, and context lines — improve performance compared with flat token-based models?

### RQ4 — Multi-Task Learning

Does jointly training intent classification and hole detection improve representation quality compared with training each task separately?

---

## 4. Scope Control

The project is intentionally scoped to be feasible.

### In scope

```text
Repository: lowRISC/opentitan
Language: SystemVerilog
Files: hw/**/rtl/*.sv
Change type: modified files only
Diff type: unified diffs
Tasks: classification only
Models: lightweight PyTorch models
```

### Out of scope

```text
Full hardware formal verification
Simulation-based correctness checking
Large language model prompting as the main method
Multi-repository training in the first version
Generated/vendor/testbench files
Very large commits
Full program dependence graphs
```

### Fallback scope

If not enough clean examples are found in `hw/**/rtl/*.sv`, expand to:

```text
hw/**/*.sv
```

while still excluding:

```text
*/dv/*
*/test/*
*/tests/*
vendor/*
third_party/*
generated/*
```

---

## 5. Literature-Based Methodological Basis

The project follows the experimental pattern of prior deep learning work on code changes.

### CC2Vec

CC2Vec learns distributed representations of code changes, using the relationship between added and removed code and commit messages as semantic supervision.

Project adaptation:

```text
Use commit messages as weak supervision for change intent labels.
Represent the change itself, not only the final code.
```

### PatchNet

PatchNet models patches using hierarchical structure.

Project adaptation:

```text
Represent each diff as:
file -> hunk -> line -> token
```

The project will use a simplified line-level hierarchy suitable for a course project.

### DeepJIT

DeepJIT predicts defect-prone commits using code changes and commit messages.

Project adaptation:

```text
Predict possible implementation-hole risk from code changes.
```

### CodeReviewer

CodeReviewer studies code review tasks such as diff quality estimation and code refinement.

Project adaptation:

```text
Treat suspicious incomplete diffs as a quality/risk-estimation problem.
```

---

## 6. Dataset Design

### 6.1 Source Repository

Use:

```bash
git clone https://github.com/lowRISC/opentitan.git external/opentitan
```

OpenTitan is selected because it is a large open-source chip-design repository with meaningful SystemVerilog RTL history.

### 6.2 File Filter

Keep files matching:

```text
hw/**/rtl/*.sv
```

Exclude paths containing:

```text
/dv/
/test/
/tests/
/vendor/
/third_party/
/generated/
/build/
/out/
```

### 6.3 Commit Filter

Keep commits satisfying:

```text
not a merge commit
not a pure revert commit
modifies at least one RTL .sv file
has a non-empty commit message
diff length <= 256 lines after preprocessing
```

Preferred clean setting:

```text
exactly one modified RTL file per example
```

Fallback setting:

```text
allow up to 3 modified RTL files, creating one example per changed file
```

### 6.4 Example Schema

Each dataset example will be stored as JSONL:

```json
{
  "repo": "opentitan",
  "commit_hash": "abc123",
  "parent_hash": "def456",
  "commit_date": "YYYY-MM-DD",
  "file_path": "hw/ip/example/rtl/example.sv",
  "commit_message": "fix reset behavior in ...",
  "old_code": "...",
  "new_code": "...",
  "unified_diff": "...",
  "intent_label": "bug_fix",
  "hole_label": "complete",
  "split": "train"
}
```

---

## 7. Labeling Plan

### 7.1 Intent Labels

Intent labels will be weakly derived from commit-message patterns.

| Label | Positive keyword patterns |
|---|---|
| `bug_fix` | `fix`, `bug`, `wrong`, `regression`, `incorrect`, `issue`, `repair` |
| `feature_or_behavior_change` | `add`, `implement`, `support`, `enable`, `introduce`, `new` |
| `refactor_cleanup` | `refactor`, `cleanup`, `rename`, `move`, `style`, `tidy`, `simplify` |
| `configuration_timing` | `clock`, `reset`, `timing`, `param`, `parameter`, `width`, `config`, `fsm` |

### 7.2 Ambiguous Commit Handling

Discard examples if:

```text
multiple label groups match strongly
no label group matches
message is only "update", "misc", "cleanup" without clear signal
message is a revert
commit changes too many unrelated files
```

### 7.3 Manual Validation

Manually inspect:

```text
25 examples per intent class
100 examples total
```

For each inspected example, record:

```text
weak label correct / incorrect / ambiguous
reason for ambiguity
```

This will be reported as a label-quality estimate in the final report.

### 7.4 Implementation-Hole Labels

Accepted real commits are labeled:

```text
hole_label = complete
```

Synthetic hole examples are generated by corrupting the accepted `new_code` or the accepted diff.

Each original complete example may produce one synthetic hole example.

#### Hole mutation operators

Use only simple, explainable mutations:

| Mutation | Example |
|---|---|
| Remove added guard | Delete an added `if (...) begin` block or assertion |
| Remove reset/default assignment | Delete added assignment under reset/default branch |
| Drop one added line | Remove a single semantically important added line |
| Drop one hunk | In multi-hunk commits, keep only part of the original change |
| Flip comparison | `==` ↔ `!=`, `<` ↔ `>=`, `<=` ↔ `>` |
| Flip logical operator | `&&` ↔ `||` |
| Change constant width/value | `'0` ↔ `'1`, `1'b0` ↔ `1'b1`, width value change |

Reject synthetic holes if:

```text
the mutation causes empty diff
the mutation only changes whitespace
the mutation creates invalid text formatting
the mutation is outside changed lines
```

---

## 8. Data Split

Use chronological split by commit date to avoid future-to-past leakage.

```text
70% oldest examples -> train
15% middle examples -> validation
15% newest examples -> test
```

Why chronological?

```text
It better simulates real deployment: training on past commits and predicting future changes.
```

Additional leakage control:

```text
Do not split synthetic hole and original complete version across different splits.
Both must stay in the same split.
```

---

## 9. Preprocessing

### 9.1 Diff Format

Convert each changed file to a normalized unified diff.

Line prefixes:

```text
<ADD> added line
<DEL> deleted line
<CTX> unchanged context line
<HUNK> hunk header
<FILE> file metadata
```

Example:

```text
<FILE> hw/ip/foo/rtl/foo.sv
<HUNK> @@ -42,7 +42,8 @@
<CTX> always_ff @(posedge clk_i or negedge rst_ni) begin
<DEL>   state_q <= Idle;
<ADD>   state_q <= Reset;
<ADD>   valid_q <= 1'b0;
```

### 9.2 Tokenization

Use a simple SystemVerilog-aware tokenizer:

```text
identifiers
numbers
operators
punctuation
keywords
macro symbols
```

Split examples:

```text
state_q <= 1'b0;
```

into:

```text
state_q
<=
1'b0
;
```

Normalize rare numeric values optionally:

```text
NUM
WIDTH_NUM
HEX_NUM
```

Do not remove SystemVerilog keywords.

### 9.3 Length Limits

Recommended limits:

```text
max_lines_per_diff = 128
max_tokens_per_line = 64
max_total_tokens_flat = 2048
```

Long diffs:

```text
truncate from the middle after preserving changed lines
```

Priority order for keeping lines:

```text
added/deleted lines first
nearby context second
far context last
```

---

## 10. Model Architectures

## 10.1 Baseline 0: TF-IDF + Logistic Regression

Purpose:

```text
Non-neural sanity baseline.
```

Input:

```text
unified diff as text
```

Models:

```text
one logistic regression classifier for intent
one logistic regression classifier for hole detection
```

Features:

```text
word n-grams: 1-2
character n-grams: 3-5
max_features: 50,000
```

This baseline is not the main deep learning contribution but establishes whether simple lexical features are already strong.

---

## 10.2 Baseline 1: PyTorch Bag-of-Tokens MLP

Input:

```text
flat token sequence from diff
```

Architecture:

```text
Embedding layer
mean pooling
dropout
2-layer MLP
two output heads
```

Recommended hyperparameters:

```yaml
embedding_dim: 128
hidden_dim: 256
dropout: 0.2
batch_size: 32
learning_rate: 0.001
epochs: 20
optimizer: AdamW
```

---

## 10.3 Baseline 2: PyTorch Flat BiGRU

Input:

```text
flat token sequence from diff
```

Architecture:

```text
Embedding layer
BiGRU
attention pooling
two output heads
```

Recommended hyperparameters:

```yaml
embedding_dim: 128
hidden_dim: 128
num_layers: 1
dropout: 0.2
batch_size: 16
learning_rate: 0.001
epochs: 20
optimizer: AdamW
```

---

## 10.4 Proposed Model: Diff-Aware Hierarchical Transformer

The proposed architecture explicitly models diff structure.

### Input representation

Each diff is represented as:

```text
lines x tokens
```

Each token receives:

```text
token embedding
line-type embedding: ADD / DEL / CTX / HUNK / FILE
position embedding
```

### Architecture

```text
Token embedding
+ line-type embedding
+ token position embedding
        |
Line encoder: small CNN or BiGRU over tokens in each line
        |
Line representations
        |
Diff encoder: 2-layer Transformer encoder over lines
        |
[CLS] or attention-pooled diff vector
        |
Intent classification head
Hole-risk classification head
```

### Recommended hyperparameters

```yaml
vocab_size: determined from training data
token_embedding_dim: 128
line_type_embedding_dim: 32
line_encoder: "bigru"
line_hidden_dim: 128
transformer_layers: 2
transformer_heads: 4
transformer_ff_dim: 512
dropout: 0.2
batch_size: 8
learning_rate: 0.0005
weight_decay: 0.01
epochs: 30
early_stopping_patience: 5
```

### Multi-task loss

```text
L_total = L_intent + lambda_hole * L_hole
```

Start with:

```text
lambda_hole = 1.0
```

If one task dominates, tune:

```text
lambda_hole in {0.5, 1.0, 2.0}
```

---

## 11. Ablation Studies

Run the following ablations:

| Experiment | Purpose |
|---|---|
| Proposed full model | Main result |
| No line-type embeddings | Test whether ADD/DEL/CTX information helps |
| No multi-task learning | Train separate models for each task |
| Diff only, no commit message | Verify model learns from code change |
| Commit message only | Estimate how much weak-label leakage exists |
| No context lines | Test whether unchanged context helps |

The most important ablation is:

```text
full model vs. no line-type embeddings
```

This directly tests the core contribution.

---

## 12. Training Protocol

### 12.1 Environment

Recommended:

```text
Python 3.10+
PyTorch 2.x
CUDA GPU if available
scikit-learn
pandas
numpy
matplotlib
GitPython or subprocess git calls
PyYAML
tqdm
```

### 12.2 Reproducibility

Set all random seeds:

```python
import random
import numpy as np
import torch

seed = 42
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
torch.cuda.manual_seed_all(seed)
```

Use deterministic settings where practical:

```python
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
```

Save:

```text
config file
train/val/test split files
model checkpoint
metrics JSON
confusion matrices
random seed
git commit hash of project code
```

### 12.3 Early Stopping

Monitor:

```text
validation macro-F1 for intent
validation F1 for hole detection
```

Primary stopping metric:

```text
average of validation intent macro-F1 and validation hole F1
```

---

## 13. Evaluation Metrics

### 13.1 Intent Classification

Report:

```text
accuracy
macro-F1
weighted-F1
per-class precision
per-class recall
per-class F1
confusion matrix
```

Primary metric:

```text
macro-F1
```

Reason:

```text
Intent classes may be imbalanced.
```

### 13.2 Implementation-Hole Detection

Report:

```text
accuracy
precision
recall
F1
AUROC
PR-AUC
confusion matrix
```

Primary metric:

```text
F1
```

Secondary metric:

```text
PR-AUC
```

Reason:

```text
Implementation-hole examples are risk-oriented; precision-recall behavior is important.
```

### 13.3 Statistical Robustness

Run each neural model with:

```text
3 random seeds: 13, 42, 123
```

Report:

```text
mean ± standard deviation
```

If time is limited, run the final proposed model with 3 seeds and baselines with 1 seed.

---

## 14. Expected Result Tables

### 14.1 Main Results Table

| Model | Intent Macro-F1 | Intent Acc. | Hole F1 | Hole AUROC | Notes |
|---|---:|---:|---:|---:|---|
| TF-IDF + LR | TBD | TBD | TBD | TBD | lexical baseline |
| PyTorch MLP | TBD | TBD | TBD | TBD | neural baseline |
| PyTorch BiGRU | TBD | TBD | TBD | TBD | sequence baseline |
| Hierarchical Transformer | TBD | TBD | TBD | TBD | proposed |

### 14.2 Ablation Table

| Variant | Intent Macro-F1 | Hole F1 | Interpretation |
|---|---:|---:|---|
| Full model | TBD | TBD | main result |
| No line-type embeddings | TBD | TBD | tests diff awareness |
| No multi-task learning | TBD | TBD | tests shared representation |
| No context lines | TBD | TBD | tests surrounding context |
| Commit message only | TBD | TBD | estimates label leakage |

### 14.3 Error Analysis Table

| Error type | Example count | Likely cause | Fix direction |
|---|---:|---|---|
| bug_fix confused with refactor | TBD | weak message labels | better manual labels |
| false hole on safe change | TBD | mutation bias | harder negatives |
| missed dropped reset | TBD | long-range dependency | structural features |
| timing/config confused with feature | TBD | overlapping vocabulary | better taxonomy |

---

## 15. Qualitative Error Analysis

Inspect:

```text
15 intent errors
15 hole-detection errors
```

For each example, record:

```text
commit hash
file path
true label
predicted label
short diff excerpt
suspected reason for error
```

Classify errors into:

```text
label noise
ambiguous commit message
diff too long
requires hardware semantics
requires cross-file context
model missed added/deleted line
synthetic mutation unrealistic
```

Include 3–5 representative examples in the final report.

---

## 16. Project Repository Structure

```text
diffintent-rtl/
├── README.md
├── PROJECT_PLAN.md
├── requirements.txt
├── environment.yml
├── configs/
│   ├── data_opentitan.yaml
│   ├── mlp.yaml
│   ├── bigru.yaml
│   └── hierarchical_transformer.yaml
├── scripts/
│   ├── clone_repo.sh
│   ├── extract_commits.py
│   ├── build_dataset.py
│   ├── generate_holes.py
│   ├── split_dataset.py
│   ├── train.py
│   ├── evaluate.py
│   ├── run_all_baselines.sh
│   └── run_ablations.sh
├── src/
│   ├── data/
│   │   ├── git_mining.py
│   │   ├── diff_parser.py
│   │   ├── tokenizer.py
│   │   ├── dataset.py
│   │   └── collate.py
│   ├── models/
│   │   ├── mlp.py
│   │   ├── bigru.py
│   │   ├── hierarchical_transformer.py
│   │   └── heads.py
│   ├── training/
│   │   ├── losses.py
│   │   ├── trainer.py
│   │   └── metrics.py
│   └── utils/
│       ├── seed.py
│       ├── logging.py
│       └── io.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── splits/
├── outputs/
│   ├── checkpoints/
│   ├── metrics/
│   ├── figures/
│   └── predictions/
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_error_analysis.ipynb
│   └── 03_figures_for_report.ipynb
├── report/
│   ├── final_report.md
│   ├── final_report.pdf
│   └── figures/
└── slides/
    └── presentation.pdf
```

---

## 17. Script-Level Execution Plan

### Step 1 — Clone OpenTitan

```bash
bash scripts/clone_repo.sh
```

Expected output:

```text
external/opentitan/
```

### Step 2 — Extract Candidate Commits

```bash
python scripts/extract_commits.py   --repo external/opentitan   --paths "hw/**/rtl/*.sv"   --output data/raw/opentitan_rtl_commits.jsonl
```

Expected output:

```text
commit hash
parent hash
date
message
changed RTL files
changed total files
```

### Step 3 — Build Old/New/Diff Examples

```bash
python scripts/build_dataset.py   --repo external/opentitan   --commits data/raw/opentitan_rtl_commits.jsonl   --output data/processed/opentitan_real_examples.jsonl   --max-diff-lines 256
```

Expected output:

```text
old_code
new_code
unified_diff
metadata
weak intent labels
```

### Step 4 — Generate Synthetic Holes

```bash
python scripts/generate_holes.py   --input data/processed/opentitan_real_examples.jsonl   --output data/processed/opentitan_with_holes.jsonl   --max-holes-per-example 1
```

Expected output:

```text
complete examples
synthetic_hole examples
```

### Step 5 — Split Dataset Chronologically

```bash
python scripts/split_dataset.py   --input data/processed/opentitan_with_holes.jsonl   --output-dir data/splits   --train-ratio 0.70   --val-ratio 0.15   --test-ratio 0.15
```

Expected output:

```text
train.jsonl
val.jsonl
test.jsonl
```

### Step 6 — Train Baselines

```bash
bash scripts/run_all_baselines.sh
```

This should train:

```text
TF-IDF + logistic regression
PyTorch MLP
PyTorch BiGRU
```

### Step 7 — Train Proposed Model

```bash
python scripts/train.py   --config configs/hierarchical_transformer.yaml   --train data/splits/train.jsonl   --val data/splits/val.jsonl   --output outputs/checkpoints/hierarchical_transformer
```

### Step 8 — Evaluate on Test Set

```bash
python scripts/evaluate.py   --checkpoint outputs/checkpoints/hierarchical_transformer/best.pt   --test data/splits/test.jsonl   --output outputs/metrics/hierarchical_transformer_test.json
```

### Step 9 — Run Ablations

```bash
bash scripts/run_ablations.sh
```

### Step 10 — Prepare Figures

Generate:

```text
intent confusion matrix
hole confusion matrix
main results bar chart
ablation bar chart
dataset label distribution
diff length distribution
```

---

## 18. Minimal PyTorch Model Interface

All models should expose the same interface:

```python
class DiffIntentModel(torch.nn.Module):
    def forward(self, batch):
        # batch: dictionary with token ids, masks, line types, and labels
        # returns intent logits and hole logits
        return {
            "intent_logits": intent_logits,
            "hole_logits": hole_logits
        }
```

Training code should be model-agnostic:

```python
outputs = model(batch)
loss_intent = cross_entropy(outputs["intent_logits"], batch["intent_label"])
loss_hole = cross_entropy(outputs["hole_logits"], batch["hole_label"])
loss = loss_intent + lambda_hole * loss_hole
```

---

## 19. Definition of Success

The project is successful if it produces:

```text
a working mined dataset from OpenTitan
at least 3 trained PyTorch models
a clear baseline comparison
at least 2 ablation experiments
quantitative results on held-out test data
qualitative error analysis
reproducible GitHub repository
final report up to 5 pages
15-minute presentation
```

A strong result would be:

```text
The hierarchical diff-aware Transformer improves over the flat BiGRU
and the no-line-type ablation, especially on macro-F1 and hole F1.
```

A scientifically acceptable result would also be:

```text
The proposed model does not significantly outperform baselines,
but the error analysis clearly explains why and identifies limitations.
```

---

## 20. Risk Management

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Too few clean RTL commits | Medium | High | Expand from `hw/**/rtl/*.sv` to `hw/**/*.sv` |
| Weak labels are noisy | High | Medium | Manual validation, label-noise discussion, ambiguous filtering |
| Synthetic holes are too easy | Medium | Medium | Use multiple mutation types and report mutation-specific results |
| Model overfits commit message labels | Medium | High | Run diff-only and message-only ablations |
| Training too slow | Low-Medium | Medium | Reduce max lines/tokens, use BiGRU as final if needed |
| Hardware semantics are too difficult | Medium | Medium | Present as risk estimation, not proof of correctness |
| Class imbalance | High | Medium | Use macro-F1, class weights, balanced sampling |

---

## 21. Timeline

### Week 1 — Setup and Literature Consolidation

Deliverables:

```text
GitHub repository initialized
OpenTitan cloned
literature summary completed
PROJECT_PLAN.md finalized
```

### Week 2 — Data Mining

Deliverables:

```text
commit extraction script
old/new/diff extraction script
first dataset statistics
manual inspection of sample diffs
```

### Week 3 — Labeling and Synthetic Holes

Deliverables:

```text
intent weak-labeling script
synthetic hole generation script
manual validation subset
train/val/test split
```

### Week 4 — Baselines

Deliverables:

```text
TF-IDF baseline
PyTorch MLP baseline
PyTorch BiGRU baseline
baseline metrics table
```

### Week 5 — Proposed Model

Deliverables:

```text
hierarchical Transformer implemented
training completed
validation tuning completed
first test metrics
```

### Week 6 — Ablations and Analysis

Deliverables:

```text
no-line-type ablation
no-multitask ablation
diff-only vs. message-only analysis
confusion matrices
error analysis spreadsheet
```

### Week 7 — Final Report and Presentation

Deliverables:

```text
final report up to 5 pages
15-minute presentation
clean GitHub README
reproducibility instructions
final figures and tables
```

---

## 22. Final Report Structure

Maximum length:

```text
5 pages
```

Recommended structure:

```text
1. Introduction and motivation
2. Related work
3. Dataset construction
4. Method
5. Experiments
6. Results
7. Error analysis and discussion
8. Limitations and future work
9. Team contribution
10. References
```

### Must include

```text
motivation and problem definition
relevant literature
data description
models and hyperparameters
results
deep result analysis
limitations and future directions
references
team contribution
GitHub link
clear run instructions
```

---

## 23. Presentation Structure

Total time:

```text
15 minutes
```

Recommended slide plan:

| Slide | Time | Content |
|---|---:|---|
| 1 | 0:45 | Title, team, one-sentence problem |
| 2 | 1:15 | Motivation: why RTL code changes matter |
| 3 | 1:30 | Related work: CC2Vec, PatchNet, DeepJIT, CodeReviewer |
| 4 | 1:30 | Data pipeline from OpenTitan commits |
| 5 | 1:30 | Labeling: intent + synthetic holes |
| 6 | 2:00 | Model architecture |
| 7 | 1:30 | Baselines and ablations |
| 8 | 2:00 | Results table and confusion matrix |
| 9 | 1:30 | Error analysis |
| 10 | 1:00 | Limitations and future work |
| 11 | 0:30 | Summary |

---

## 24. Team Work Division

### Member 1

```text
Git mining pipeline
dataset construction
weak labeling
synthetic hole generation
data statistics
```

### Member 2

```text
PyTorch models
training loop
evaluation metrics
ablations
figures
```

### Joint work

```text
literature review
manual validation
error analysis
final report
presentation
code cleanup
```

The final report must explicitly describe each team member's contribution.

---

## 25. Reproducibility Checklist

Before submission, verify:

```text
[ ] README has installation instructions
[ ] requirements.txt or environment.yml exists
[ ] all random seeds are fixed
[ ] train/val/test split files are saved
[ ] configs for all models are saved
[ ] commands reproduce all reported results
[ ] figures are generated from saved metrics
[ ] final model checkpoints are documented
[ ] final report includes GitHub link
[ ] final report includes team contribution
[ ] final report includes limitations
[ ] presentation fits 15 minutes
```

---

## 26. Exact Final Commands Expected in README

```bash
# 1. Install environment
conda env create -f environment.yml
conda activate diffintent-rtl

# 2. Clone OpenTitan
bash scripts/clone_repo.sh

# 3. Build dataset
python scripts/extract_commits.py --config configs/data_opentitan.yaml
python scripts/build_dataset.py --config configs/data_opentitan.yaml
python scripts/generate_holes.py --config configs/data_opentitan.yaml
python scripts/split_dataset.py --config configs/data_opentitan.yaml

# 4. Train baselines
bash scripts/run_all_baselines.sh

# 5. Train proposed model
python scripts/train.py --config configs/hierarchical_transformer.yaml

# 6. Evaluate
python scripts/evaluate.py   --checkpoint outputs/checkpoints/hierarchical_transformer/best.pt   --test data/splits/test.jsonl   --output outputs/metrics/final_test_metrics.json

# 7. Generate figures
python scripts/make_figures.py   --metrics-dir outputs/metrics   --output-dir outputs/figures
```

---

## 27. Final Deliverables

```text
PROJECT_PLAN.md
proposal PDF, 300-500 words
GitHub code repository
processed dataset metadata
trained PyTorch models
metrics JSON files
figures
final report PDF, up to 5 pages
15-minute presentation
```

---

## 28. Main Limitations to Discuss

The project should explicitly acknowledge:

```text
Weak labels from commit messages are noisy.
Synthetic holes are approximations of real implementation bugs.
The model does not prove hardware correctness.
Some RTL bugs require simulation or formal verification.
Single-file diffs miss cross-file dependencies.
OpenTitan-specific training may not generalize to all chip projects.
```

These limitations are acceptable because the project goal is not formal verification. The goal is to test whether deep models can learn useful code-change representations for RTL diffs.

---

## 29. Expected Scientific Contribution

The expected contribution is:

```text
A reproducible PyTorch study of diff-based intent classification
and implementation-hole risk detection for real SystemVerilog RTL changes.
```

The specific methodological contribution is:

```text
A lightweight diff-aware hierarchical Transformer with line-type embeddings
and multi-task prediction heads, evaluated against strong simple baselines
and ablations.
```

The expected practical contribution is:

```text
A prototype that could help hardware developers prioritize suspicious RTL changes
for code review.
```

---

## 30. References

1. Hoang et al. **CC2Vec: Distributed Representations of Code Changes.** ICSE 2020.  
   https://arxiv.org/abs/2003.05620

2. Hoang et al. **PatchNet: Hierarchical Deep Learning-Based Stable Patch Identification.**  
   https://arxiv.org/abs/1911.03576

3. Hoang et al. **DeepJIT: An End-to-End Deep Learning Framework for Just-In-Time Defect Prediction.**  
   https://www.semanticscholar.org/paper/DeepJIT%3A-An-End-to-End-Deep-Learning-Framework-for-Hoang-Dam/952fe2400f4b1a33fa45aa1aefaa856235e13c0c

4. Li et al. **CodeReviewer: Pre-Training for Automating Code Review Activities.**  
   https://arxiv.org/abs/2203.09095

5. lowRISC. **OpenTitan GitHub Repository.**  
   https://github.com/lowRISC/opentitan

6. OpenTitan Project Website.  
   https://opentitan.org/

---

## 31. One-Sentence Version

This project trains and evaluates PyTorch models that classify the intent and possible incompleteness of SystemVerilog RTL code changes from OpenTitan by learning structured representations of unified diffs.
