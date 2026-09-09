NetVision AI — Phase 8 XAI + MITRE ATT&CK Report

Project: SIH26153 — AI based Network Attack Forecasting from Network Traffic Data
Phase: Phase 8 — XAI + MITRE ATT&CK
Status: COMPLETE

1. Executive Summary

Phase 8 extended the NetVision AI forecasting system with two interpretation layers:

Explainable AI (XAI) using probability-space SHAP for the final XGBoost + Random Forest-SMOTE ensemble.

MITRE ATT&CK mapping using network-observable behavioral evidence and explicitly defined decision rules.

Research and validation were first performed in Google Colab using the final Phase 7 model artifacts and real Phase 4 traffic data. The finalized components were then implemented in the VS Code project and integrated with the forecasting pipeline and FastAPI backend.

The final Phase 8 system produces a unified response containing:

ML attack probability and current state

World Model future-state probabilities

SHAP-based feature contributions

MITRE ATT&CK technique candidates when sufficient behavioral evidence exists

Phase 8 final validation: PASS.

2. Objectives

The objectives of Phase 8 were to:

Select an appropriate XAI method for the final ensemble.

Explain the ensemble prediction in probability space.

Validate SHAP reconstruction/additivity.

Investigate explanation stability across temporal windows.

Research suitable MITRE ATT&CK techniques for network-traffic observations.

Define evidence-based MITRE mapping rules.

Design a unified XAI + MITRE output.

Implement XAI and MITRE components in the project source code.

Integrate them with the existing forecasting pipeline.

Expose the unified result through the FastAPI backend.

Validate the complete Phase 8 integration.

3. Phase 8 Architecture

Network Traffic Features
          |
          v
   ML Forecasting
          |
     +----+----+
     |         |
     v         v
World Model   XAI
              SHAP
               |
               v
        Feature Evidence
               |
        +------+------+
        |
        v
MITRE ATT&CK Mapping
        |
        v
 Unified System Output

The roles of the components remain separate:

ML: estimates whether an attack is likely in the forecast target.

World Model: estimates future state evolution across multiple horizons.

XAI: explains the ML ensemble prediction.

MITRE ATT&CK: identifies known adversarial behaviors that are consistent with observed network evidence.

MITRE mapping is therefore not treated as proof that a specific technique occurred.

4. XAI Research and Method Selection

4.1 Final Ensemble

The final forecasting ensemble consists of:

XGBoost

Random Forest-SMOTE

Both are tree-based models, making Tree SHAP appropriate for model explanation.

4.2 Output-Space Investigation

Initial investigation showed that directly combining raw-space SHAP values from XGBoost and Random Forest was not valid because the models expose different output representations.

The final system therefore uses a common probability output space.

4.3 Selected Method

Probability-Space SHAP with weighted aggregation across XGBoost and Random Forest-SMOTE.

Weights:

XGBoost              0.50
Random Forest-SMOTE  0.50

This aligns the explanation with the actual ensemble attack probability.

5. SHAP Validation

5.1 XGBoost

Probability-space SHAP reconstruction was validated using a real Phase 4 traffic sample.

Reconstruction error was approximately:

2.4 × 10^-8

Result:

PASS

5.2 Random Forest

Random Forest attack-class SHAP reconstruction was independently validated.

Reconstruction error was approximately:

1.1 × 10^-16

Result:

PASS

5.3 Final Ensemble

The final weighted ensemble explanation was reconstructed from the probability-space contributions.

Measured reconstruction error:

1.2022241813 × 10^-8

Configured tolerance:

1 × 10^-5

Result:

Ensemble SHAP reconstruction: PASS

6. SHAP Background Dataset

A real Phase 4 traffic sample was used as the SHAP background for the final backend implementation.

Rows:       50
Features:   138
NaN:        0
Infinity:   0

Location:

models/xai/shap_background.csv

The final implementation therefore does not rely on a synthetic zero-feature background for backend explanations.

7. SHAP Stability Investigation

A multi-window exploratory investigation was performed using 20 evenly distributed temporal windows from a real Phase 4 file.

Windows analyzed: 20
Attack windows:   14
Benign windows:    6
Features:        138

Eight features appeared in the top-10 contribution list in at least half of the analyzed windows:

Feature

Top-10 appearances

TotLen Fwd Pkts_sum

20/20

TotLen Fwd Pkts_max

17/20

Fwd Seg Size Min_mean

16/20

Tot Fwd Pkts_sum

14/20

Init Bwd Win Byts_mean

13/20

Flow Duration_max

12/20

Init Fwd Win Byts_mean

11/20

Flow IAT Mean_max

11/20

These findings indicate repeated influence from traffic-volume, packet-size, timing, and TCP-window-related features in the analyzed sample.

Limitation: the analysis used 20 windows from one Phase 4 file and is therefore exploratory rather than a population-wide stability study.

8. Final XAI Configuration

Method:              Probability-space SHAP
Models:              XGBoost + Random Forest-SMOTE
Weights:             0.50 / 0.50
Features explained:  138
Stability sample:    20 windows
Additivity:          PASS
Ensemble validation: PASS

Artifact:

artifacts/phase-8/netvision_xai_configuration.json

9. MITRE ATT&CK Research

The MITRE research focused on techniques for which network-flow observations can provide relevant evidence.

Three techniques were selected.

9.1 T1046 — Network Service Discovery

Tactic: Discovery

Relevant network observations include destination-port and destination-diversity behavior.

Initial mapping confidence:

Medium

Flow data alone is not treated as proof of malicious discovery.

9.2 T1498 — Network Denial of Service

Tactic: Impact

Relevant observations include high traffic volume, packet-rate behavior, and temporal concentration.

Initial mapping confidence:

Medium

9.3 T1498.001 — Direct Network Flood

Parent: T1498 — Network Denial of Service

Relevant observations include concentrated high-volume traffic over short windows.

Initial mapping confidence:

Low-Medium

10. MITRE Evidence Model

The final mapping uses four network-observable signal groups.

Destination Diversity

unique_dst_ports
unique_protocols

Traffic Volume

flow_count
total_flow_count
Tot Fwd Pkts_sum
TotLen Fwd Pkts_sum

Packet Rate

Bwd Pkts/s_mean

Temporal Concentration

Flow Duration_max

During evidence-matrix validation, Fwd Pkts/s_mean was found to be unavailable in the final 138-feature schema and was removed from the final mapping configuration.

Final validation:

Mapped features available: PASS
Unavailable required features: 0

11. MITRE Behavioral Decision Rules

T1046

Required groups:

destination_diversity
traffic_volume
temporal_concentration

Minimum groups:

2

Confidence:

Medium

T1498

Required groups:

traffic_volume
packet_rate
temporal_concentration

Minimum groups:

3

Confidence:

Medium

T1498.001

Required groups:

traffic_volume
packet_rate
temporal_concentration

Minimum groups:

3

Confidence:

Low-Medium

A signal group is considered present when at least one valid feature in that group contains a finite value greater than zero.

These are research/design-level behavioral mapping rules, not calibrated attack-detection thresholds.

12. Insufficient-Evidence Handling

The system does not force a MITRE technique when behavioral evidence is insufficient.

Output:

No confident MITRE mapping identified

with:

techniques: []

This behavior was validated with zero and partial synthetic inputs.

The absence of a confident mapping does not mean that an attack is impossible.

13. Unified XAI + MITRE Output

The unified response contains:

ml
world_model
xai
mitre_attack

The XAI section contains:

explanation method

model weights

XGBoost probability

Random Forest probability

ensemble probability

base probability

reconstructed probability

reconstruction error

validation status

top contributions

positive contributors

negative contributors

The MITRE section contains:

mapping status

technique ID

technique name

tactic

confidence

evidence

supporting features

interpretation

limitations

The design also supports the empty-MITRE case.

14. VS Code Implementation

XAI

src/xai/
├── __init__.py
└── shap_explainer.py

Main class:

SHAPExplainer

MITRE

src/mitre/
├── __init__.py
└── attack_mapping.py

Main class:

MITREAttackMapper

Forecasting Integration

src/forecasting/attack_forecast.py

The forecasting pipeline was extended to return:

ML
World Model
XAI
MITRE ATT&CK

15. FastAPI Backend Integration

The XAI and MITRE components were integrated into:

backend/app/main.py

The backend loads:

XGBoost model
Random Forest-SMOTE model
Feature schema
Ensemble configuration
World Model
SHAP background
XAI module
MITRE mapper

Health endpoint result:

{
  "status": "healthy",
  "ml_model": "loaded",
  "world_model": "loaded",
  "xai": "loaded",
  "mitre_attack": "loaded"
}

Result:

Backend component loading: PASS

16. Complete Forecast API Validation

A complete 138-feature test request was sent to:

POST /forecast

HTTP result:

200 OK

ML output:

XGBoost probability:       0.1260959208
Random Forest probability: 0.3733333333
Ensemble probability:      0.2497146271
Current state:             BENIGN

World Model:

10 min:  0.0562658672
20 min:  0.1020767098
30 min:  0.1393752249
45 min:  0.1827404535
60 min:  0.2145990423

XAI:

Method: Probability-space SHAP
Ensemble probability: 0.2497146271
Reconstruction error: 2.1156567526 × 10^-8
Validation: PASS

MITRE:

Mapping status:
No confident MITRE mapping identified

Techniques:
0

The zero-input validation therefore correctly produced no MITRE technique.

17. Phase 8 Test Results

XAI Module

Model artifacts loading      : PASS
138-feature schema           : PASS
Ensemble configuration       : PASS
SHAP initialization          : PASS
Probability-space SHAP       : PASS
SHAP reconstruction          : PASS
Feature contribution output  : PASS

OVERALL XAI MODULE TEST      : PASS

MITRE Module

138-feature schema          : PASS
MITRE mapper initialization : PASS
Full evidence mapping       : PASS
Confidence validation       : PASS
Insufficient evidence       : PASS
Partial evidence handling   : PASS
Output structure            : PASS
Signal groups               : PASS

OVERALL MITRE MODULE TEST   : PASS

Unified Forecast Pipeline

ML forecasting                 : PASS
World Model forecasting        : PASS
Probability-space SHAP         : PASS
MITRE ATT&CK mapping           : PASS
Unified output structure       : PASS
ML ↔ XAI probability           : PASS

18. Final Phase 8 Artifacts

The finalized artifacts are stored under:

artifacts/phase-8/

Artifacts:

netvision_xai_configuration.json
netvision_mitre_research.json
netvision_mitre_evidence_matrix.json
netvision_mitre_mapping_configuration.json
netvision_mitre_architecture.json
netvision_mitre_output_schema.json
netvision_mitre_decision_rules.json
netvision_unified_xai_mitre_output.json
netvision_xai_mitre_integration.json
netvision_phase8_validation.json
PHASE_8_ARTIFACT_MANIFEST.json

19. Limitations

SHAP stability analysis was based on 20 windows from one Phase 4 file and is exploratory.

MITRE mapping uses network-observable evidence and does not prove that a technique was executed maliciously.

MITRE decision rules are design-level behavioral rules, not calibrated detection thresholds.

Some observed network behaviors may also occur during legitimate activity.

The current API accepts model-ready 138-feature input. Practical raw-input-to-138-feature transformation is addressed in the subsequent final system validation stage.

The Random Forest model was trained with scikit-learn 1.6.1 while the current Windows development environment uses scikit-learn 1.9.0, producing an InconsistentVersionWarning. The model loaded and passed validation; dependency pinning remains a deployment-hardening task.

20. Final Assessment

Phase 8 achieved its defined research, validation, implementation, and integration objectives.

The resulting system provides an interpretation layer around the forecasting model:

ML Forecast
     |
     +----> World Model
     |
     +----> SHAP Explanation
     |
     +----> MITRE ATT&CK Mapping
     |
     v
Unified Forecasting Response

Probability-space SHAP was selected and validated for the final ensemble.

MITRE ATT&CK mapping was constrained to network-observable evidence and implemented with explicit decision rules and insufficient-evidence handling.

The components were implemented in VS Code, integrated into the forecasting pipeline, and successfully exposed through FastAPI.

Final Status
PHASE 8 — COMPLETE
All planned Phase 8 activities have been completed.

The project is ready to proceed to: Phase 9 — Final Validation