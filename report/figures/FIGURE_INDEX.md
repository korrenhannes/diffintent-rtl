# Figure Index

- `figure_dataset_overview.png`: Intent labels, hole labels, overall synthetic mutation counts, and test-set mutation counts.
- `figure_diff_length_distribution.png`: Distribution of diff lengths in the processed full dataset, separated by complete and synthetic-hole examples.
- `figure_main_results.png`: Three-panel comparison of intent macro-F1, hole F1, and hole AUROC for the four main full models.
- `figure_ablation_results.png`: Ablation results with dashed baseline from the full hierarchical Transformer.
- `figure_intent_per_class_f1.png`: Per-class intent F1 for the best intent baseline, the proposed model, and the no-line-type ablation.
- `figure_hole_roc_curves.png`: ROC curves for hole detection using representative full runs of the four main models.
- `figure_hole_pr_curves.png`: Precision-recall curves for hole detection using representative full runs of the four main models.
- `figure_hole_mutation_recall.png`: Hole recall by synthetic mutation type for representative full runs.
- `figure_pairwise_hole_ranking.png`: Pairwise ranking accuracy and average hole-score margin between each synthetic mutation and its paired complete example.
- `figure_intent_confusion_panels.png`: Row-normalized intent confusion matrices for the best intent baseline and the proposed model.
- `figure_hole_confusion_panels.png`: Row-normalized hole confusion matrices for TF-IDF, the proposed model, and the no-line-type ablation.

## Additional study figures (error analysis, generalization, improved labeling)

- `erroranalysis_perclass_f1.png`: Per-class intent F1 comparing the lexical baseline (TF-IDF) with the Hierarchical Transformer; shows the Transformer collapsing on the rare `refactor_cleanup` class.
- `erroranalysis_confusion_full_hierarchical_transformer.png`: Intent confusion matrix for the Hierarchical Transformer; the `refactor` column is all zeros (the model never predicts it).
- `erroranalysis_confusion_full_tfidf_lr.png`: Intent confusion matrix for the TF-IDF baseline, shown for comparison.
- `generalization_compare.png`: Cross-project comparison between OpenTitan and Caliptra — weak-label discard rate and change-type (intent) profile.
- `labeler_improvement.png`: Weak-label discard rate before vs after the improved keyword scheme (OpenTitan 29%→16%, Caliptra 53%→25%), showing a narrower cross-project gap.
- `rtl_features_model.png`: Intent macro-F1 comparison — lexical baseline vs a hardware-aware Random Forest model vs a hybrid (text + features); the hardware-aware model beats the text baseline (0.527 vs 0.379).
