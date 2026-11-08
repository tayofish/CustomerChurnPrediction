
# ChurnGuard Automated Batch Prediction and Email Notifications

ChurnGuard provides two prediction methods: **Streamlit for manual single and batch predictions** and **GitHub Actions for automated batch processing**. Both use the selected model and preprocessing pipeline, generate churn risk assessments, and send email notifications for High and Critical-risk customers.

### 1. Automated Prediction Setup

The GitHub repository contains the following components:

- `.github/workflows/churnguard-predict.yml` — GitHub Actions automation.
- `scripts/predict_changed.py` — Dataset validation and churn prediction.
- `scripts/notify_risks.py` — Automated email notifications.
- `scripts/preprocessing.py` — Feature preprocessing.
- `models/churnguard_best_model.joblib` — Selected trained model and preprocessing pipeline.
- `models/feature_schema.json` — Model reference and feature definitions.

The workflow installs dependencies from `requirements.txt` and dynamically loads the model referenced in the feature schema, allowing future model replacements without changing the workflow.

### 2. Automated Prediction Workflow

New or modified CSV/XLSX datasets committed to `data_to_predict/` on the `main` branch trigger GitHub Actions. Only changed datasets are processed, while manual workflow execution supports processing all eligible datasets.

Each dataset undergoes input validation, preprocessing, and churn prediction. The system generates:

- Customer churn probabilities and four risk segments: Low, Moderate, High, and Critical.
- Probability-weighted revenue-at-risk estimates.
- Recommended retention actions.
- Prediction CSV files and `run_summary.json`.

Generated files are committed to GitHub and made available as downloadable workflow artifacts.

### 3. Automated Email Notifications

After successful prediction, `scripts/notify_risks.py` identifies newly classified High and Critical-risk customers and sends email alerts using SMTP credentials stored securely in GitHub Actions secrets.

A persistent `notification_history.json` file tracks previously notified account/risk combinations to reduce duplicate notifications across workflow runs.

Streamlit independently provides email notifications for manual predictions, using its own SQLite-based notification history.

### 4. Security and Data Management

SMTP credentials are stored in GitHub Actions secrets and are excluded from repository files. Customer datasets and prediction outputs should be maintained in a private repository with restricted access.

Notification history contains customer identifiers and must also be protected. GitHub artifact retention, access permissions, and data governance requirements should be reviewed before processing real customer information.

### 5. Testing and Validation

The automated workflow has been successfully tested, confirming model loading, dataset validation, churn prediction, revenue-at-risk calculation, prediction exports, GitHub commits, and SMTP email delivery.

Manual execution is also supported:

```bash
python -m scripts.predict_changed --all
```

GitHub Actions subsequently executes the notification script, commits generated outputs and notification history, and uploads prediction artifacts.

**Note:** GitHub Actions and Streamlit maintain separate notification histories, so the same customer may receive alerts through both channels. GitHub-based deduplication also depends on successfully committing the updated notification history.

### 6. Deployment Outcome

ChurnGuard now supports both interactive and automated churn prediction, with downloadable results and risk-based email notifications. The implementation enables repeatable customer risk assessment and provides actionable information for prioritising retention activities.
