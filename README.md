# Intelligent University Complaint Analysis and Routing (Kazakh NLP)

A research-oriented AI project for classifying **university student complaints in Kazakh** and supporting confidence-aware routing to responsible departments. Developed as a final project for **AI Essentials: Theory and Applications**.

This repository contains the **Google Colab research notebook**. The Streamlit user interface is a **separate application**, not part of this notebook repository.

## Project overview

Given a Kazakh-language student complaint, the models predict four labels:

| Task | Classes |
| --- | --- |
| Category | `academic_process`, `administrative_services`, `campus_environment` |
| Urgency | `low`, `medium`, `high` |
| Tone | `neutral`, `dissatisfied`, `intense_negative` |
| Department | `academic_affairs`, `faculty_dean_office`, `student_service_center`, `facilities_office`, `finance_office`, `security_ombudsperson` |

The research explores both classification performance and a **human-in-the-loop routing policy**: lower-confidence complaints and potentially urgent complaints can be referred for manual review.

## Dataset and experimental setup

- **Dataset:** `university_student_complaints_dedup.csv` (1,000 Kazakh complaint texts, four target labels; original dataset is referenced in the notebook).
- **Train:** 700 examples (70%)
- **Validation:** 150 examples (15%)
- **Test:** 150 examples (15%)
- **Split:** random seed 42, stratified on category × urgency.
- **Preprocessing:** Unicode NFC normalization, removal of selected invisible characters, whitespace cleanup; Kazakh characters and punctuation are retained.
- **Metrics:** accuracy, macro-averaged precision/recall/F1, confusion matrices, and task-level error analysis.

> **Data limitation:** Although exact duplicate texts were not detected, similarity analysis found structurally similar complaints across the splits. The current split is **not group-aware**, so results may overestimate performance on genuinely new, naturally written complaints. The 150-example test set also limits the certainty of small differences between models.

## Models

1. **Character TF-IDF + Linear SVM:** four independently trained classification pipelines; character `char_wb` 2–5-grams, with `C` selected on validation.
2. **BiLSTM + Attention:** shared bidirectional recurrent encoder with attention pooling and four task-specific classification heads.
3. **XLM-RoBERTa-base:** fine-tuned multilingual Transformer with a shared encoder and four classification heads.
4. **KazRoBERTa conversational:** fine-tuned Kazakh-language Transformer with a shared encoder and four classification heads.

Neural architectures use a sum of four classification losses for joint prediction.

## Final test results

**Macro-F1 on the held-out test set (150 complaints)**, as recorded in the notebook:

| Model | Category | Urgency | Tone | Department | Mean Macro-F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Linear SVM + TF-IDF** | 0.9867 | 0.9722 | 1.0000 | 0.9334 | **0.9731** |
| KazRoBERTa Multi-Task | 0.9933 | 0.9510 | 0.9844 | 0.9128 | 0.9604 |
| BiLSTM + Attention | 0.9733 | 0.9790 | 1.0000 | 0.8642 | 0.9541 |
| XLM-RoBERTa Multi-Task | 0.9798 | 0.9313 | 0.9681 | 0.9000 | 0.9448 |

The **Linear SVM** achieved the highest mean test Macro-F1 in this experiment. KazRoBERTa was selected as the neural-model basis for the separate inference/routing prototype, **not** because it had the highest overall test score.

Among 38 high-urgency test complaints, the models incorrectly classified the urgency as non-high in **3 cases for SVM**, **3 for BiLSTM**, **5 for KazRoBERTa**, and **5 for XLM-RoBERTa**. This motivates manual escalation and further work on urgency-sensitive evaluation.

### Routing threshold experiment

The notebook evaluates routing decisions using **validation** predictions from KazRoBERTa. Coverage is the fraction handled automatically; routing accuracy is computed **only over automatically routed complaints**.

| Confidence threshold | Auto-routing coverage | Accuracy among auto-routed | Manual review |
| --- | ---: | ---: | ---: |
| 0.30 | 73.33% | 88.18% | 26.67% |
| 0.60 | 56.67% | 94.12% | 43.33% |
| 0.75 | 48.00% | 97.22% | 52.00% |
| 0.85 | 28.67% | 100.00% | 71.33% |

These numbers apply to **this validation sample only**. The `0.75` threshold is a preliminary demonstration choice, and probabilities are **not calibrated**. The routing policy also flags cases with predicted high-urgency probability of at least `0.30`; this is a conservative demonstration heuristic, not a verified university policy.

## Repository contents

```text
University-Complaints-AI-Final/
├── University_Complaints_AI_Final.ipynb   # Research pipeline and results
├── requirements.txt                      # Python dependencies
├── README.md                             # Project documentation
└── .gitignore                            # Ignore models, archives and local files
```

Model weights (`.pt`), large archives, and generated outputs are intentionally excluded from ordinary Git commits. The notebook exports the trained KazRoBERTa checkpoint, tokenizer, and label mappings for use in a separate application. A public model download link can be added once the model is hosted externally (e.g., Hugging Face Hub).

## How to run the research notebook

1. Open `University_Complaints_AI_Final.ipynb` in [Google Colab](https://colab.research.google.com/).
2. Choose **T4 GPU** (or another supported CUDA GPU) for the Transformer training sections. Earlier EDA and SVM sections can run on CPU.
3. Run the first data-loading cell and **upload `university_student_complaints_dedup.csv`** when prompted. The CSV must be obtained separately; it is not included in this repository.
4. Execute the remaining cells **in order**, keeping the original train/validation/test partition. The notebook includes preprocessing, model training, evaluation, routing and model export.
5. Use the notebook's final export cell if you want the **KazRoBERTa model ZIP** for the separate application.

To install Python dependencies in a suitable local environment:

```bash
python -m pip install -r requirements.txt
```

**Reproducibility note:** The research notebook was developed in Colab. GPU availability, package versions, numerical behavior, and training randomness may affect reproduced scores. Some code cells rely on variables established by earlier cells; do not start from a middle cell in a fresh runtime. Training all four models requires the source CSV and sufficient compute resources.

## Responsible AI and limitations

- The dataset is small and includes similar phrasing across data partitions.
- High test metrics do **not** establish reliability on real university complaints, code-switching, slang, or out-of-distribution text.
- High-urgency errors remain; predictions should be reviewed by authorized staff when needed.
- Confidence values from softmax outputs are not calibrated probabilities.
- The response-time/SLA values in the routing prototype are **illustrative**, not official institutional requirements.
- Real-world deployment would require privacy safeguards, human oversight, monitoring, institutional authorization, and further testing with representative data.

## Future improvements

- Evaluate with a larger, independently collected Kazakh complaint dataset and group-aware splits.
- Compare standalone single-task Transformers against multi-task architectures.
- Perform repeated runs and uncertainty/statistical-significance analysis.
- Calibrate prediction probabilities and optimize urgent-case recall.
- Evaluate robustness on spelling mistakes, paraphrases, colloquial Kazakh, and Kazakh–Russian code-switching.
- Deploy and test the **separate Streamlit application** with documented model-loading instructions.

## Acknowledgment

This is an academic research prototype. The notebook contains the detailed experimental implementation and its accompanying introduction and conclusion. Model outputs are intended to assist, not replace, human administrative judgment.
