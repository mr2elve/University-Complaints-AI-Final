# Research artifact provenance

`test_comparison.csv` is transcribed from saved cell 18 output and the supplied research README. Values are rounded to four decimal places; the mean column is the notebook's reported mean, not a recalculation from rounded values. High-urgency counts come from cell 19.

`routing_validation.csv` transcribes four requested operating points from saved cell 23 output. Coverage and routing accuracy are validation results (150 records), not test metrics or estimates of this application's live performance. Routing accuracy measures department correctness only among auto-routed cases. All points include P(high) < 0.30 as a condition for automatic routing.

`assets/svm_test_confusion_matrices.png` is the original embedded PNG extracted from cell 19 of `University_Complaints_AI_Final.ipynb`. It represents SVM test confusion matrices, not KazRoBERTa matrices. No matrices or row-level predictions were fabricated. Numerical confusion-matrix CSVs were not supplied.

Notebook architecture: cell 15. Preprocessing: cell 4. Split: cell 6. Inference: cell 20. Export: cell 24. The early cell 20 threshold is 0.60; the final export sets 0.75 and is authoritative for the application.

The supplied 1,000-row CSV was inspected for schema and size. Its texts are not automatically imported into the operational database or packaged into this application.

Base encoder config source (downloaded during setup): https://huggingface.co/kz-transformers/kaz-roberta-conversational/blob/main/config.json
The original export `config.json` is an application configuration, not a Transformers encoder config. The latter is kept separately as `model/encoder_config.json`.
