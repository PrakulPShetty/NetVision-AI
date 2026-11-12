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

The system ingests raw CICFlowMeter CSV exports, PCAP/PCAPNG captures or aggregated traffic-profile CSVs, aggregates them into 5-minute observation windows, expands the 40-field practical profile into 138 engineered features using a runtime feature transformer, evaluates current threat status via an **XGBoost + Random Forest-SMOTE Ensemble**, projects future threat progression using a **Discrete-Time Markov World Model**, explains key risk drivers via **SHAP (SHapley Additive exPlanations)**, and maps predicted attack patterns to actionable **MITRE ATT&CK** tactics and techniques.

---

## 2. Key Capabilities

- **40-Field Practical Input Surface**: A single 5-minute traffic window described by counts, volumes, durations, packet-size statistics, rates, timing, TCP flags, and activity/idle behaviour.
- **Capture File Ingestion**: Upload raw CICFlowMeter CSVs, PCAP/PCAPNG captures, aggregated 40-field profile CSVs, or 138-feature Phase 4 CSVs. Flows are aggregated into 5-minute windows with the training pipeline's Phase 4 semantics.
- **Runtime Feature Engineering**: Automated 138-feature expansion from the 40-field profile, matching the frozen model schema without re-engineering the trained models.
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
                    │  Upload panel · Profile form · Results  │
                    └────────────────────┬────────────────────┘
                                         │ HTTP: /preprocess/file
                                         │       /forecast
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │   FastAPI Backend + Capture Ingestion   │
                    │ CSV / PCAP / PCAPNG → 5-minute windows  │
                    │         (Uvicorn + Pydantic v2)         │
                    └────────────────────┬────────────────────┘
                                         │ 40 Profile Fields
                                         ▼
                    ┌─────────────────────────────────────────┐
                    │       Runtime Feature Transformer       │
                    │   (Expands 40 inputs to 138 features)   │
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
| **File Ingestion** | Pandas, Scapy (PCAP/PCAPNG), python-multipart |
| **Machine Learning** | Scikit-learn, XGBoost, Imbalanced-learn (SMOTE), Joblib, NumPy, Pandas |
| **Explainability (XAI)** | SHAP (SHapley Additive exPlanations) |
| **Security Framework** | MITRE ATT&CK v14 Knowledge Base Mapping |
| **Testing & CI** | Pytest, Vite Build Validator |

---

## 5. Machine Learning Pipeline & Dataset

### Dataset: CIC-IDS2018
The models were trained and validated on the benchmark **CIC-IDS2018** network intrusion dataset, capturing diverse traffic conditions across benign state operations, Reconnaissance (Port Scans), Exploitation, and Denial of Service (DoS/DDoS) scenarios.

### Feature Engineering (`RuntimeFeatureTransformer`)
The input interface describes **one 5-minute traffic observation window** using 40 practical fields:

- **Window**: `flow_count`, `unique_dst_ports`, `unique_protocols`
- **Volume**: `forward_packets`, `backward_packets`, `forward_bytes`, `backward_bytes`
- **Largest flow**: `max_fwd_packets_per_flow`, `max_bwd_packets_per_flow`, `max_fwd_bytes_per_flow`, `max_bwd_bytes_per_flow`
- **Flow duration (s)**: `avg_flow_duration_sec`, `max_flow_duration_sec`, `min_flow_duration_sec`
- **Packet profile (bytes)**: `avg_fwd_packet_size`, `avg_bwd_packet_size`, `max_fwd_packet_size`, `max_bwd_packet_size`, `min_fwd_packet_size`, `min_bwd_packet_size`, `pkt_len_std`
- **Rates**: `avg_flow_bytes_per_sec`, `avg_flow_packets_per_sec`, `avg_bwd_packets_per_sec`
- **Timing (s)**: `avg_iat_sec`, `iat_std_sec`, `max_iat_sec`, `avg_bwd_iat_sec`
- **TCP flags**: `syn_flag_cnt`, `ack_flag_cnt`, `rst_flag_cnt`, `fin_flag_cnt`, `psh_flag_cnt`, `urg_flag_cnt`
- **TCP profile**: `init_fwd_win_byts`, `init_bwd_win_byts`, `fwd_seg_size_min`
- **Activity / idle (s)**: `active_mean_sec`, `idle_mean_sec`
- **Balance**: `down_up_ratio`

The same profile can be produced automatically by uploading a raw CICFlowMeter CSV, a PCAP/PCAPNG capture, or an aggregated profile CSV. The runtime transformer expands the 40 fields into the complete **138-feature vector** expected by the pre-trained ML models. See [`docs/architecture/file_ingestion.md`](docs/architecture/file_ingestion.md) and [`docs/api/file_ingestion_api.md`](docs/api/file_ingestion_api.md).

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
- **Request Body** (all 40 profile fields shown; omitted fields default to `0.0`):
```json
{
  "traffic": {
    "flow_count": 150,
    "unique_dst_ports": 45,
    "unique_protocols": 2,
    "forward_packets": 1200,
    "backward_packets": 1100,
    "forward_bytes": 85000,
    "backward_bytes": 78000,
    "max_fwd_packets_per_flow": 120,
    "max_bwd_packets_per_flow": 110,
    "max_fwd_bytes_per_flow": 8500,
    "max_bwd_bytes_per_flow": 7800,
    "avg_flow_duration_sec": 5.0,
    "max_flow_duration_sec": 30.0,
    "min_flow_duration_sec": 0.01,
    "avg_fwd_packet_size": 70.8,
    "avg_bwd_packet_size": 70.9,
    "max_fwd_packet_size": 1460,
    "max_bwd_packet_size": 1460,
    "min_fwd_packet_size": 54,
    "min_bwd_packet_size": 54,
    "pkt_len_std": 320.5,
    "avg_flow_bytes_per_sec": 32600.0,
    "avg_flow_packets_per_sec": 460.0,
    "avg_bwd_packets_per_sec": 220.0,
    "avg_iat_sec": 0.05,
    "iat_std_sec": 0.12,
    "max_iat_sec": 2.4,
    "avg_bwd_iat_sec": 0.08,
    "syn_flag_cnt": 80,
    "ack_flag_cnt": 150,
    "rst_flag_cnt": 5,
    "fin_flag_cnt": 10,
    "psh_flag_cnt": 90,
    "urg_flag_cnt": 0,
    "init_fwd_win_byts": 8700,
    "init_bwd_win_byts": 24120,
    "fwd_seg_size_min": 17,
    "active_mean_sec": 0.13,
    "idle_mean_sec": 4.8,
    "down_up_ratio": 0.92
  }
}
```
- **Response Schema**: `ForecastResponse`
  - `current_assessment`: Object containing `predicted_class`, `attack_probability`, `threshold_used` (`0.40`), `ensemble_breakdown`.
  - `forecast_timeline`: Array of predictions for horizons `[10, 20, 30, 45, 60]` minutes.
  - `xai_explanation`: Object containing top positive and negative SHAP feature contributions.
  - `mitre_correlation`: Object containing mapped tactic, technique ID, technique name, and mitigation guidance.

### 3. Capture Preprocessing
- **`POST /preprocess/file`** (multipart)
- Upload a CICFlowMeter CSV, PCAP/PCAPNG capture, 40-field profile CSV, or
  138-feature Phase 4 CSV. Returns 5-minute windows with either a `profile`
  (40 fields) or `features` (138 fields) payload. No inference is performed.

### 4. Forecast From File
- **`POST /forecast/file`** (multipart)
- Form fields: `file` and optional `window_index` (default `0`).
- Runs the existing pipeline on the selected window and returns the unified
  forecast under `forecast`.
- Full request/response documentation: [`docs/api/file_ingestion_api.md`](docs/api/file_ingestion_api.md).

---

## 12. Testing & Verification

### Automated Backend Tests
Run the complete Pytest suite to verify feature transformation, ML model loading, Markov state transitions, ingestion, and API routes:

```bash
.venv313\Scripts\python.exe -m pytest
```

The ingestion suites (`tests/test_file_ingestion.py`, `tests/test_ingestion_api.py`) run without the trained artifacts; model-path tests require `models/trained/*` and `models/forecasting/*` to be present.

### Frontend Production Build
To verify component syntax and JSX bundle integrity:

```bash
cd frontend
cmd /c npm run build
```

---

## 13. Limitations & Future Scope

1. **Live Interface Capture**: File-based CSV/PCAP/PCAPNG ingestion is implemented; future releases will add live WinPcap / LibPcap streaming wrappers to auto-populate the 40-field profile directly from network interfaces.
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


