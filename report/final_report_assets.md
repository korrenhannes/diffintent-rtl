# Final Report Assets

## Dataset Statistics

```json
{
  "avg_diff_line_count": 37.678,
  "example_counts": {
    "test": 797,
    "train": 3873,
    "val": 830
  },
  "group_counts": {
    "test": 427,
    "train": 1990,
    "val": 426
  },
  "hole_distribution": {
    "complete": 2843,
    "synthetic_hole": 2657
  },
  "intent_distribution": {
    "bug_fix": 1861,
    "configuration_timing": 934,
    "feature_or_behavior_change": 2240,
    "refactor_cleanup": 465
  },
  "mutation_distribution": {
    "drop_added_line": 2058,
    "drop_hunk": 12,
    "flip_binary_constant": 24,
    "flip_comparison_operator": 8,
    "flip_logical_operator": 2,
    "none": 2843,
    "remove_added_guard_or_assertion": 528,
    "remove_reset_or_default_assignment": 25
  },
  "num_examples": 5500,
  "num_groups": 2843
}
```

## Main Results

| setting_name | num_runs | intent_accuracy_mean | intent_macro_f1_mean | intent_macro_f1_std | hole_accuracy_mean | hole_f1_mean | hole_f1_std | hole_auroc_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_bigru | 3 | 0.3998327059807612 | 0.30228705169172704 | 0.028341893057717824 | 0.5821831869510665 | 0.4204336776177931 | 0.0677365845589627 | 0.5942169335611959 |
| full_hierarchical_transformer | 3 | 0.4065244667503137 | 0.300679108210622 | 0.022897752394201207 | 0.6725219573400251 | 0.602924109721289 | 0.022635862693944832 | 0.7351942106040467 |
| full_mlp | 3 | 0.40485152655792556 | 0.2960697769628042 | 0.05502621351111561 | 0.5529067335842744 | 0.32928079585018266 | 0.1418530272467224 | 0.5488237652172079 |
| full_tfidf_lr | 3 | 0.5131744040150564 | 0.41973380330967003 | 0.0 | 0.5734002509410289 | 0.543010752688172 | 0.0 | 0.6122982467244762 |

## Ablation Results

| setting_name | num_runs | intent_accuracy_mean | intent_macro_f1_mean | intent_macro_f1_std | hole_accuracy_mean | hole_f1_mean | hole_f1_std | hole_auroc_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_hierarchical_no_context | 1 | 0.47051442910915936 | 0.2676813961225539 | 0.0 | 0.6599749058971142 | 0.5937031484257871 | 0.0 | 0.7125957339072093 |
| full_hierarchical_no_line_type | 3 | 0.4094521120869929 | 0.30279830178943146 | 0.031031430161490438 | 0.589293182768716 | 0.47243304633690975 | 0.004770552986079231 | 0.6293583982108573 |
| full_hierarchical_no_multitask_hole | 1 | 0.29109159347553326 | 0.18127922210388553 | 0.0 | 0.6587202007528231 | 0.6353887399463807 | 0.0 | 0.7162795113614786 |
| full_hierarchical_no_multitask_intent | 1 | 0.45294855708908405 | 0.3192835120979899 | 0.0 | 0.4742785445420326 | 0.5797392176529589 | 0.0 | 0.49469903158427747 |
| full_tfidf_message_only | 1 | 0.9849435382685069 | 0.9854909069297515 | 0.0 | 0.5294855708908407 | 0.43609022556390975 | 0.0 | 0.5450250015823785 |

These tables summarize the available full-run aggregates.

## Figures

- `outputs/figures/dataset_label_distribution.png`
- `outputs/figures/diff_length_distribution.png`
- `outputs/figures/main_results_intent_macro_f1.png`
- `outputs/figures/main_results_hole_f1.png`
- model-specific confusion matrices in `outputs/figures/`
