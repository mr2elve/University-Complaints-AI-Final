# Research artifact provenance

`test_comparison.csv` is transcribed from saved cell 18 output and the supplied research README. Values are rounded to four decimal places; the mean column is the notebook's reported mean, not a recalculation from rounded values. High-urgency counts come from cell 19.

`routing_validation.csv` transcribes four requested operating points from saved cell 23 output. Coverage and routing accuracy are validation results (150 records), not test metrics or estimates of this application's live performance. Routing accuracy measures department correctness only among auto-routed cases. All points include P(high) < 0.30 as a condition for automatic routing.

`assets/svm_test_confusion_matrices.png` is the original embedded PNG extracted from cell 19 of `University_Complaints_AI_Final.ipynb`. It represents SVM test confusion matrices, not KazRoBERTa matrices. No matrices or row-level predictions were fabricated. Numerical confusion-matrix CSVs were not supplied.

Notebook architecture: cell 15. Preprocessing: cell 4. Split: cell 6. Inference: cell 20. Export: cell 24. The early cell 20 threshold is 0.60; the final export sets 0.75 and is authoritative for the application.

The supplied 1,000-row CSV was inspected for schema and size. Its texts are not automatically imported into the operational database or packaged into this application.

Base encoder config source (downloaded during setup): https://huggingface.co/kz-transformers/kaz-roberta-conversational/blob/main/config.json
The original export `config.json` is an application configuration, not a Transformers encoder config. The latter is kept separately as `model/encoder_config.json`.

## Multilingual XLM-RoBERTa upgrade — 14 November 2026

Source: [multilingual export](https://huggingface.co/mr2elve/xlmr-university-complaints-multilingual/tree/f15eb91b1b494b4ed92978a89b1f628e338b0ce3/XLMR_Multilingual_University_Complaints), revision `f15eb91b1b494b4ed92978a89b1f628e338b0ce3`. The subfolder is required.

- `xlmr_metrics_by_language.csv` and `xlmr_mixed_synthetic_metrics.json` are byte-for-byte copies of the published evaluation files. Evaluation was not rerun against the full held-out dataset, which was not supplied with the export.
- `tests/fixtures/xlmr_config.json` is a byte-for-byte copy of its task configuration, used for transport/validation tests without downloading weights.
- `xlmr_model_checksums.json` records local SHA-256 values and sizes for all downloaded artifacts and the separately obtained base encoder architecture configuration. No base encoder weights were fetched.
- `xlmr_runtime_validation.json` and `xlmr_streamlit_runtime_validation.json` contain locally measured CPU load/inference times, RSS and real predictions for `data/multilingual_examples.json`. These inputs are illustrative. The Streamlit measurement also verifies that the same resource object is reused. Download time is excluded; memory-mapped loading may defer page reads until inference.
- The config/model card specify masked mean pooling, dropout 0.2, four linear heads, XLM-R base and a 128-token limit. The checkpoint's named `heads.<task>.weight/bias` tensors establish `ModuleDict` structure. All 207 tensors load strictly (278,055,183 parameters). The original notebook's cell 13 corroborates pooling, but its numbered heads are not the new checkpoint's architecture.

The original research results, screenshots and validation files remain historical evidence. The new translation-grouped split and synthetic mixed-language test are separate experiments, not replacements for the original comparison table. Routing thresholds were preserved as application policy and were not recalibrated on the new export.
