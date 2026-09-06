# NetVision-AI-SIH26153
AI based Network Attack Forecasting from Network Traffic Data — SIH26153


Smart India Hackathon 2026
1. Project Overview

NetVision-AI-SIH26153 is an AI/ML-based cybersecurity system designed to forecast potential network attacks from network traffic data.

The project focuses on moving beyond conventional intrusion detection, which primarily answers:

"Is an attack happening now?"

Our objective is to investigate:

"Based on the current and previous network states, is an attack likely to occur in the future?"

The system therefore studies the temporal behaviour of network traffic, models changes in network state, predicts future states, and generates an explainable attack forecast.


2. Problem Statement

Problem Statement ID: SIH26153

Problem Statement: AI based Network Attack Forecasting from Network Traffic Data

Theme: Blockchain & Cybersecurity

Category: Software

The proposed system aims to analyse network traffic and learn evolving network behaviour to forecast possible future attacks.


3. Project Objective

The primary objectives of the project are:

Analyse network traffic data.
Extract and process relevant network features.
Represent network traffic in a temporal form.
Identify the current network state.
Investigate state-transition behaviour.
Predict future network states.
Forecast the probability of an upcoming network attack.
Investigate multi-step/K-step forecasting where feasible.
Map predicted attack behaviour to relevant MITRE ATT&CK stages/techniques where supported.
Provide explainable predictions using SHAP.
Compare baseline, individual ML models, and ensemble approaches.
Develop an offline working prototype with a web dashboard and REST API.


4. Core Idea

The project follows the concept:

Network Traffic
       ↓
Data Preprocessing
       ↓
Feature Engineering
       ↓
Temporal Representation
       ↓
Current Network State
       ↓
State Transition Modelling
       ↓
Future-State Prediction
       ↓
Attack Forecasting
       ↓
MITRE ATT&CK Mapping
       ↓
SHAP / XAI
       ↓
REST API
       ↓
Web Dashboard

The central research direction is temporal network attack forecasting, rather than only static attack detection.


5. Proposed System

The system will process network traffic records and transform them into a representation that captures how network behaviour changes over time.

The general workflow is:

Input Network Traffic
        ↓
Dataset Investigation
        ↓
Data Cleaning
        ↓
Feature Processing
        ↓
Feature Engineering
        ↓
Temporal Ordering
        ↓
Time Window / Sequence Construction
        ↓
Current Network State
        ↓
ML Model Experiments
        ↓
Ensemble Experiments
        ↓
State Transition Modelling
        ↓
Future-State Prediction
        ↓
Attack Forecast
        ↓
MITRE ATT&CK Mapping
        ↓
SHAP Explanation
        ↓
REST API
        ↓
Web Dashboard

The exact temporal representation, forecasting horizon, state-transition technique, and final ensemble architecture will be determined through research and experimentation.


6. Machine Learning Direction

The project will investigate multiple machine learning approaches.

Baseline

Logistic Regression will be used as a reference baseline.

Individual Models

Candidate models may include:

Decision Tree
Random Forest
Extra Trees
XGBoost
LightGBM
Other suitable models identified during experimentation
Ensemble Learning

Ensemble modelling is an important direction of the project.

Different ensemble approaches will be experimentally evaluated before selecting the final approach.

The final model will be selected based on experimental evidence rather than assuming a particular algorithm in advance.


7. Temporal Forecasting

Temporal modelling is a core component of the project.

The intended concept is:

S(t-2) → S(t-1) → S(t)
                  ↓
          State Transition
                  ↓
               S(t+1)
                  ↓
               S(t+2)
                  ↓
          Attack Forecast

Where:

S(t) represents the current network state.
Previous states provide historical context.
The transition process models how the network state evolves.
Future states are predicted.
The predicted future behaviour is used for attack forecasting.

The exact:

temporal window,
sequence length,
state representation,
transition method,
forecasting horizon

will be determined experimentally.


8. Explainable AI

Explainability is an important part of the system.

SHAP will be investigated to identify the network traffic features contributing to model predictions.

Conceptually:

Future Attack Forecast
          ↓
      SHAP Analysis
          ↓
Important Contributing Features
          ↓
Human-Readable Explanation

The system should provide not only an attack forecast but also an explanation of the important features contributing to that forecast.


9. MITRE ATT&CK Integration

The project will investigate mapping predicted attack behaviour to relevant MITRE ATT&CK stages or techniques where the available evidence supports such mapping.

The intended concept is:

Predicted Network Behaviour
          ↓
Attack Behaviour Analysis
          ↓
MITRE ATT&CK Mapping
          ↓
Likely Stage / Technique

Mappings will not be fabricated when the available traffic data or model output cannot reliably support them.


10. Dataset
Primary Dataset

CIC-IDS2018

The dataset will be investigated for:

Network traffic features
Labels
Timestamps
Attack scenarios
Class distribution
Missing values
Duplicate records
Feature types
Temporal ordering
Attack progression
Suitability for forecasting
Secondary Dataset

CTU-13 may be investigated for additional validation or generalization if required.

The final dataset usage will depend on the results of dataset investigation and experimentation.


11. Input and Output
Input

The initial prototype is intended to work with network traffic data such as:

CSV flow records

PCAP processing may be investigated and implemented if required.

Expected Output

The system aims to provide:

Current network state
Future predicted state
Attack probability
Forecast timeline
Predicted attack behaviour/type where supported
Relevant MITRE ATT&CK stage/technique where supported
Important contributing network features
SHAP-based explanation


12. Technology Stack
Data and Scientific Computing
Python
NumPy
Pandas
SciPy

Machine Learning
Scikit-learn
XGBoost
LightGBM

Explainable AI
SHAP

Visualization
Matplotlib
Seaborn

Model Serialization
Joblib

Pickle where appropriate
Backend and REST API
FastAPI
Uvicorn
REST API
Frontend
Web-based dashboard
Development and Version Control
Visual Studio Code
Git
GitHub
ML Compute
Google Colab
Processed Dataset Storage
Hugging Face Dataset Repository


13. Development Architecture

The project follows a research-to-engineering workflow:

Research
   ↓
Understand
   ↓
Experiment
   ↓
Validate
   ↓
Decide
   ↓
Implement
   ↓
Evaluate
   ↓
Integrate
   ↓
Demonstrate

Heavy ML experimentation will be performed using Google Colab.

GitHub will contain the project source code, scripts, tests, documentation, and configuration.

Processed and ML-ready datasets may be stored and accessed through Hugging Face.



14. Frontend–Backend Architecture

The frontend will communicate with the backend through REST APIs.

┌─────────────────────┐
│      Frontend       │
│    Web Dashboard    │
└──────────┬──────────┘
           │
           │ REST API / HTTP
           ↓
┌─────────────────────┐
│    FastAPI Backend  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Backend Services  │
│                     │
│ Preprocessing       │
│ Feature Processing  │
│ Forecasting         │
│ XAI                 │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│ ML / Forecasting    │
│ Pipeline            │
└─────────────────────┘

The exact API routes and backend service architecture will be finalized after the ML input/output format is established.


15. Repository Structure
NetVision-AI-SIH26153/
│
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── raw/
│   │   └── README.md
│   ├── interim/
│   │   └── README.md
│   └── processed/
│       └── README.md
│
├── src/
│   ├── data/
│   ├── preprocessing/
│   ├── features/
│   ├── temporal/
│   ├── models/
│   ├── transition/
│   ├── forecasting/
│   ├── mitre/
│   ├── xai/
│   └── utils/
│
├── scripts/
│
├── models/
│   ├── README.md
│   ├── preprocessing/
│   └── trained/
│
├── backend/
│   ├── README.md
│   └── app/
│
├── frontend/
│   └── README.md
│
├── tests/
│
└── docs/
    ├── literature/
    ├── research/
    ├── datasets/
    ├── architecture/
    └── results/

The repository structure is maintained as the canonical project structure. Changes should only be made when a genuine architectural requirement is identified and agreed upon.


16. Research Documentation

Research documentation is maintained under:

docs/research/

Important research documents include:

research_gap.md
methodology.md
research_decisions.md

Literature documentation is maintained under:

docs/literature/

The current literature survey consists of three research papers.

Research documentation will distinguish between:

Findings reported by existing research.
Our analysis of those findings.
Proposed research directions for SIH26153.


17. Research Gap Direction

Existing network intrusion research commonly focuses on detecting or classifying attacks from network traffic.

Our research direction investigates the additional temporal question:

Can evolving network traffic behaviour be used to forecast a future attack before it occurs?

The project therefore investigates:

Static Detection
      ↓
Temporal Network Understanding
      ↓
State Transition
      ↓
Future-State Prediction
      ↓
Attack Forecasting

This research direction will be validated through dataset investigation and experiments.


18. Evaluation

The project will evaluate:

Classification and Detection Benchmarks
Accuracy
Precision
Recall
F1-score
False Positive Rate
Forecasting

Forecasting-specific metrics will be selected after the forecasting target, state representation, and prediction horizon are defined.

Models will be compared under consistent experimental conditions.


19. Project Development Phases

Phase 0 — Project Setup
Repository setup
Project structure
Git configuration
Python dependencies
README
GitHub ↔ Google Colab
Hugging Face dataset repository
Colab ↔ Hugging Face
End-to-end connection test

Phase 1 — Research Foundation
Literature survey
Research gap
Research questions
Methodology
Dataset investigation

Phase 2 — Data Pipeline
Data loading
Data cleaning
Encoding
Scaling
Feature engineering

Phase 3 — Temporal Representation
Timestamp ordering
Time windows
Sequence construction
Network state representation

Phase 4 — ML Experiments
Logistic Regression baseline
Individual models
Model comparison
Ensemble experiments

Phase 5 — Forecasting
State-transition modelling
Future-state prediction
Multi-step forecasting
Attack forecasting

Phase 6 — XAI and MITRE
MITRE ATT&CK mapping
SHAP analysis
Explainable forecast output

Phase 7 — System Integration
Model artifacts
REST API
FastAPI backend
Frontend dashboard
End-to-end integration

Phase 8 — Testing and Evaluation
Unit testing
Integration testing
ML evaluation
Forecasting evaluation
XAI validation

Phase 9 — Finalization
Technical documentation
Architecture diagrams
Working demonstration
Presentation
SIH submission preparation


20. Current Status
Completed
GitHub repository created
Canonical project structure created
.gitignore configured
Python dependency structure created
Literature survey completed with three papers
Initial research direction established
In Progress
Project setup
Research gap
Dataset investigation
Methodology development
Not Yet Finalized
Exact temporal window
Sequence length
Network state representation
State-transition algorithm
Forecasting horizon
Forecasting target representation
Final ensemble architecture
Final ML model
Final forecasting metrics
Final MITRE mapping methodology
Final backend API design
Final frontend design
Final deployment and inference architecture

These decisions will be made through research and experimentation.


21. Important Development Principle

The project will not assume that a particular model or architecture is the final solution.

The process is:

Literature
    ↓
Research Gap
    ↓
Hypothesis
    ↓
Experiment
    ↓
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


