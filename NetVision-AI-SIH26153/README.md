# NetVision AI — AI-Based Network Attack Forecasting System

**Problem Statement ID:** SIH26153  
**Problem Statement:** AI-Based Network Attack Forecasting from Network Traffic Data  
**Theme:** Blockchain & Cybersecurity  
**Category:** Software (Smart India Hackathon 2026)  

---

## 1. Project Overview

**NetVision AI** is a next-generation predictive network security intelligence platform. Traditional Intrusion Detection Systems (IDS) operate reactively by asking:  
> *"Is an attack happening right now?"*

NetVision AI shifts the security paradigm from reactive detection to **proactive temporal forecasting**, asking:  
> *"Based on current network flow dynamics and historical state transitions, is an attack likely to escalate in the next 10 to 60 minutes?"*

The system processes 15 operational network flow attributes, expands them into 138 engineered features using a runtime feature transformer, evaluates current threat status via an **XGBoost + Random Forest-SMOTE Ensemble**, projects future threat progression using a **Discrete-Time Markov World Model**, explains key risk drivers via **SHAP (SHapley Additive exPlanations)**, and maps predicted attack patterns to actionable **MITRE ATT&CK** tactics and techniques.

---

## 2. Key Capabilities

- **15-Field Practical Input Surface**: Operational network flow parameters (packets, bytes, flow rates, flag counts, distinct ports/protocols) mapped live to model features.
- **Runtime Feature Engineering**: Automated 138-feature expansion calculating packet/byte ratios, flow rates, flag densities, and statistical moments without raw PCAP overhead.
- **XGBoost + Random Forest-SMOTE Ensemble**: Calibrated ensemble classifier operating at a optimal `0.40` decision threshold for maximum recall on minority attack classes.
- **Discrete-Time Markov World Model**: Multi-horizon predictive state modeling across **10m, 20m, 30m, 45m, and 60m** timeframes across 5 discrete threat states (`BENIGN`, `RECONNAISSANCE`, `EXPLOITATION`, `LATERAL_MOVEMENT`, `DENIAL_OF_SERVICE`).
- **Explainable AI (SHAP)**: Real-time calculation of positive and negative feature attribution scores to explain model predictions to SOC analysts.
- **MITRE ATT&CK Alignment**: Dynamic correlation mapping predicted attack vectors to industry-standard Tactics (e.g., *Impact*, *Reconnaissance*) and Techniques (e.g., *T1498 - Network Denial of Service*, *T1595 - Active Scanning*).
- **Modern Interactive Dashboard**: High-contrast, responsive React interface built with custom glassmorphism design system, interactive Recharts visualization, and dynamic API synchronization.

---

## 3. System Architecture

```
                    ┌─────────────────────────────────────────┐
                    │          React 18 Web Dashboard         │
                    │        (Vite + Custom CSS + Recharts)   │
                    └────────────────────┬────────────────────┘
                                         │ HTTP POST /forecast
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │             FastAPI Backend             │
                    │         (Uvicorn + Pydantic v2)         │
                    └────────────────────┬────────────────────┘
                                         │ 15 Flow Inputs
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │       Runtime Feature Transformer       │
                    │   (Expands 15 inputs to 138 features)   │
                    └────────────────────┬────────────────────┘
                                         │ 138 Features
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │   XGBoost + RF-SMOTE Ensemble Model   │
                    │      (Calibrated Threshold: 0.40)       │
                    └─────────┬──────────────────────┬────────┘
                              │                      │
       Current Threat State   │                      │ Feature Matrix
                              ▼                      ▼
           ┌──────────────────────┐      ┌──────────────────────┐
           │  Markov World Model  │      │  SHAP XAI Engine     │
           │ (10m–60m Horizons)   │      │ (Feature Attribution)│
           └──────────┬───────────┘      └───────────┬──────────┘
                      │                              │
                      └──────────────┬───────────────┘
                                     │ Forecast + SHAP Scores
                                     ▼
                    ┌─────────────────────────────────────────┐
                    │      MITRE ATT&CK Correlation Engine    │
                    │   (Maps vector to Tactics & Tech IDs)   │
                    └────────────────────┬────────────────────┘
                                         │ Unified Response
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │ React UI State Render (No Static Mocks) │
                    └─────────────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Frontend** | React 18, Vite, Recharts, Lucide React, Custom Glassmorphism CSS |
| **Backend Framework** | Python 3.13, FastAPI, Uvicorn, Pydantic v2, Pytest |
| **Machine Learning** | Scikit-learn, XGBoost, Imbalanced-learn (SMOTE), Joblib, NumPy, Pandas |
| **Explainability (XAI)** | SHAP (SHapley Additive exPlanations) |
| **Security Framework** | MITRE ATT&CK v14 Knowledge Base Mapping |
| **Testing & CI** | Pytest, Vite Build Validator |

---

## 5. Machine Learning Pipeline & Dataset

### Dataset: CIC-IDS2018
The models were trained and validated on the benchmark **CIC-IDS2018** network intrusion dataset, capturing diverse traffic conditions across benign state operations, Reconnaissance (Port Scans), Exploitation, and Denial of Service (DoS/DDoS) scenarios.

### Feature Engineering (`RuntimeFeatureTransformer`)
The input interface collects 15 core telemetry attributes:
1. `flow_count`: Active concurrent flows
2. `unique_dst_ports`: Distinct target ports contacted
3. `unique_protocols`: Distinct IP protocols observed
4. `forward_packets`: Total packets sent forward
5. `forward_bytes`: Total payload bytes sent forward
6. `backward_packets`: Total packets received backward
7. `backward_bytes`: Total payload bytes received backward
8. `flow_duration`: Flow duration (microseconds)
9. `flow_bytes_per_sec`: Data throughput rate
10. `flow_packets_per_sec`: Packet transmission rate
11. `backward_packets_per_sec`: Return packet rate
12. `syn_flag_cnt`: SYN flag frequency
13. `ack_flag_cnt`: ACK flag frequency
14. `rst_flag_cnt`: RST flag frequency
15. `fin_flag_cnt`: FIN flag frequency

The runtime transformer dynamically computes 123 derived statistics (mean packet sizes, flag ratios, flow ratios, header density metrics) to construct the complete **138-feature vector** expected by the pre-trained ML models.

### Model Architecture
- **XGBoost Classifier**: Optimized gradient boosting tree model trained on log-loss objective.
- **Random Forest with SMOTE**: Random Forest classifier trained on oversampled minority attack instances to handle extreme class imbalance.
- **Ensemble Fusion**: Weighted probability averaging between XGBoost and RF-SMOTE.
- **Decision Threshold**: Calibrated at `0.40`. Probabilities $\ge 0.40$ classify the network state as `ATTACK` (or specific attack sub-types), ensuring high sensitivity for security threats.

---

## 6. Temporal Markov World Model

The system incorporates a **Discrete-Time Markov Chain (DTMC)** transition matrix trained on sequential network window transitions:

$$P_{ij} = P(S_{t+1} = j \mid S_t = i)$$

Where state space $S \in \{\text{BENIGN}, \text{RECONNAISSANCE}, \text{EXPLOITATION}, \text{LATERAL\_MOVEMENT}, \text{DENIAL\_OF\_SERVICE}\}$.

Given initial state distribution $\pi(t)$ derived from current ML ensemble confidence scores, future probabilities for horizon $h \in \{10\text{m}, 20\text{m}, 30\text{m}, 45\text{m}, 60\text{m}\}$ are computed via matrix exponentiation:

$$\pi(t + h) = \pi(t) \cdot P^{k_h}$$

This allows NetVision AI to output probabilistic forecasting timelines showing how threat risk evolves over time.

---

## 7. Explainable AI & MITRE ATT&CK Integration

### SHAP Feature Attribution
For every inference request, the SHAP engine calculates feature impact values relative to background traffic distribution (`shap_background.csv`). The top positive drivers (increasing attack risk) and negative drivers (stabilizing factors) are formatted into human-readable explanations.

### MITRE ATT&CK Mapping
Detected attack behaviors are automatically cross-referenced against MITRE ATT&CK techniques:
- **Denial of Service (`DENIAL_OF_SERVICE`)**: Mapped to **T1498** (Network Denial of Service) under *Impact*.
- **Reconnaissance (`RECONNAISSANCE`)**: Mapped to **T1595** (Active Scanning) under *Reconnaissance*.
- **Exploitation (`EXPLOITATION`)**: Mapped to **T1190** (Exploit Public-Facing Application) under *Initial Access*.
- **Lateral Movement (`LATERAL_MOVEMENT`)**: Mapped to **T1021** (Remote Services) under *Lateral Movement*.

---

## 8. Repository Structure

```
NetVision-AI-SIH26153/
├── backend/                  # FastAPI Application Server
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint & CORS setup
│   │   ├── api/
│   │   │   └── forecast.py   # POST /forecast endpoint
│   │   └── schemas/
│   │       └── forecast.py   # Pydantic v2 validation models
│   └── README.md
├── frontend/                 # React 18 + Vite Web Dashboard
│   ├── src/
│   │   ├── components/
│   │   │   ├── layout/       # Navbar, Footer, Section wrappers
│   │   │   └── product/      # TrafficForm, Results, ForecastPlot, XaiExplanation
│   │   ├── pages/            # Hero, About, Analyze, Forecast, Explainability pages
│   │   ├── services/
│   │   │   └── api.js        # Axios REST client to backend
│   │   ├── App.jsx           # Main state manager & section orchestrator
│   │   └── index.css         # Global design system & theme tokens
│   └── package.json
├── models/                   # Pre-trained ML Artifacts (UNMODIFIED)
│   ├── trained/
│   │   ├── xgb_model.json
│   │   ├── rf_smote_model.pkl
│   │   ├── feature_names.json
│   │   └── ensemble_config.json
│   ├── state_transition_model.json
│   └── shap_background.csv
├── src/                      # Core Python Processing Packages
│   ├── features/
│   │   └── runtime_transformer.py
│   ├── temporal/
│   │   └── markov_model.py
│   ├── mitre/
│   │   └── mapper.py
│   └── xai/
│       └── shap_explainer.py
├── tests/                    # Pytest Suite (5 Modules)
│   ├── test_backend.py
│   ├── test_features.py
│   ├── test_models.py
│   ├── test_preprocessing.py
│   └── test_temporal.py
├── requirements.txt          # Python dependencies
└── README.md                 # Project Documentation
```

---

## 9. Setup & Installation

### Prerequisites
- **Python**: 3.11+ (Python 3.13 recommended)
- **Node.js**: v18+ and `npm`

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/PrakulPShetty/NetVision-AI-SIH26153.git
cd NetVision-AI-SIH26153/NetVision-AI-SIH26153

# Create & activate a Python virtual environment
python -m venv .venv313
# Windows (PowerShell):
.venv313\Scripts\Activate.ps1
# Linux/macOS:
source .venv313/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend
npm install
```

---

## 10. Running the Application

### Option A: Run Backend Server
From the project root:
```bash
.venv313\Scripts\python.exe -m uvicorn backend.app.main:app --port 8000 --host 127.0.0.1 --reload
```
The FastAPI backend will start at `http://127.0.0.1:8000`.  
Interactive API docs are available at `http://127.0.0.1:8000/docs`.

### Option B: Run Frontend Dev Server
From the `frontend/` directory:
```bash
npm run dev
```
The React web dashboard will launch at `http://localhost:3000`.

---

## 11. API Endpoints

### 1. Health Check
- **`GET /health`**
- **Response**: `{"status": "ok", "service": "NetVision AI API"}`

### 2. Traffic Forecast Inference
- **`POST /forecast`**
- **Request Body**:
```json
{
  "traffic": {
    "flow_count": 150,
    "unique_dst_ports": 45,
    "unique_protocols": 2,
    "forward_packets": 1200,
    "forward_bytes": 85000,
    "backward_packets": 1100,
    "backward_bytes": 78000,
    "flow_duration": 5000000,
    "flow_bytes_per_sec": 32600.0,
    "flow_packets_per_sec": 460.0,
    "backward_packets_per_sec": 220.0,
    "syn_flag_cnt": 80,
    "ack_flag_cnt": 150,
    "rst_flag_cnt": 5,
    "fin_flag_cnt": 10
  }
}
```
- **Response Schema**: `ForecastResponse`
  - `current_assessment`: Object containing `predicted_class`, `attack_probability`, `threshold_used` (`0.40`), `ensemble_breakdown`.
  - `forecast_timeline`: Array of predictions for horizons `[10, 20, 30, 45, 60]` minutes.
  - `xai_explanation`: Object containing top positive and negative SHAP feature contributions.
  - `mitre_correlation`: Object containing mapped tactic, technique ID, technique name, and mitigation guidance.

---

## 12. Testing & Verification

### Automated Backend Tests
Run the complete Pytest suite to verify feature transformation, ML model loading, Markov state transitions, and API routes:

```bash
.venv313\Scripts\python.exe -m pytest
```

**Expected Result**: All 5 test suites pass (`5 passed`).

### Frontend Production Build
To verify component syntax and TypeScript/JSX bundle integrity:

```bash
cd frontend
cmd /c npm run build
```

---

## 13. Limitations & Future Scope

1. **Live PCAP Ingestion**: Future releases will incorporate live WinPcap / LibPcap streaming wrappers to auto-populate the 15 input fields directly from network interfaces in real time.
2. **Online Markov Model Updating**: Transition probability matrices can be updated online using streaming Bayesian parameter estimation as continuous network traffic logs arrive.
3. **Multi-Node Federated Intelligence**: Scaling forecasting capabilities across distributed enterprise subnets via federated learning architectures.

---

## 14. Project Status

- **Phase 1 (Design & Baseline UI)**: Completed.
- **Phase 2 (End-to-End Functional Integration)**: **Completed**.
- **Model Integrity**: 100% Preserved (Unmodified research models and weights).
- **Integration Status**: Live FastAPI + React integration active.

---

*Developed for Smart India Hackathon 2026 — Problem Statement SIH26153.*
��
Evaluation
    ↓
Comparison
    ↓
Evidence
    ↓
Final Decision

The final architecture will therefore be based on experimental evidence rather than assumptions.


22. Project Philosophy

NetVision-AI-SIH26153 follows a research-driven engineering approach:

Research → Understand → Experiment → Validate → Implement → Evaluate → Integrate → Demonstrate

The goal is to develop a technically defensible and demonstrable network attack forecasting system rather than only a conventional intrusion detection classifier.


23. Project Status

Status: Under Development

Primary Focus: Temporal Network Attack Forecasting

Primary Dataset Candidate: CIC-IDS2018

ML Direction: Comparative ML and Ensemble Experiments

Explainability: SHAP

Backend: FastAPI + REST API

ML Compute: Google Colab

Processed Dataset Storage: Hugging Face

Version Control: GitHub


