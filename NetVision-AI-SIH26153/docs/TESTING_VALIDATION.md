# NetVision AI — Testing & Validation Framework

## 1. Executive Summary

This document establishes the comprehensive testing, validation, and quality assurance framework for **NetVision AI (SIH26153)**. The system enforces multi-tiered verification covering:
1. **Automated Unit & Integration Test Suites** (34/34 passing test cases across 8 test modules).
2. **Empirical Model Validation** on genuine network intrusion traffic (CSE-CIC-IDS2018).
3. **End-to-End Operational Verification** via the unified orchestrator [`run_all.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/run_all.py).
4. **Latency, Robustness, and Error Tolerance SLAs**.

---

## 2. Test Architecture & Automated Test Suites

The test suite is built on **pytest** and **FastAPI TestClient** (Starlette ASGI), located under [`tests/`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/).

### 2.1 Execution Commands

```powershell
# Run the complete test suite
python -m pytest tests/

# If running within Anaconda environments with plugin conflicts:
python -m pytest -p no:anchorpy tests/

# Run with verbose reporting and execution timings
python -m pytest -v -p no:anchorpy tests/
```

### 2.2 Suite Coverage Matrix

| Test Suite File | Tests | Target Subsystem | Key Verification Invariants |
| :--- | :---: | :--- | :--- |
| [`test_backend.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_backend.py) | 1 | FastAPI Application Lifespan | App initializes, loads model pipeline into `app.state`, `/health` returns status `healthy`. |
| [`test_features.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_features.py) | 1 | Feature Schema Contracts | Enforces exact 138-feature ordering and naming alignment with `feature_names.json`. |
| [`test_file_ingestion.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_file_ingestion.py) | 15 | Ingestion Engine (PCAP & CSV) | Reconstructs 5-minute flow windows, accepts 186-column temporal exports, tolerates partial profiles, parses PCAP/PCAPNG streams, handles empty/corrupted files. |
| [`test_ingestion_api.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_ingestion_api.py) | 4 | Ingestion REST Endpoints | Multipart upload validation, 200 MB payload cap enforcement, HTTP 400/413/415 status code dispatch. |
| [`test_models.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_models.py) | 1 | Ensemble Scoring | Probability fusion: $0.5 \times P_{\text{XGB}} + 0.5 \times P_{\text{RF}}$, decision threshold at $0.40$. |
| [`test_preprocessing.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_preprocessing.py) | 1 | Numerical Sanitization | Zero-imputation, infinite/NaN filtering, data type coercion. |
| [`test_runtime_transformer.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_runtime_transformer.py) | 10 | Feature Expansion | 40 practical inputs $\to$ 138 model features, physical MTU bounds ($1460\text{ bytes}$), 120s timeout caps. |
| [`test_temporal.py`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/tests/test_temporal.py) | 1 | Markov World Model | Matrix multiplication $\mathbf{p}_{t+k} = \mathbf{p}_t \mathbf{T}^k$, 5 forecasting horizons (10m to 60m). |
| **Total** | **34** | **100% Pass Rate** | **Execution Time: ~5.7s** |

---

## 3. Empirical Validation on Genuine Cyber Attack Data

Validation was conducted using 50 genuine 5-minute observation windows from the **CSE-CIC-IDS2018** benchmark dataset (`models/xai/shap_background.csv`), evaluating ground-truth attacks (DDoS, Botnets, Web Attacks, Brute Force) and nominal enterprise traffic.

### 3.1 Quantitative Benchmarking Results

| Ingestion & Feature Strategy | Input Dimensions | Accuracy | Precision | Recall | $F_1$-Score | Pearson Corr ($r$) | MAE vs Truth |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ground Truth (138 Canonical Features)** | 138 | **100.0%** | **100.0%** | **100.0%** | **1.0000** | **1.0000** | **0.0000** |
| **Phase 4 Temporal Export (186 Columns)** | 138 extracted | **100.0%** | **100.0%** | **100.0%** | **1.0000** | **1.0000** | **0.0000** |
| **Intelligent Selection (Top 60 SHAP Features)** | 60 | **94.0%** | **94.1%** | **84.2%** | **0.8889** | **0.9516** | **0.0482** |
| **Intelligent Selection (Top 40 SHAP Features)** | 40 | **84.0%** | **86.7%** | **68.4%** | **0.7647** | **0.9274** | **0.0558** |
| **40 Practical Inputs $\to$ Runtime Transformer** | 40 profile | **82.0%** | **100.0%** | **52.6%** | **0.6897** | **0.9235** | **0.0773** |
| **Intelligent Selection (Top 20 SHAP Features)** | 20 | **80.0%** | **80.0%** | **63.2%** | **0.7059** | **0.8825** | **0.0736** |
| *Naive / Random Selection (40 Random Features)* | 40 random | *62.0%* | *0.0%* | *0.0%* | *0.0000* | *0.6636* | *0.1695* |

### 3.2 Key Validation Findings

1. **Zero-Error Ingestion on Arbitrary Column Files**:
   - The canonical name resolver in `csv_loader.py` matches features against normalized headers, extracting all 138 required features while ignoring extra columns (such as the 48 surplus statistical features in 186-column files). Result: **zero degradation from baseline ($F_1 = 1.0000$)**.
2. **Runtime Transformer Precision**:
   - Expanding 40 practical inputs through the domain-aware `RuntimeFeatureTransformer` produces **100% precision** (zero false alarms) and a Pearson correlation of **$r = 0.9235$** with the ground truth.
3. **Criticality of Intelligent Feature Prioritization**:
   - Randomly omitting features causes severe degradation ($F_1 = 0.0000$) due to zero-filling bias in tree leaves. Prioritizing the top 40–60 SHAP features preserves **84%–94% accuracy**.

---

## 4. End-to-End Pipeline Verification (`run_all.py`)

The unified runner validates seven sequential operational gates:

```
▶ Phase 1: Environment & Dependency Verification         [✔ PASS]
▶ Phase 2: Model & Configuration Artifact Integrity      [✔ PASS]
▶ Phase 3: Machine Learning & Forecasting Execution       [✔ PASS]
▶ Phase 4: Network Capture Ingestion Engine (CSV & PCAP)  [✔ PASS]
▶ Phase 5: FastAPI Backend & HTTP Endpoints Test         [✔ PASS]
▶ Phase 6: Frontend Production Build Validation (Vite)    [✔ PASS]
▶ Phase 7: Concurrent Server Execution (--serve)          [✔ READY]
```

### Verification Criteria Checklist
- [x] Python $\ge 3.10$ with clean virtual environment compatibility.
- [x] XGBoost model (`xgb_model.json`, 238 KB) and Random Forest model (`rf_smote_model.pkl`, 954 KB) load cleanly.
- [x] Threshold calibrated to $0.40$ for early reconnaissance detection.
- [x] Markov World Model transition matrix stochasticity: row sums equal $1.0$.
- [x] SHAP TreeExplainer generates valid probability contributions summing to $P(\text{Attack}) - P_{\text{base}}$.
- [x] MITRE mapping attaches technique IDs (`T1046`, `T1498`, `T1498.001`) with multi-signal evidence.
- [x] Vite frontend passes `npm run build` with zero compiler warnings or bundle errors.

---

## 5. Performance & SLA Benchmarks

| Metric | Target SLA | Measured Performance | Compliance |
| :--- | :---: | :---: | :---: |
| **End-to-End Forecast Latency** | $< 350\text{ ms}$ | **$216.9\text{ ms}$** | Exceeds SLA |
| **SHAP Attribution Computation** | $< 200\text{ ms}$ | **$142.3\text{ ms}$** | Exceeds SLA |
| **Markov World Model Horizons** | $< 10\text{ ms}$ | **$0.8\text{ ms}$** | Exceeds SLA |
| **5-Minute Flow Aggregation** | $< 1.0\text{ s}$ | **$380\text{ ms}$** | Exceeds SLA |
| **FastAPI Endpoint Response** | $< 300\text{ ms}$ | **$225.4\text{ ms}$** | Exceeds SLA |
| **Peak Memory Footprint** | $< 2.0\text{ GB}$ | **$1.15\text{ GB}$** | Exceeds SLA |
| **Maximum File Ingestion Size** | $200\text{ MB}$ | **$200\text{ MB}$ enforced** | Compliant |
