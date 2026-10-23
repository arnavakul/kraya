# ML Evaluation Agent & SHAP Feature Attribution

This directory contains the implementation for Kraya's **Predictive Analytics & Audit-Ready Risk Scoring Engine**, integrated directly into the platform's **Evaluation Agent**.

## 1. Overview & Core Philosophy

The primary objective of this module is to deliver **explainable, multi-factor risk scoring** for supplier quote evaluation without introducing non-deterministic black-box calculations into strict financial operations.

### Key Principles:

1. **Separation of Concerns**: Non-negotiable commercial math (line-item totals, taxes, discounts, freight) is calculated deterministically in Java (`backend/`). Non-linear risk scoring, anomaly detection, and feature attributions are evaluated via machine learning in Python (`agents/`).

2. **Audit-Ready Explainability**: Rather than returning an unexplainable score, the ML engine uses **TreeSHAP (SHapley Additive exPlanations)** to break down every final score (0–100) into positive and negative point drivers (e.g., `+10.2 pts for competitive price, -5.3 pts for historical delivery delays`).

3. **Graceful Cold-Start Handling**: For brand-new suppliers with zero historical order data in PostgreSQL, feature imputation defaults to neutral baselines while weightings dynamically shift to the current quote document metrics (price alignment, warranty, payment terms).

## 2. Technical Architecture & Data Flow

```
                                [Spring Boot App Core]
                                          │
            ┌─────────────────────────────┴─────────────────────────────┐
            ▼                                                           ▼
┌──────────────────────────────┐                         ┌──────────────────────────────┐
│ Deterministic Financial Core │                         │ Feature Engineering Pipeline │
│ (Totals, Taxes, Freight)     │                         │ (Normalizes RAG & Perf Data) │
└──────────────┬───────────────┘                         └──────────────┬───────────────┘
               │                                                        │
               │                                 Engineered Vector x    │
               │                                                        ▼
               │                                         ┌──────────────────────────────┐
               │                                         │   Python ML Sidecar Service  │
               │                                         │   (FastAPI / gRPC)           │
               │                                         │   ┌────────────────────────┐ │
               │                                         │   │ XGBoost Scoring Model  │ │
               │                                         │   └───────────┬────────────┘ │
               │                                         │               │ Output       │
               │                                         │               ▼              │
               │                                         │   ┌────────────────────────┐ │
               │                                         │   │    TreeSHAP Engine     │ │
               │                                         │   └────────────────────────┘ │
               │                                         └──────────────┬───────────────┘
               │                                                        │
               └──────────────────────────┬─────────────────────────────┘
                                          ▼
                         ┌─────────────────────────────────┐
                         │   SHAP Normalizer & Persistence │
                         │      (PostgreSQL + Spring JPA)  │
                         └─────────────────────────────────┘

```

## 3. Evaluated Categories & Features

The XGBoost model assesses quotes across 5 key operational and risk dimensions:

| Category | Feature Name | Description | Source | 
| ----- | ----- | ----- | ----- | 
| **Commercial Alignment** | `price_variance_pct` | Variance between quoted price and target budget | Quote Extraction / Intake | 
|  | `tco_markup_pct` | Extra landed costs (freight, duties, line markup) | Deterministic Financial Core | 
| **Operational Reliability** | `lead_time_days_delta` | Days variance vs. requested delivery deadline | Request vs. Quote | 
|  | `historical_delay_avg_days` | Average past delivery delay (days) | PostgreSQL Order History | 
|  | `historical_defect_rate` | Historical order defect percentage | PostgreSQL Order History | 
| **Contractual Terms** | `payment_terms_penalty` | Penalty weight for policy deviation (e.g., Net 30 vs. Net 60) | Policy Engine | 
|  | `warranty_months` | Warranty duration in months | Quote Extraction | 
| **Profile & Anomaly** | `category_experience_years` | Supplier experience in category | RAG / Supplier Metadata | 
|  | `extraction_completeness_pct` | Completeness of parsed PDF quote fields | Document AI Pipeline | 
|  | `anomaly_lowball_flag` | Low-ball pricing flag (risk of mid-contract renegotiation) | Anomaly Detection Model | 

## 4. Directory Structure

```
agents/
├── evaluation/                   # Core Evaluation ML Engine
│   ├── README.md                 # System documentation (This file)
│   ├── feature_pipeline.py       # Preprocesses raw backend metrics into feature vectors
│   ├── predictor.py              # Runs XGBoost inference
│   ├── shap_engine.py            # Computes TreeSHAP attributions & ranks score impacts
│   └── router.py                 # FastAPI endpoints (/evaluations/score-and-explain)
│
├── models/                       # Serialized Model Binaries
│   └── evaluation_xgb_v1.bin     # Trained XGBoost model artifact
│
├── pydantic_models/              # Input / Output Schemas
│   └── evaluation_schemas.py     # Request / Response Pydantic models
│
├── notebooks/                    # Model Training & Experiments
│   └── train_model.py            # Synthetic transaction generator & trainer
│
└── tests/                        # Pytest Test Suites
    └── test_shap_engine.py       # Unit tests for SHAP calculation & output ranking

```

## 5. API Endpoint Reference

### `POST /evaluations/score-and-explain`

**Query Parameters:**

* `supplier_id` (string): Unique identifier for the candidate supplier.

* `quote_id` (string): Unique identifier for the submitted quote document.

**Request Body (`FeatureVector`):**

```
{
  "price_variance_pct": -0.045,
  "tco_markup_pct": 0.02,
  "lead_time_days_delta": 0.0,
  "historical_delay_avg_days": 3.8,
  "historical_defect_rate": 0.01,
  "payment_terms_penalty": 0.5,
  "warranty_months": 36.0,
  "category_experience_years": 4.5,
  "extraction_completeness_pct": 0.95,
  "anomaly_lowball_flag": 0.0
}

```

**Response Body (`EvaluationResponse`):**

```
{
  "supplier_id": "sup_99182",
  "quote_id": "q_44810",
  "final_score": 82.5,
  "baseline_score": 75.0,
  "shap_breakdown": {
    "base_value": 75.0,
    "top_positive_drivers": [
      {
        "feature_name": "price_variance_pct",
        "display_label": "Price vs. Budget Target",
        "feature_value": "-0.045",
        "shap_value": 0.204,
        "score_delta": 10.2
      },
      {
        "feature_name": "warranty_months",
        "display_label": "Warranty Duration",
        "feature_value": "36.0",
        "shap_value": 0.082,
        "score_delta": 4.1
      }
    ],
    "top_negative_drivers": [
      {
        "feature_name": "historical_delay_avg_days",
        "display_label": "Historical Delivery Delay",
        "feature_value": "3.8",
        "shap_value": -0.106,
        "score_delta": -5.3
      },
      {
        "feature_name": "payment_terms_penalty",
        "display_label": "Payment Terms Compliance",
        "feature_value": "0.5",
        "shap_value": -0.030,
        "score_delta": -1.5
      }
    ]
  }
}

```

## 6. How to Run & Test Locally

### 1. Activate Environment & Install Dependencies

From the `agents/` root directory:

```
# Activate your local virtual environment
source venv/bin/activate        # On Mac/Linux
.\venv\Scripts\Activate.ps1     # On Windows PowerShell

# Install dependencies
pip install -r requirements.txt

```

### 2. Train / Refresh the Model Artifact

Run the trainer script to generate a fresh model binary:

```
python notebooks/train_model.py

```

*Outputs: `agents/models/evaluation_xgb_v1.bin`*

### 3. Launch the FastAPI Service

Start the FastAPI app locally:

```
uvicorn agents.main:app --reload --port 8000

```

Open your browser to `http://127.0.0.1:8000/docs` to test the `/evaluations/score-and-explain` endpoint interactively via Swagger UI.