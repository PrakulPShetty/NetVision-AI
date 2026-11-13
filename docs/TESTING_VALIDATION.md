# NetVision AI — Testing & Validation Framework

The canonical Testing & Validation document is located at:
[`NetVision-AI-SIH26153/docs/TESTING_VALIDATION.md`](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/docs/TESTING_VALIDATION.md)

### Summary of Testing & Validation Metrics:
- **Automated Tests**: 34/34 passing unit & integration tests (`pytest tests/`).
- **End-to-End Orchestrator**: `python run_all.py` (all 7 phases verified in <5s).
- **Inference Latency**: ~216 ms per full 138-feature forecast with SHAP and World Model.
- **Model Accuracy on 186-Column Ingestion**: 100.0% ($F_1 = 1.0000$).
- **Runtime Transformer Precision**: 100.0% precision on 40 practical traffic profile inputs ($r = 0.9235$).
- **MITRE ATT&CK Mapping**: Multi-signal conjunction verified for T1046, T1498, T1498.001.

Please refer to the full document at [TESTING_VALIDATION.md](file:///C:/Users/Asus/Documents/GitHub/NetVision-AI-SIH26153/NetVision-AI-SIH26153/docs/TESTING_VALIDATION.md) for detailed empirical tables and SLA compliance.
