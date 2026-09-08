Phase 7 — System Integration Report
NetVision AI — AI-Based Network Attack Forecasting from Network Traffic Data

Project: SIH26153 — AI based Network Attack Forecasting from Network Traffic Data
Phase: Phase 7 — System Integration
Status: Completed
Primary components: ML Forecasting + World Model + Unified Pipeline + FastAPI Backend
Dataset: CIC-IDS2018
Temporal representation: 5-minute windows
Forecasting horizon: 10 minutes
ML ensemble: XGBoost + Random Forest with SMOTE
World Model: First-order two-state Markov model
API framework: FastAPI

1. Executive Summary

Phase 7 focused on integrating the independently developed machine-learning forecasting model and the temporal World Model into a single executable forecasting system.

The objective of this phase was not to develop a new machine-learning model. Instead, the objective was to convert the validated Phase 5 and Phase 6 research artifacts into a reproducible software pipeline that can accept model-ready network traffic features and produce:

current attack probability,
current network state,
ensemble prediction,
future attack probabilities,
multi-step forecasts from 10 to 60 minutes,
and API-accessible forecasting results.

The final system integrates:

Network Traffic Features
          ↓
     Input Validation
          ↓
   ML Forecasting Layer
      ↙           ↘
   XGBoost      Random Forest
      ↘           ↙
       50:50 Ensemble
             ↓
      Current State
             ↓
       World Model
             ↓
 Future Attack Forecasts
  10 / 20 / 30 / 45 / 60 min
             ↓
        FastAPI API

Phase 7 successfully established the backend foundation required for the later frontend, XAI, MITRE ATT&CK integration, and final validation phases.

2. Objectives of Phase 7

The main objectives were:

Integrate the final ML models into the application.
Avoid unreliable wrapper-based model serialization.
Integrate the Phase 6 state-transition World Model.
Build a unified forecasting pipeline.
Expose the forecasting functionality through a backend API.
Validate the API with valid and invalid requests.
Verify that model outputs remain consistent with Phase 5 and Phase 6 results.
Establish a stable backend foundation for subsequent phases.
3. Phase 7 Architecture

The completed Phase 7 architecture is:

                    ┌─────────────────────────┐
                    │    Network Features     │
                    │     138 ML Features     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     FastAPI Backend     │
                    │       /forecast         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Input & Schema          │
                    │ Validation              │
                    └────────────┬────────────┘
                                 │
                                 ▼
              ┌─────────────────────────────────────┐
              │        ML Forecasting Layer         │
              └────────────────┬────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌────────────────┐          ┌────────────────┐
        │    XGBoost     │          │ Random Forest  │
        │     Model      │          │    + SMOTE     │
        └───────┬────────┘          └───────┬────────┘
                │                           │
                └────────────┬──────────────┘
                             ▼
                    ┌────────────────┐
                    │ 50:50 Ensemble │
                    └───────┬────────┘
                            │
                            ▼
                  Current Attack State
                            │
                            ▼
                 ┌────────────────────┐
                 │   World Model      │
                 │ First-order Markov │
                 │      Model         │
                 └─────────┬──────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ Multi-Step Forecasting   │
              │ 10 / 20 / 30 / 45 / 60m │
              └────────────┬─────────────┘
                           │
                           ▼
                    JSON API Response
4. Model Artifact Strategy

During Phase 7, an important serialization issue was discovered.

The original Phase 5 ensemble was stored as:

netvision_final_ensemble_v1.pkl

The wrapper-based pickle depended on the Python class definition being available in the same expected module context. An attempted backend loading approach encountered an XGBoost serialization error:

input stream corrupted

Therefore, rather than relying on the complete wrapper pickle, the final backend architecture uses native model artifacts.

Final model artifacts
models/
└── trained/
    ├── xgb_model.json
    ├── rf_smote_model.pkl
    ├── feature_names.json
    ├── ensemble_config.json
    ├── netvision_final_ensemble_v1.pkl
    └── netvision_final_ensemble_v1_backend.pkl

The old .pkl files were retained temporarily as historical/reference artifacts and were not used as the primary backend model-loading mechanism.

5. Final ML Model Components

The Phase 7 backend uses the two models selected during Phase 5.

5.1 XGBoost

The XGBoost model was exported in native JSON format:

xgb_model.json

This avoids dependence on Python pickle serialization for XGBoost.

The model uses the final 138-feature schema established during Phase 5.

5.2 Random Forest with SMOTE

The second component is:

rf_smote_model.pkl

This is the Random Forest model trained using SMOTE on the training data.

The model successfully loaded in the Windows backend environment and successfully generated predictions.

A scikit-learn version warning was observed because the model was serialized under scikit-learn 1.6.1 and loaded under 1.9.0.

The warning was:

InconsistentVersionWarning

Despite this warning:

the model loaded successfully,
the expected 138-feature structure was available,
predictions were successfully generated,
and the integrated ensemble produced the expected output.

This compatibility consideration should be documented and potentially resolved through environment pinning or controlled reserialization in a later maintenance step.

6. Feature Schema

The final ML model expects:

138 features

The exact feature order is stored separately in:

models/trained/feature_names.json

This is important because tree-based models require the inference features to correspond to the same feature representation used during training.

The backend therefore does not simply accept arbitrary columns.

It validates:

missing features,
unexpected features,
numerical values,
and the expected feature schema.
7. Ensemble Configuration

The final ensemble uses:

XGBoost + Random Forest-SMOTE

with equal probability weights:

XGBoost weight = 0.50
Random Forest weight = 0.50

The ensemble probability is:

$$ P_{ensemble} = 0.5P_{XGB} + 0.5P_{RF} $$

The final classification threshold selected during Phase 5 is:

$$ Threshold = 0.40 $$

Therefore:

If ensemble probability >= 0.40
        → ATTACK

If ensemble probability < 0.40
        → BENIGN

The configuration is stored in:

models/trained/ensemble_config.json
8. Phase 7.1 — ML Model Integration
Objective

The objective of Phase 7.1 was to load the final trained ML components independently and verify that they could produce predictions outside the original Colab environment.

Implemented components
XGBoost native JSON model loading
Random Forest joblib loading
feature schema loading
ensemble configuration loading
probability prediction
ensemble probability calculation
threshold-based current-state prediction
8.1 XGBoost Loading Test

The native XGBoost artifact:

xgb_model.json

was successfully loaded in the local Windows environment.

Result:

XGBoost model loaded successfully
138 features
8.2 Random Forest Loading Test

The Random Forest artifact:

rf_smote_model.pkl

was successfully loaded.

Result:

Random Forest model loaded successfully
138 features

A version compatibility warning was generated, but the model remained operational.

8.3 Prediction Test

A zero-valued 138-feature input was used for a controlled inference test.

The Random Forest produced:

Attack probability = 0.37333333333333335
Predicted class = 0

The XGBoost model produced:

Attack probability = 0.12609592080116272

The ensemble therefore produced:

$$ 0.5(0.12609592)+0.5(0.37333333) $$

which gives:

0.24971462706724804

Since:

0.2497 < 0.40

the resulting state is:

BENIGN
9. Phase 7.2 — World Model Integration

The Phase 6 World Model was integrated into the application.

The model is a:

First-order two-state Markov transition model

with:

0 = BENIGN
1 = ATTACK

The transition matrix is:

$$ P = \begin{bmatrix} 0.97042254 & 0.02957746\\ 0.06810036 & 0.93189964 \end{bmatrix} $$

where rows represent the current state and columns represent the next state.

Therefore:

BENIGN → BENIGN
0.97042254
BENIGN → ATTACK
0.02957746
ATTACK → BENIGN
0.06810036
ATTACK → ATTACK
0.93189964
10. World Model Software Implementation

The integration was implemented through:

src/transition/state_transition.py

with the main class:

StateTransitionModel

The implementation:

loads the transition model JSON,
reads the state space,
reads transition probabilities,
constructs the transition matrix,
validates that transition rows sum to 1,
performs one-step forecasting,
performs k-step forecasting.
11. World Model Verification

The integrated implementation reproduced the Phase 6 transition probabilities.

BENIGN → ATTACK
0.0295774648
ATTACK → ATTACK
0.9318996416

For a 10-minute forecast:

2 steps × 5 minutes

the model produced:

Starting from BENIGN
Attack probability = 0.0562658672
Starting from ATTACK
Attack probability = 0.8704511779

These values match the Phase 6 World Model calculations.

12. Phase 7.3 — Unified Forecasting Pipeline

The next objective was to combine the ML and World Model components.

The unified pipeline was implemented in:

src/forecasting/attack_forecast.py

using:

AttackForecastPipeline
13. Unified Forecasting Logic

The complete process is:

Input Features
      ↓
Validate 138 features
      ↓
XGBoost prediction
      ↓
Random Forest prediction
      ↓
50:50 probability ensemble
      ↓
Apply 0.40 threshold
      ↓
Current state
      ↓
Pass state to World Model
      ↓
Calculate k-step transition probabilities
      ↓
10 / 20 / 30 / 45 / 60 minute forecasts
14. Forecast Horizons

The unified pipeline provides five forecast horizons:

Horizon	Number of 5-min steps
10 minutes	2
20 minutes	4
30 minutes	6
45 minutes	9
60 minutes	12

The World Model uses matrix powers:

$$ P^k $$

to obtain the state distribution after \(k\) future steps.

15. Unified Pipeline Verification

A controlled zero-feature input was passed through the complete pipeline.

ML output
XGB attack probability:
0.12609592080116272

RF attack probability:
0.37333333333333335

Ensemble attack probability:
0.24971462706724804

Current state:

BENIGN

The World Model then generated the following forecast:

Horizon	Future attack probability
10 min	0.056266
20 min	0.102077
30 min	0.139375
45 min	0.182740
60 min	0.214599

Thus, the unified pipeline successfully connected the ML prediction with temporal state forecasting.

16. Phase 7.4 — Backend API

The backend was implemented using:

FastAPI

Project structure:

backend/
└── app/
    ├── __init__.py
    ├── main.py
    └── schemas/
        ├── __init__.py
        └── forecast.py
17. API Endpoints

Three main endpoints were implemented.

17.1 Root Endpoint
GET /

Response:

{
  "project": "NetVision AI",
  "status": "running",
  "service": "Network Attack Forecasting"
}
17.2 Health Endpoint
GET /health

Response:

{
  "status": "healthy",
  "ml_model": "loaded",
  "world_model": "loaded"
}

This confirms that both major forecasting components are available to the backend.

17.3 Forecast Endpoint
POST /forecast

The request structure is:

{
  "features": {
    "feature_name_1": 0.0,
    "feature_name_2": 0.0,
    "...": 0.0
  }
}

The current Phase 7 API expects the 138 model-ready features.

18. Backend Request Validation

The request schema is implemented using Pydantic:

class ForecastRequest(BaseModel):
    features: Dict[str, float]

This ensures that feature values are expected to be numerical.

The forecasting pipeline additionally checks:

missing features,
unexpected features,
numerical validity,
NaN/Inf conditions,
feature schema consistency.
19. Phase 7.5 — Backend Testing

Multiple backend tests were performed.

Test 1 — Missing Features

A request containing only:

{
  "features": {
    "Flow Duration": 0.0
  }
}

was submitted.

The backend correctly returned:

HTTP 422

with a detailed list of missing features.

Result

PASS

This proves that incomplete model input is rejected instead of being silently passed to the ML model.

20. Test 2 — Unexpected Feature

A complete 138-feature dictionary was created and an additional:

fake_feature

was deliberately inserted.

The backend returned:

HTTP 422
Result

PASS

This confirms that the backend does not accept arbitrary feature names.

21. Test 3 — Invalid Data Type

The request contained:

{
  "features": {
    "Flow Duration": "hello"
  }
}

FastAPI/Pydantic returned:

{
  "detail": [
    {
      "type": "float_parsing",
      "loc": [
        "body",
        "features",
        "Flow Duration"
      ],
      "msg": "Input should be a valid number, unable to parse string as a number",
      "input": "hello"
    }
  ]
}
Result

PASS

This confirms that invalid non-numerical values are rejected at the API validation layer.

22. Test 4 — Complete Valid Request

A complete 138-feature request containing zero values was submitted.

The backend successfully returned the complete ML + World Model result.

ML response
{
  "xgb_attack_probability": 0.12609592080116272,
  "rf_attack_probability": 0.37333333333333335,
  "ensemble_attack_probability": 0.24971462706724804,
  "current_state": 0,
  "current_state_label": "BENIGN"
}
World Model response
10 min → 0.056266
20 min → 0.102077
30 min → 0.139375
45 min → 0.182740
60 min → 0.214599
Result

PASS

23. Phase 7 Validation Summary
Component	Validation	Result
XGBoost loading	Native JSON load	✅ PASS
Random Forest loading	Joblib load	✅ PASS
Feature schema	138 features	✅ PASS
Ensemble	50:50 probability	✅ PASS
Threshold	0.40	✅ PASS
World Model loading	JSON	✅ PASS
Transition matrix	Reproduced Phase 6	✅ PASS
k-step forecasting	2–12 steps	✅ PASS
Unified pipeline	ML → World Model	✅ PASS
FastAPI startup	Uvicorn	✅ PASS
/ endpoint	API test	✅ PASS
/health	API test	✅ PASS
Missing features	HTTP 422	✅ PASS
Unexpected features	HTTP 422	✅ PASS
Invalid datatype	HTTP 422	✅ PASS
Complete forecast	HTTP 200	✅ PASS
24. Final Phase 7 Software Structure

The relevant project structure after Phase 7 is:

NetVision-AI-SIH26153/
│
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       └── schemas/
│           ├── __init__.py
│           └── forecast.py
│
├── models/
│   ├── trained/
│   │   ├── xgb_model.json
│   │   ├── rf_smote_model.pkl
│   │   ├── feature_names.json
│   │   ├── ensemble_config.json
│   │   ├── netvision_final_ensemble_v1.pkl
│   │   └── netvision_final_ensemble_v1_backend.pkl
│   │
│   └── forecasting/
│       ├── phase6_final_configuration.json
│       ├── state_transition_matrix.csv
│       ├── state_transition_model.json
│       ├── multi_step_forecasting_config.json
│       ├── future_state_simulation_config.json
│       └── k_step_forecasting_config.json
│
├── src/
│   ├── forecasting/
│   │   └── attack_forecast.py
│   │
│   └── transition/
│       └── state_transition.py
│
└── ...
25. Important Design Decision — Current API Input

A key limitation of the current Phase 7 API should be clearly documented.

The current endpoint accepts:

138 model-ready temporal features

It does not yet accept a simple human-friendly network traffic form.

This is intentional.

The Phase 4 representation transforms raw network traffic into temporal window-level features. The final frontend should eventually provide practical traffic/network information and the backend should perform the required transformation before inference.

Therefore:

CURRENT PHASE 7

138 model-ready features
        ↓
FastAPI
        ↓
ML + World Model

Later:

FINAL SYSTEM

User-friendly traffic form
        ↓
Backend preprocessing /
feature construction
        ↓
138 model-ready features
        ↓
ML + World Model
        ↓
Forecast + XAI + MITRE
        ↓
Frontend dashboard

This frontend/input abstraction is deliberately deferred until the later integration stages are finalized.

26. Important Serialization Decision

The original complete ensemble pickle was not selected as the primary backend artifact because of the serialization compatibility problem encountered with the XGBoost component.

The final strategy is therefore:

XGBoost
   ↓
Native JSON

Random Forest
   ↓
Joblib/Pickle

Feature Schema
   ↓
JSON

Ensemble Configuration
   ↓
JSON

World Model
   ↓
JSON

This makes each component independently loadable and easier to debug.

27. Reproducibility

Phase 7 uses configuration and model artifacts rather than hidden notebook state.

The backend explicitly loads:

xgb_model.json
rf_smote_model.pkl
feature_names.json
ensemble_config.json
state_transition_model.json

This allows the forecasting pipeline to be reproduced outside the original Colab experimentation environment.

28. Limitations Identified

The following limitations were identified during Phase 7.

28.1 Current API uses model-ready features

The API currently requires 138 temporal features rather than raw user-friendly traffic inputs.

This will be addressed during the later frontend/backend integration stage.

28.2 Random Forest version warning

The Random Forest was trained/serialized using scikit-learn 1.6.1 and currently loaded under scikit-learn 1.9.0.

The model successfully loads and predicts, but environment pinning or controlled reserialization should be considered for production deployment.

28.3 Phase 7 is not the final user interface

No frontend was developed in this phase.

The purpose of Phase 7 was backend and model integration.

28.4 XAI is not yet integrated

Explainability is intentionally reserved for:

Phase 8 — XAI + MITRE ATT&CK

28.5 MITRE ATT&CK mapping is not yet integrated

MITRE ATT&CK technique mapping will be implemented in Phase 8.

29. Research-to-Engineering Continuity

Phase 7 preserves the outputs of previous phases.

Phase 1
Dataset Investigation
       ↓
Phase 2
Data Cleaning
       ↓
Phase 3
Feature Engineering
       ↓
Phase 4
Temporal Representation
       ↓
Phase 5
ML Forecasting
       ↓
Phase 6
World Model
       ↓
Phase 7
System Integration
       ↓
Phase 8
XAI + MITRE ATT&CK
       ↓
Phase 9
Final Validation
       ↓
Frontend + Final Demonstration

Therefore, Phase 7 is not an independent software project. It is the engineering integration of the research pipeline developed across Phases 1–6.

30. Final Outcome

Phase 7 successfully transformed the independently validated ML and World Model components into a working backend forecasting system.

The final system can:

Accept model-ready network traffic features.
Validate the input schema.
Generate XGBoost attack probability.
Generate Random Forest attack probability.
Calculate the 50:50 ensemble probability.
Determine the current network state using the 0.40 threshold.
Pass the current state to the World Model.
Generate future attack probabilities.
Produce forecasts for 10, 20, 30, 45 and 60 minutes.
Expose the entire pipeline through a FastAPI endpoint.
Reject malformed, incomplete, or unexpected requests.

The core integrated pipeline is therefore:

                INPUT
                  │
                  ▼
        138 Network Features
                  │
                  ▼
        ┌───────────────────┐
        │   FastAPI Backend │
        └─────────┬─────────┘
                  │
                  ▼
          Input Validation
                  │
                  ▼
        ┌───────────────────┐
        │   ML Ensemble     │
        │                   │
        │ XGBoost + RF      │
        │      50:50        │
        └─────────┬─────────┘
                  │
                  ▼
       Current Attack State
                  │
                  ▼
        ┌───────────────────┐
        │    World Model    │
        │  Markov Transition│
        └─────────┬─────────┘
                  │
                  ▼
        Future Attack Risk
                  │
        ┌─────────┼──────────┐
        ▼         ▼          ▼
      10 min    30 min     60 min
        │         │          │
        └─────────┼──────────┘
                  ▼
             JSON Response
31. Phase 7 Completion Statement

Phase 7 — System Integration is completed.

The final ML forecasting models and Phase 6 World Model have been successfully integrated into a unified forecasting pipeline and exposed through a validated FastAPI backend.

The integrated system reproduces the expected ML ensemble and World Model outputs, while backend validation successfully handles incomplete, unexpected, and invalid requests.

The system is now ready for the next research and engineering stage:

Phase 8 — Explainable AI (XAI) + MITRE ATT&CK Integration.