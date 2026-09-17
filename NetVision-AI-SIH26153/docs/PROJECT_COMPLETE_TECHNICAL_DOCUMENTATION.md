# NetVision AI — Complete Technical Documentation

## 1. Scope and evidence basis

This document summarizes the repository as it currently exists in the workspace and records what is implemented, what is documented but not yet embodied in the code, and what remains unverified or aspirational.

Repository evidence reviewed for this document:
- `README.md`
- `backend/app/main.py`
- `backend/app/schemas/forecast.py`
- `src/forecasting/attack_forecast.py`
- `src/features/runtime_transformer.py`
- `src/transition/state_transition.py`
- `src/mitre/attack_mapping.py`
- `src/xai/shap_explainer.py`
- `frontend/src/App.jsx`
- `frontend/src/pages/ForecastPage.jsx`
- `frontend/src/pages/ExplainPage.jsx`
- `frontend/src/pages/AttackPage.jsx`
- `tests/test_backend.py`
- `models/trained/ensemble_config.json`
- `models/forecasting/state_transition_model.json`
- `models/trained/feature_names.json`

Important rule applied in this analysis:
- No existing file was edited, overwritten, renamed, moved, or deleted.
- This file is the only newly created output for the documentation requirement.

---

## 2. Project purpose

NetVision AI is a network security forecasting system designed to estimate the current attack likelihood from a recent traffic window and project future threat evolution over multiple short horizons.

The actual code path is centered on a practical input pipeline:
1. Accept practical traffic metrics or a direct model-ready feature dictionary.
2. Transform the practical traffic values into the exact trained-feature schema.
3. Estimate current attack probability with an ensemble model.
4. Propagate the current state through a time-step world model.
5. Generate SHAP-based explanation values.
6. Correlate observed traffic patterns with MITRE ATT&CK behavioral techniques.
7. Return a unified response for the dashboard.

This is a forecasting and explainability pipeline, not a simple intrusion detector.

---

## 3. Verified system architecture

### 3.1 Backend entrypoint

`backend/app/main.py` is the API entrypoint. It does the following:
- creates a `FastAPI` application named `NetVision AI`
- defines `/` and `/health` endpoints
- exposes a POST `/forecast` endpoint
- validates a `ForecastRequest`
- loads a SHAP background dataset from `models/xai/shap_background.csv`
- instantiates `AttackForecastPipeline`

The `health` endpoint returns:
- `status: healthy`
- `ml_model: loaded`
- `world_model: loaded`
- `xai: loaded`
- `mitre_attack: loaded`

The `forecast` endpoint accepts either:
- `features` as a direct 138-feature dictionary
- `traffic` as a practical traffic dictionary
- or top-level practical fields such as `flow_count`, `forward_packets`, `flow_duration`, etc.

Key validation in `backend/app/main.py`:
- if `shap_background.shape != (50, 138)`, startup fails with a `ValueError`
- if background contains NaN values, startup fails
- the pipeline is initialized with model artifact paths and SHAP background data

### 3.2 Request validation layer

`backend/app/schemas/forecast.py` defines `ForecastRequest` with Pydantic validation.

It supports:
- model-ready direct input via `features`
- practical traffic input via `traffic`
- convenience top-level numeric input fields

Disallowed keys are explicitly blocked, including:
- `future_attack_state`
- `ground_truth`
- `model_prediction`
- `shap_values`
- `mitre_mapping`

The schema validates that all input feature values are finite numbers and rejects non-numeric or NaN/Inf values.

### 3.3 Unified forecasting pipeline

`src/forecasting/attack_forecast.py` implements `AttackForecastPipeline`, the central orchestration object.

The pipeline validates that the feature schema contains exactly 138 entries, matching the artifact list from `models/trained/feature_names.json`.

It loads and validates:
- XGBoost model: `models/trained/xgb_model.json`
- Random Forest model: `models/trained/rf_smote_model.pkl`
- feature names: `models/trained/feature_names.json`
- ensemble config: `models/trained/ensemble_config.json`
- world model: `models/forecasting/state_transition_model.json`
- SHAP background: `models/xai/shap_background.csv`

Important implementation facts:
- the ensemble config requires `xgb_weight + rf_weight = 1.0`
- the decision threshold is validated between 0 and 1
- `self.threshold` is read from the configuration and defaults to `0.40`

### 3.4 Model-ready feature schema

`models/trained/feature_names.json` defines the final schema. The actual file contains a list of 138 sorted feature names; it is the canonical model contract used by the pipeline and SHAP background compatibility checks.

The stored feature names are not generic placeholders; they correspond to the engineered packet/byte/throughput/flag/time statistics used throughout the runtime transformer and model evaluation.

### 3.5 Runtime traffic-to-feature transformation

`src/features/runtime_transformer.py` is the practical input transformation layer. It transforms a practical 5-minute traffic profile into a 1-row DataFrame with the exact 138-feature schema required by the trained models.

The transformer does all of the following:
- parses a practical traffic dictionary and normalizes field names
- applies safe division logic and default values for absent fields
- computes derived statistics for packet counts, byte totals, packet size distributions, inter-arrival timing, rates, TCP flags, ratio fields, activity/idle behavior, and header lengths
- enforces output schema order exactly according to the final feature list
- raises errors on NaN or Inf values

This is the actual bridge between operational telemetry and model input. The project documentation describes it as a correction for the earlier mismatch between practical inputs and frozen model schema.

### 3.6 Forecasting and current-state logic

The core inference logic in `AttackForecastPipeline.forecast()` is:
1. validate the 138-feature dictionary
2. compute XGBoost attack probability
3. compute Random Forest attack probability
4. compute ensemble probability
5. compare against the threshold
6. set current state to `ATTACK` if probability >= threshold, else `BENIGN`
7. request world-model forecast for horizons 10, 20, 30, 45, and 60 minutes
8. generate SHAP explanation
9. generate MITRE ATT&CK mapping

The ensemble probability formula is effectively:
- `ensemble_probability = xgb_weight * xgb_probability + rf_weight * rf_probability`

The trained config file confirms the practical weights and threshold:
- `xgb_weight`: 0.5
- `rf_weight`: 0.5
- `threshold`: 0.4

This means the ensemble is a simple 50:50 probability blend using the configured threshold.

### 3.7 World model

`src/transition/state_transition.py` implements a first-order Markov model with two states:
- `0 = BENIGN`
- `1 = ATTACK`

This is the actual implementation being used by the pipeline. It is not a five-state model.

The model:
- loads `models/forecasting/state_transition_model.json`
- validates a 2x2 matrix with rows summing to 1
- computes `k`-step forecast using matrix exponentiation
- exposes `k_step_attack_probability()` and `forecast()`

The temporal window is 5 minutes per step.

The pipeline then creates forecast points for 10, 20, 30, 45, and 60 minute horizons by using `steps = minutes / 5`.

### 3.8 Explanation and XAI behavior

`src/xai/shap_explainer.py` implements probability-space SHAP for the ensemble.

It computes:
- XGBoost SHAP values using a background dataset and TreeExplainer
- Random Forest SHAP values using the tree explainer
- weighted combination in the same probability space as the ensemble
- base expectation values and reconstructed probability estimates
- ranked contribution summaries for positive and negative impact

This is designed to explain the prediction for the exact observation window rather than to produce a separate classification model.

### 3.9 MITRE ATT&CK mapping behavior

`src/mitre/attack_mapping.py` is an evidence-based behavioral correlator.

The mapper checks for signal groups:
- `destination_diversity`
- `traffic_volume`
- `packet_rate`
- `temporal_concentration`

It has a very limited rule set in the current code:
- `T1046` — Network Service Discovery
- `T1498` — Network Denial of Service
- `T1498.001` — Direct Network Flood

The code explicitly says it is not a classifier and only returns techniques when the configured minimum number of behavioral groups are present.

### 3.10 Frontend behavior

The frontend uses a React application that interacts with the backend through HTTP calls.

`frontend/src/App.jsx` manages top-level app navigation and submits requests to the backend.

The frontend pages are implemented as:
- `ForecastPage.jsx`: current and future state forecast visualization
- `ExplainPage.jsx`: SHAP-driven explanation page
- `AttackPage.jsx`: MITRE ATT&CK correlation and evidence display

These pages are consistent with the backend response structure and show a practical dashboard-oriented interface.

---

## 4. Actual data contract and response structure

The backend returns a unified dictionary with sections like:
- `ml` or `ml_forecast`
- `world_model` or `world_model_forecast`
- `xai`
- `mitre_attack`
- plus an optional `input` block when traffic is transformed

The tests validate this contract.

`tests/test_backend.py` checks:
- `GET /` returns project metadata
- `GET /health` returns the health object
- `POST /forecast` with practical traffic succeeds
- `POST /forecast` with 138 zero features succeeds
- invalid keys like `future_attack_state` are rejected with HTTP 422

The test file also asserts exact values for a zero-feature scenario:
- `xgb_attack_probability ≈ 0.126096`
- `rf_attack_probability ≈ 0.373333`
- `ensemble_attack_probability ≈ 0.249715`

These expected numbers indicate the pipeline is not a purely hypothetical design; it is a live, tested implementation.

---

## 5. Technical notes and implementation reality

### 5.1 The runtime design is real and central

The system is intentionally structured around a practical telemetry input profile being converted into the exact model schema expected by the models. This is not optional or decorative; it is the actual runtime contract used by the backend.

The `RuntimeFeatureTransformer` code demonstrates the conversion logic from traffic-window descriptors to engineered features. It is a careful reconstruction of a 138-feature vector from aggregate traffic signals.

### 5.2 Current code is simpler than the marketing description

The project-level README describes a broader five-state Markov world model with states such as `BENIGN`, `RECONNAISSANCE`, `EXPLOITATION`, `LATERAL_MOVEMENT`, and `DENIAL_OF_SERVICE`.

The actual code uses a two-state Markov model:
- `BENIGN`
- `ATTACK`

The state transition model file also defines a 2x2 matrix, not a 5x5 matrix.

This means the repository contains a broader narrative design in the project overview, but the shipped implementation is narrower and simpler than the README implies.

### 5.3 MITRE mapping is behavioral correlation, not evidence of attack certainty

The mapper makes this clear in the code comments and logic: it is a correlation engine that maps patterns to ATT&CK techniques only when signal-group thresholds are satisfied. The output is meant to support analyst interpretation, not to prove intrusion.

### 5.4 Explainability is attached to the current prediction, not a separate classifier

The XAI layer is built around the current ensemble probability. It shows the factors contributing to the current estimate and reconstructs the same probability space. This is consistent with the project’s forecasting goal.

---

## 6. What is implemented vs what is documented vs unknown

### Implemented and verified
- FastAPI backend with `/health` and `/forecast`
- Direct feature and practical-traffic input support
- exact 138-feature schema validation
- ensemble probability blending using XGBoost and Random Forest
- threshold-based current state decision
- Markov 2-state temporal forecast with 5-minute steps and 10/20/30/45/60 minute horizons
- SHAP explanation pipeline using background data
- MITRE ATT&CK behavioral mapping with minimum evidence rules
- React UI for analyze/forecast/explain/attack views
- backend test coverage validating the key path

### Documented but not fully aligned with current code
- README claims five threat states and a five-state Markov world model
- README claims a richer broad ATT&CK mapping taxonomy and security state taxonomy
- Some narrative blocks describe a more elaborate operational architecture than the shipped model logic

### Unknown or not fully evidenced in the repository
- whether the user-facing dashboard is connected to real production telemetry in a deployment environment
- whether the trained XGBoost and Random Forest artifacts were generated from a publicly documented dataset pipeline beyond the repository code seen here
- whether the exact original dataset or label mapping beyond CIC-IDS2018 references is preserved in reproducible artifact metadata
- whether all README claims were meant as a design aspiration rather than an exact implementation statement

---

## 7. Key files for developers

These files are the best entry points for ongoing work:
- `README.md` — project overview and intended architecture
- `backend/app/main.py` — API runtime entry and bootstrap
- `backend/app/schemas/forecast.py` — request contracts and validation rules
- `src/forecasting/attack_forecast.py` — main orchestration logic
- `src/features/runtime_transformer.py` — the runtime feature mapping logic
- `src/transition/state_transition.py` — world model implementation
- `src/xai/shap_explainer.py` — explanation engine
- `src/mitre/attack_mapping.py` — ATT&CK correlation logic
- `models/trained/ensemble_config.json` — threshold and weights
- `models/forecasting/state_transition_model.json` — transition matrix definition
- `tests/test_backend.py` — direct validation of current contract

---

## 8. Recommended developer focus areas

1. Resolve the mismatch between README narrative and deployed 2-state implementation.
2. Confirm whether the five-state world model is purely aspirational or if a newer artifact is expected to replace the current 2-state Markov model.
3. Validate whether the fitted model artifact paths and SHAP background were generated from the same feature schema consistently across training and runtime.
4. Treat the MITRE mapping layer as a behavioral correlation aid rather than a ground-truth detection system.
5. If production deployment is planned, verify that `RuntimeFeatureTransformer` receives the full practical telemetry schema expected by the field validations and that real-world traffic values match the assumptions built into the derivation formulas.

---

## 9. Final assessment

The repository is a working, coherent forecasting system with a clear end-to-end implementation path:
- practical traffic input
- runtime feature construction
- 138-feature validation
- ensemble classification
- Markov forecast propagation
- SHAP explanation
- MITRE correlation
- React dashboard rendering

The strongest repository-grounded conclusion is that the actual implementation is a pragmatic, tested network attack forecasting stack designed around a 138-feature engineered schema and a 2-state temporal attack model, with a lightweight ATT&CK correlation layer and an analyst-focused explanation layer.

The main caution is that the project narrative in the root README is broader than the code and may describe a future or aspirational state rather than the exact current implementation.

This is not a defect in the codebase; it is a documentation/implementation alignment issue that a future maintainer should resolve explicitly.
