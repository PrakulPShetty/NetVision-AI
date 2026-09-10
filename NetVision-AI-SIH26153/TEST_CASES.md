# NetVision AI — Test Case Documentation

**Document:** `TEST_CASES.md`
**Location:** Repository root (`./TEST_CASES.md`)
**System under test:** NetVision AI — AI-Based Network Attack Forecasting System (SIH26153)
**Pipeline under test:** `AttackForecastPipeline` (`src/forecasting/attack_forecast.py`) — the same pipeline invoked by the FastAPI backend (`backend/app/main.py` → `POST /forecast`)

---

## 0. Execution Statement (Integrity Declaration)

> **All four test cases documented in this file were actually executed against the CURRENT implementation on September 11, 2026.**
>
> Every probability, state, forecast, SHAP contribution, and MITRE correlation below is a **recorded system output**, not an invented or aspirational value.
>
> During this validation **NO changes** were made to:
>
> - ML models or model weights (`models/trained/xgb_model.json`, `models/trained/rf_smote_model.pkl`)
> - Ensemble weights (XGBoost `0.50` / Random Forest `0.50` — soft voting)
> - Decision threshold (**`0.40`**, loaded from `models/trained/ensemble_config.json`)
> - World Model (`models/forecasting/state_transition_model.json`)
> - XAI engine (`src/xai/shap_explainer.py`, probability-space SHAP)
> - MITRE logic (`src/mitre/attack_mapping.py`)
>
> Raw machine-readable results: [`reports/test_case_results.json`](reports/test_case_results.json)
> Executing script: [`scripts/execute_test_cases_doc.py`](scripts/execute_test_cases_doc.py)
> Environment: Python 3.13.5 (`.venv313`), Windows.

### How the cases were executed

| Case | Input path | Execution mode |
| :--- | :--- | :--- |
| TC1–TC3 | Practical traffic dictionary (39 fields) | `pipeline.forecast_from_traffic()` → `RuntimeFeatureTransformer` → 138 features → full pipeline |
| TC4 | Real CIC-IDS2018 Phase 4 row (138 features, direct) | `pipeline.forecast()` with the genuine feature vector — no runtime transformation |

For every case the pipeline ran end-to-end: runtime transformation (where applicable) → XGBoost probability → Random Forest probability → 50/50 soft-voting ensemble → `0.40` threshold → current state → Markov World Model k-step forecasts (10/20/30/45/60 min) → probability-space SHAP explanation → MITRE ATT&CK behavioral mapping.

### Validation-status semantics used in this document

- **TC1–TC3 are synthetic, behavioral/attack-like validation scenarios.** They are derived from the project's established runtime-input profiles (`scripts/runtime_input_test_suite.py`, mirroring `frontend/src/utils/presets.js`). **No ground-truth label exists for these inputs** — they validate *behavioral separation* (does the system react correctly to traffic that looks normal vs. attack-like), **not** dataset ground truth. They are explicitly labeled as such.
- **TC4 is the ground-truth validation case.** The input is a genuine CIC-IDS2018 Phase 4 feature-engineered window (sampled from `models/xai/shap_background.csv`, which holds 50 genuine Phase 4 rows), so its label **is** known.

### Note on the previously reported baseline

A previously validated real-sample baseline reported (as aggregate validation metrics over the evaluation set): XGBoost ≈ 98.20%, Random Forest ≈ 93.10%, Ensemble ≈ 95.65%, State = ATTACK. Those are aggregate dataset-level metrics. The values below are **single-window inference probabilities produced by the current implementation during this run** and are reported as actually observed; they are not forced to match the aggregate baseline figures.

---

## Test Case 1 — Normal / Benign Traffic

### Purpose

Verify that ordinary, balanced enterprise traffic (web/API/database-like flows with symmetric bidirectional payloads and long-lived flows) is classified as **BENIGN** with a low ensemble attack probability, and that the World Model forecasts the benign state to persist across all horizons. This is a **behavioral validation scenario (no ground-truth label available)**.

### Scenario

A healthy enterprise observation window: ~8,570 concurrent flows across ~950 distinct destination ports and 3 protocols, symmetric forward/backward packet and byte volumes, moderate flow durations (avg ~12.9 s), low-to-moderate flag counts (handshake-completion ratios normal), and steady inter-arrival times. Median benign CIC-IDS2018 Phase 4 window values.

### Actual input values (practical traffic — 39 fields)

| Field | Value | Field | Value |
| :--- | ---: | :--- | ---: |
| flow_count | 8570 | avg_flow_bytes_per_sec | 214664 |
| unique_dst_ports | 950 | avg_flow_packets_per_sec | 21281 |
| unique_protocols | 3 | avg_bwd_packets_per_sec | 2543 |
| forward_packets | 50500 | avg_iat_sec | 4.05 |
| backward_packets | 50300 | iat_std_sec | 0.74 |
| forward_bytes | 3555000 | max_iat_sec | 6.6 |
| backward_bytes | 28700000 | avg_bwd_iat_sec | 0.57 |
| max_fwd_packets_per_flow | 1130 | syn_flag_cnt | 285 |
| max_bwd_packets_per_flow | 5820 | ack_flag_cnt | 2694 |
| max_fwd_bytes_per_flow | 28300 | rst_flag_cnt | 2007 |
| max_bwd_bytes_per_flow | 8340000 | fin_flag_cnt | 35 |
| avg_flow_duration_sec | 12.9 | psh_flag_cnt | 3846 |
| max_flow_duration_sec | 120 | urg_flag_cnt | 259 |
| avg_fwd_packet_size | 57 | init_fwd_win_byts | 8733 |
| avg_bwd_packet_size | 108 | init_bwd_win_byts | 24352 |
| max_fwd_packet_size | 222 | fwd_seg_size_min | 17 |
| max_bwd_packet_size | 371 | active_mean_sec | 0.14 |
| min_fwd_packet_size | 9 | idle_mean_sec | 4.85 |
| min_bwd_packet_size | 22 | down_up_ratio | 0.45 |
| pkt_len_std | 117 | | |

### Runtime transformation & feature vector audit

| Check | Observed value |
| :--- | :--- |
| Runtime transformed feature count | **138** |
| Feature shape | **(1, 138)** |
| NaN count | **0** |
| Inf count | **0** |
| Zero-valued features / non-zero features | 19 / 119 |

### Model inference (actual output)

| Metric | Observed value |
| :--- | ---: |
| XGBoost probability | **0.172121** |
| Random Forest probability | **0.333333** |
| Ensemble probability | **0.252727** |
| Threshold | 0.40 |
| Current security state | **BENIGN** |

### World Model forecasts (actual output)

| Horizon | Attack probability | Forecast state | Steps (5-min) |
| ---: | ---: | :--- | ---: |
| 10 minutes | 0.056266 | BENIGN | 2 |
| 20 minutes | 0.102077 | BENIGN | 4 |
| 30 minutes | 0.139375 | BENIGN | 6 |
| 45 minutes | 0.182740 | BENIGN | 9 |
| 60 minutes | 0.214599 | BENIGN | 12 |

### XAI — top contributing features (probability-space SHAP, actual output)

| Rank | Feature | SHAP contribution |
| ---: | :--- | ---: |
| 1 | Flow Duration_max | +0.034852 |
| 2 | Init Bwd Win Byts_mean | −0.034779 |
| 3 | TotLen Fwd Pkts_max | −0.025089 |
| 4 | Bwd Pkts/s_mean | −0.022579 |
| 5 | Tot Fwd Pkts_sum | −0.015900 |

Interpretation from the run: the flow-duration term pushes slightly toward attack risk while the backward-window, forward-packet-volume and backward-rate features pull the probability down — net effect keeps the ensemble far below the 0.40 threshold. (SHAP reconstruction error: 8.12e-09 → PASS.)

### MITRE behavioral correlations (actual output)

Mapping status: `MITRE ATT&CK mapping identified`

| Technique | Name | Tactic | Confidence |
| :--- | :--- | :--- | :--- |
| T1046 | Network Service Discovery | Discovery | Medium |
| T1498 | Network Denial of Service | Impact | Medium |
| T1498.001 | Direct Network Flood | Impact | Low-Medium |

> Caveat (documented Phase 8 limitation): the MITRE mapper fires on **network-observable behavioral evidence groups** (traffic volume, packet rate, temporal concentration, destination diversity), not on the ML verdict. This benign window is high-volume in absolute terms, so the evidence rules triggered despite the BENIGN classification. Flow-level evidence alone cannot confirm maliciousness — this is expected mapper behavior, not a forced or fabricated result.

### Validation status

**PASS (behavioral validation scenario).** Clean-traffic profile → BENIGN (ensemble 0.252727 « 0.40), benign state forecast at all five horizons. Behavioral scenario — no ground-truth label claimed.

---

## Test Case 2 — High-Volume / Flood-Like Attack Scenario

### Purpose

Verify that a bulk, asymmetric, high-volume traffic pattern with heavy backward payload and elevated RST/ACK activity — the traffic shape of a volumetric DoS/flood — crosses the 0.40 threshold and that the World Model forecasts sustained ATTACK risk across all horizons. This is a **behavioral/attack-like validation scenario (no ground-truth label available)**.

### Scenario

~9,880 flows, ~1,134 destination ports, 3 protocols, large asymmetric backward byte volume (46.1 MB backward vs 3.9 MB forward), heavy RST (2,746) and ACK (3,579) flag activity, sustained high flow rates. Median attack Phase 4 window values used as the profile basis.

### Actual input values (practical traffic — 39 fields)

| Field | Value | Field | Value |
| :--- | ---: | :--- | ---: |
| flow_count | 9880 | avg_flow_bytes_per_sec | 187343 |
| unique_dst_ports | 1134 | avg_flow_packets_per_sec | 18120 |
| unique_protocols | 3 | avg_bwd_packets_per_sec | 2244 |
| forward_packets | 59200 | avg_iat_sec | 3.49 |
| backward_packets | 69900 | iat_std_sec | 0.63 |
| forward_bytes | 3875000 | max_iat_sec | 5.6 |
| backward_bytes | 46115000 | avg_bwd_iat_sec | 0.51 |
| max_fwd_packets_per_flow | 2000 | syn_flag_cnt | 345 |
| max_bwd_packets_per_flow | 6160 | ack_flag_cnt | 3579 |
| max_fwd_bytes_per_flow | 41500 | rst_flag_cnt | 2746 |
| max_bwd_bytes_per_flow | 8970000 | fin_flag_cnt | 38 |
| avg_flow_duration_sec | 11.3 | psh_flag_cnt | 4705 |
| max_flow_duration_sec | 120 | urg_flag_cnt | 297 |
| avg_fwd_packet_size | 54 | init_fwd_win_byts | 8352 |
| avg_bwd_packet_size | 101 | init_bwd_win_byts | 20239 |
| max_fwd_packet_size | 203 | fwd_seg_size_min | 18 |
| max_bwd_packet_size | 322 | active_mean_sec | 0.12 |
| min_fwd_packet_size | 7 | idle_mean_sec | 4.12 |
| min_bwd_packet_size | 17 | down_up_ratio | 0.47 |
| pkt_len_std | 115 | | |

### Runtime transformation & feature vector audit

| Check | Observed value |
| :--- | :--- |
| Runtime transformed feature count | **138** |
| Feature shape | **(1, 138)** |
| NaN count | **0** |
| Inf count | **0** |
| Zero-valued features / non-zero features | 19 / 119 |

### Model inference (actual output)

| Metric | Observed value |
| :--- | ---: |
| XGBoost probability | **0.598588** |
| Random Forest probability | **0.510000** |
| Ensemble probability | **0.554294** |
| Threshold | 0.40 |
| Current security state | **ATTACK** |

### World Model forecasts (actual output)

| Horizon | Attack probability | Forecast state | Steps (5-min) |
| ---: | ---: | :--- | ---: |
| 10 minutes | 0.870451 | ATTACK | 2 |
| 20 minutes | 0.764974 | ATTACK | 4 |
| 30 minutes | 0.679097 | ATTACK | 6 |
| 45 minutes | 0.579251 | ATTACK | 9 |
| 60 minutes | 0.505898 | ATTACK | 12 |

### XAI — top contributing features (probability-space SHAP, actual output)

| Rank | Feature | SHAP contribution |
| ---: | :--- | ---: |
| 1 | Fwd Seg Size Min_mean | +0.046238 |
| 2 | Flow Duration_max | +0.032637 |
| 3 | Tot Fwd Pkts_sum | +0.030436 |
| 4 | TotLen Fwd Pkts_sum | +0.025878 |
| 5 | Bwd Pkts/s_mean | −0.019107 |

Interpretation from the run: the minimum forward segment size, long flow durations and total forward packet/byte volumes are the main drivers pushing the probability above the threshold. (SHAP reconstruction error: 7.55e-10 → PASS.)

### MITRE behavioral correlations (actual output)

Mapping status: `MITRE ATT&CK mapping identified`

| Technique | Name | Tactic | Confidence |
| :--- | :--- | :--- | :--- |
| T1046 | Network Service Discovery | Discovery | Medium |
| T1498 | Network Denial of Service | Impact | Medium |
| T1498.001 | Direct Network Flood | Impact | Low-Medium |

The T1498 / T1498.001 correlations (Impact tactic) are behaviorally consistent with this flood-like scenario — driven by the traffic-volume, packet-rate and temporal-concentration evidence groups.

### Validation status

**PASS (behavioral/attack-like validation scenario).** Flood-like profile → ATTACK (ensemble 0.554294 ≥ 0.40), sustained ATTACK forecast at all horizons with decaying confidence (0.87 → 0.51) reflecting the Markov model's learned attack-persistence statistics. No ground truth claimed for this synthetic profile.

---

## Test Case 3 — Scanning-Like Traffic Scenario

### Purpose

Verify how the current model scores service-discovery behavior: thousands of distinct destination ports, small 1–2 packet flows, short durations and high RST replies. This probes the reconnaissance-shaped region of the feature space. This is a **behavioral/attack-like validation scenario (no ground-truth label available)**.

### Scenario

~12,000 flows toward ~5,000 distinct destination ports with only 2 protocols, tiny flows (max 2 forward / 1 backward packet per flow), short durations (avg 0.5 s), 6,000 SYNs vs 8,000 RSTs — classic horizontal service-scan shape.

### Actual input values (practical traffic — 39 fields)

| Field | Value | Field | Value |
| :--- | ---: | :--- | ---: |
| flow_count | 12000 | avg_flow_bytes_per_sec | 60000 |
| unique_dst_ports | 5000 | avg_flow_packets_per_sec | 2000 |
| unique_protocols | 2 | avg_bwd_packets_per_sec | 500 |
| forward_packets | 24000 | avg_iat_sec | 0.05 |
| backward_packets | 6000 | iat_std_sec | 0.02 |
| forward_bytes | 1320000 | max_iat_sec | 0.5 |
| backward_bytes | 480000 | avg_bwd_iat_sec | 0.05 |
| max_fwd_packets_per_flow | 2 | syn_flag_cnt | 6000 |
| max_bwd_packets_per_flow | 1 | ack_flag_cnt | 9000 |
| max_fwd_bytes_per_flow | 120 | rst_flag_cnt | 8000 |
| max_bwd_bytes_per_flow | 80 | fin_flag_cnt | 10 |
| avg_flow_duration_sec | 0.5 | psh_flag_cnt | 20 |
| max_flow_duration_sec | 2 | urg_flag_cnt | 0 |
| avg_fwd_packet_size | 55 | init_fwd_win_byts | 64240 |
| avg_bwd_packet_size | 80 | init_bwd_win_byts | 64240 |
| max_fwd_packet_size | 60 | fwd_seg_size_min | 0 |
| max_bwd_packet_size | 80 | active_mean_sec | 0.01 |
| min_fwd_packet_size | 54 | idle_mean_sec | 0.1 |
| min_bwd_packet_size | 54 | down_up_ratio | 0.36 |
| pkt_len_std | 10 | | |

### Runtime transformation & feature vector audit

| Check | Observed value |
| :--- | :--- |
| Runtime transformed feature count | **138** |
| Feature shape | **(1, 138)** |
| NaN count | **0** |
| Inf count | **0** |
| Zero-valued features / non-zero features | 24 / 114 |

### Model inference (actual output)

| Metric | Observed value |
| :--- | ---: |
| XGBoost probability | **0.077923** |
| Random Forest probability | **0.443333** |
| Ensemble probability | **0.260628** |
| Threshold | 0.40 |
| Current security state | **BENIGN** |

> Honest observation: the two models disagree markedly on this profile (XGB 0.078 vs RF 0.443). The 50/50 ensemble lands at 0.2606, below the frozen 0.40 threshold, so the reported state is BENIGN. The RF-SMOTE model reacts to the scan shape but the XGBoost component dominates the average downward. This disagreement is reported as observed — no output was forced. The project's known runtime-input limitation (some Phase 4 schema features, e.g. `_sum` aggregates and several IAT/window fields, are approximated or zeroed for practical inputs, see `scripts/diagnostic_integration_test.py` Section 10) plausibly contributes to the practical-input representation not fully matching the trained scan region.

### World Model forecasts (actual output)

| Horizon | Attack probability | Forecast state | Steps (5-min) |
| ---: | ---: | :--- | ---: |
| 10 minutes | 0.056266 | BENIGN | 2 |
| 20 minutes | 0.102077 | BENIGN | 4 |
| 30 minutes | 0.139375 | BENIGN | 6 |
| 45 minutes | 0.182740 | BENIGN | 9 |
| 60 minutes | 0.214599 | BENIGN | 12 |

### XAI — top contributing features (probability-space SHAP, actual output)

| Rank | Feature | SHAP contribution |
| ---: | :--- | ---: |
| 1 | TotLen Fwd Pkts_sum | −0.059056 |
| 2 | Fwd Seg Size Min_mean | −0.047618 |
| 3 | Fwd IAT Max_mean | +0.038990 |
| 4 | Init Fwd Win Byts_mean | +0.034582 |
| 5 | Fwd IAT Tot_max | −0.026093 |

Interpretation from the run: the low forward byte totals and minimum segment size pull the probability down, while the forward-IAT and initial-window features push modestly up — net well below threshold. (SHAP reconstruction error: 1.25e-08 → PASS.)

### MITRE behavioral correlations (actual output)

Mapping status: `MITRE ATT&CK mapping identified`

| Technique | Name | Tactic | Confidence |
| :--- | :--- | :--- | ---: |
| T1046 | Network Service Discovery | Discovery | Medium |
| T1498 | Network Denial of Service | Impact | Medium |
| T1498.001 | Direct Network Flood | Impact | Low-Medium |

The **T1046 Network Service Discovery (Discovery)** correlation is the behaviorally consistent one for this scan-shaped scenario (destination-diversity + traffic-volume + temporal-concentration evidence groups). The T1498 correlations fire from the same absolute-volume evidence and carry the documented mapper limitation (behavioral evidence ≠ malicious confirmation).

### Validation status

**PARTIAL PASS (behavioral/attack-like validation scenario).** The pipeline processed the scan-shaped profile correctly end-to-end (138 features, 0 NaN/Inf, valid forecasts) and the MITRE mapper correlated T1046 as expected. However, the current model ensemble scores this practical-input scan profile BENIGN (0.2606 < 0.40), with a large XGB/RF disagreement. Reported exactly as observed; no ground truth claimed for this synthetic profile.

---

## Test Case 4 — Real CIC-IDS2018 Attack Sample ⭐ Ground-Truth Validation Case

### Purpose

Validate the full pipeline against a **genuine attack window from the CIC-IDS2018 dataset** — the strongest available ground truth. This case tests the models on data drawn from the same feature-engineering pipeline used in training (direct 138-feature path, no runtime approximation), where the label is actually known: **ATTACK**.

### Scenario

A real Phase 4 temporal feature window (row index **15** of `models/xai/shap_background.csv`, a 50-row sample of genuine CIC-IDS2018 Phase 4 data): ~19,800 flows across 1,202 destination ports and 3 protocols, ~88.8k forward / ~84.5k backward packets, ~6.35 MB forward / ~31.3 MB backward payload, long flow durations, heavy RST (7,209) / PSH (9,558) / ACK (7,617) flag counts. Exact provenance copy saved to [`artifacts/phase-8/attack_sample_for_TEST_CASES.csv`](artifacts/phase-8/attack_sample_for_TEST_CASES.csv).

### Actual input values (key fields of the real 138-feature row)

| Feature | Value | Feature | Value |
| :--- | ---: | :--- | ---: |
| flow_count | 19800 | Flow Byts/s_mean | 115264.71 |
| unique_dst_ports | 1202 | Flow Byts/s_max | 95000000 |
| unique_protocols | 3 | Flow Pkts/s_mean | 11277.83 |
| total_flow_count | 19800 | Flow Pkts/s_max | 3000000 |
| Tot Fwd Pkts_sum | 88805 | Bwd Pkts/s_mean | 1919.37 |
| Tot Fwd Pkts_mean | 4.4851 | Bwd Pkts/s_max | 2000000 |
| Tot Fwd Pkts_max | 2100 | SYN Flag Cnt_sum | 381 |
| Tot Bwd Pkts_sum | 84485 | SYN Flag Cnt_max | 1 |
| Tot Bwd Pkts_max | 4350 | RST Flag Cnt_sum | 7209 |
| TotLen Fwd Pkts_sum | 6350199 | RST Flag Cnt_max | 1 |
| TotLen Bwd Pkts_sum | 31323885 | PSH Flag Cnt_sum | 9558 |
| Flow Duration_mean | 7671222.58 | ACK Flag Cnt_sum | 7617 |
| Flow Duration_max | 119999738 | FIN Flag Cnt_sum | 33 |
| Flow IAT Mean_mean | 2695452.29 | URG Flag Cnt_sum | 384 |
| Fwd IAT Max_mean | 3811606.79 | Init Fwd Win Byts_mean | 7424.08 |
| Bwd IAT Mean_mean | 382785.95 | Init Bwd Win Byts_mean | 15043.14 |
| Fwd Pkt Len Max_mean | 202.89 | Fwd Seg Size Min_mean | 18.38 |
| Bwd Pkt Len Max_mean | 244.91 | Active Mean_mean | 74532.49 |
| Pkt Len Min_mean | 5.0003 | Idle Mean_mean | 3189215.22 |
| Pkt Len Max_mean | 309.13 | Down/Up Ratio_mean | 0.5990 |
| Pkt Len Mean_mean | 57.35 | | |
| Pkt Len Std_mean | 95.82 | | |

*(All 138 features of this row were passed to the pipeline; the table above shows the most informative ones. Full row: `artifacts/phase-8/attack_sample_for_TEST_CASES.csv`.)*

### Feature vector audit (direct 138-feature path)

| Check | Observed value |
| :--- | :--- |
| Runtime transformed feature count | **138** (native Phase 4 schema — no runtime transformation applied) |
| Feature shape | **(1, 138)** |
| NaN count | **0** |
| Inf count | **0** |
| Zero-valued features / non-zero features | 18 / 120 |

### Model inference (actual output)

| Metric | Observed value |
| :--- | ---: |
| XGBoost probability | **0.809926** |
| Random Forest probability | **0.660000** |
| Ensemble probability | **0.734963** |
| Threshold | 0.40 |
| Current security state | **ATTACK** |

**Ground-truth verdict: TP — the real ATTACK sample is correctly classified as ATTACK** with a comfortable margin (0.735 vs 0.40 threshold; both models agree above threshold).

### World Model forecasts (actual output)

| Horizon | Attack probability | Forecast state | Steps (5-min) |
| ---: | ---: | :--- | ---: |
| 10 minutes | 0.870451 | ATTACK | 2 |
| 20 minutes | 0.764974 | ATTACK | 4 |
| 30 minutes | 0.679097 | ATTACK | 6 |
| 45 minutes | 0.579251 | ATTACK | 9 |
| 60 minutes | 0.505898 | ATTACK | 12 |

### XAI — top contributing features (probability-space SHAP, actual output)

| Rank | Feature | SHAP contribution |
| ---: | :--- | ---: |
| 1 | Init Bwd Win Byts_mean | +0.058682 |
| 2 | Fwd IAT Max_mean | +0.051617 |
| 3 | Fwd Seg Size Min_mean | +0.046561 |
| 4 | TotLen Fwd Pkts_sum | +0.036230 |
| 5 | Init Fwd Win Byts_mean | −0.036153 |

Interpretation from the run: the initial backward TCP window size, forward inter-arrival-time maximum and minimum forward segment size are the dominant attack-risk drivers for this real window. (SHAP reconstruction error: 5.69e-09 → PASS.)

### MITRE behavioral correlations (actual output)

Mapping status: `MITRE ATT&CK mapping identified`

| Technique | Name | Tactic | Confidence |
| :--- | :--- | :--- | ---: |
| T1046 | Network Service Discovery | Discovery | Medium |
| T1498 | Network Denial of Service | Impact | Medium |
| T1498.001 | Direct Network Flood | Impact | Low-Medium |

The **T1498 / T1498.001 (Impact — Network DoS / Direct Network Flood)** correlations are behaviorally consistent with this high-volume real attack window (traffic-volume + packet-rate + temporal-concentration evidence groups all satisfied).

### Validation status

**PASS — GROUND-TRUTH VALIDATED.** The genuine CIC-IDS2018 attack window (label: ATTACK) was classified ATTACK by the current unmodified implementation (XGB 0.8099 / RF 0.6600 / Ensemble 0.7350 ≥ 0.40). This is the strongest evidence in this document that the end-to-end detection pipeline (features → ensemble → threshold → World Model → XAI → MITRE) functions correctly on real data.

**Reference contrast (same execution run):** the genuine benign row (row index 26 of the same background sample) scored XGB 0.013329 / RF 0.050000 / Ensemble 0.031665 → BENIGN, giving a clean real-data separation of ~0.70 ensemble probability between the two genuine rows (ATTACK 0.7350 vs BENIGN 0.0317).

---

## Summary Comparison of All 4 Test Cases

| Metric | TC1 Normal / Benign | TC2 High-Volume / Flood-Like | TC3 Scanning-Like | TC4 Real CIC-IDS2018 Attack ⭐ |
| :--- | ---: | ---: | ---: | ---: |
| Input type | Practical traffic (39 fields) | Practical traffic (39 fields) | Practical traffic (39 fields) | Real Phase 4 row (138 features) |
| Ground truth | None (behavioral scenario) | None (behavioral scenario) | None (behavioral scenario) | **ATTACK (real dataset label)** |
| Transformed feature count | 138 | 138 | 138 | 138 |
| Feature shape | (1, 138) | (1, 138) | (1, 138) | (1, 138) |
| NaN count | 0 | 0 | 0 | 0 |
| Inf count | 0 | 0 | 0 | 0 |
| XGBoost probability | 0.172121 | 0.598588 | 0.077923 | **0.809926** |
| Random Forest probability | 0.333333 | 0.510000 | 0.443333 | **0.660000** |
| Ensemble probability | 0.252727 | 0.554294 | 0.260628 | **0.734963** |
| Threshold | 0.40 | 0.40 | 0.40 | 0.40 |
| Current security state | BENIGN | ATTACK | BENIGN | **ATTACK** |
| 10-min forecast | 0.056266 / BENIGN | 0.870451 / ATTACK | 0.056266 / BENIGN | 0.870451 / ATTACK |
| 20-min forecast | 0.102077 / BENIGN | 0.764974 / ATTACK | 0.102077 / BENIGN | 0.764974 / ATTACK |
| 30-min forecast | 0.139375 / BENIGN | 0.679097 / ATTACK | 0.139375 / BENIGN | 0.679097 / ATTACK |
| 45-min forecast | 0.182740 / BENIGN | 0.579251 / ATTACK | 0.182740 / BENIGN | 0.579251 / ATTACK |
| 60-min forecast | 0.214599 / BENIGN | 0.505898 / ATTACK | 0.214599 / BENIGN | 0.505898 / ATTACK |
| XAI top driver | Flow Duration_max (+0.035) | Fwd Seg Size Min_mean (+0.046) | TotLen Fwd Pkts_sum (−0.059) | Init Bwd Win Byts_mean (+0.059) |
| MITRE correlations | T1046, T1498, T1498.001 | T1046, T1498, T1498.001 | T1046, T1498, T1498.001 | T1046, T1498, T1498.001 |
| Validation status | PASS (behavioral) | PASS (behavioral/attack-like) | PARTIAL PASS (behavioral/attack-like) | **PASS (ground truth)** |

### Reading of the results

1. **Real-data ground truth holds (TC4):** the genuine attack window is confidently detected (ensemble 0.735 vs threshold 0.40) while the genuine benign reference row in the same run scores 0.032 — a clean real-data separation.
2. **Behavioral separation works for clear-cut synthetic profiles:** the flood-like profile (TC2) crosses the threshold and the normal profile (TC1) stays well below it.
3. **Honest limitation (TC3):** the scan-shaped *practical-input* profile scores BENIGN due to marked XGB/RF disagreement under the current runtime-transformation approximation of the Phase 4 schema; the real-data path (TC4) is unaffected because it bypasses that approximation. This is reported as observed and is a known input-representation limitation, not a threshold or model change.
4. **World Model behavior is state-consistent:** BENIGN current states forecast benign persistence (0.06 → 0.21 rising slowly); ATTACK current states forecast attack persistence with decaying probability (0.87 → 0.51), matching the learned Markov transition statistics (P(ATTACK→ATTACK) ≈ 0.932 per 5-min step).

---

## Verification Checklist

| # | Check | Result |
| :--- | :--- | :--- |
| 1 | `./TEST_CASES.md` exists at the repository root | ✅ (this file) |
| 2 | File is alongside `README.md`, `backend/`, `frontend/`, `models/`, `src/`, `tests/`, `notebooks/`, `reports/` | ✅ |
| 3 | Exactly 4 documented test cases (TC1–TC4) | ✅ |
| 4 | All four cases actually executed via `scripts/execute_test_cases_doc.py` on 2026-09-11 | ✅ |
| 5 | All documented numbers come from recorded system output (`reports/test_case_results.json`) | ✅ |
| 6 | No model, weight, ensemble weight, threshold, World Model, XAI, or MITRE logic modified | ✅ (only new files added: `TEST_CASES.md`, `scripts/execute_test_cases_doc.py`, `reports/test_case_results.json`, `artifacts/phase-8/attack_sample_for_TEST_CASES.csv`) |

*Reproduce with: `.venv313/Scripts/python.exe scripts/execute_test_cases_doc.py` (from the project root; set `PYTHONIOENCODING=utf-8` on Windows consoles).*
