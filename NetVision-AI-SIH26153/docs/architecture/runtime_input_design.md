# NetVision AI — Runtime Input Architecture Redesign

**Status:** Design proposal (approved for implementation)
**Scope:** Rearchitect the practical traffic input so runtime inputs map into the
frozen 138-feature model space correctly. The ML models, ensemble weights,
0.40 threshold, World Model transition probabilities, XAI, and MITRE mapping
are **not** modified.

---

## 1. Current architecture

```
Practical Traffic Form (40 fields)
        ↓  POST /forecast  {traffic: {...}}
Input Validation (ForecastRequest schema)
        ↓
RuntimeFeatureTransformer (src/features/runtime_transformer.py)
        ↓
138-feature DataFrame (feature_names.json order)
        ↓
XGBoost + RandomForest-SMOTE (50:50 soft vote, 0.40 threshold)
        ↓
Current State → Markov World Model → XAI/SHAP → MITRE → Unified result
```

The same 40-field profile can now also be produced automatically from an
uploaded CICFlowMeter CSV, PCAP/PCAPNG capture or pre-aggregated profile CSV;
see `docs/architecture/file_ingestion.md`. The ingestion layer is an adapter
and does not change the transformer or any model.

## 2. Current problem

Even strongly attack-like values entered in the form produce ensemble
probabilities around 30% (below the 40% threshold), so the result is BENIGN,
while genuine Phase 4 attack rows produce ~95%.

## 3. Root cause

The runtime transformer **inverts the semantics of the Phase 4 aggregation**:

1. **Window totals are placed into per-flow mean/max slots.**
   Phase 4 defined each 5-minute window as a row. `Tot Fwd Pkts_sum` is the
   *window total*; `Tot Fwd Pkts_mean` is the *mean per flow*
   (= total / flow_count, verified exact on all 50 real rows). The old
   transformer wrote the user's "Total forward packets" value into
   `Tot Fwd Pkts_mean` **and** `Tot Fwd Pkts_max`, and never wrote
   `Tot Fwd Pkts_sum` at all.

2. **`_sum` features were never populated.**
   `Tot Fwd Pkts_sum`, `Tot Bwd Pkts_sum`, `TotLen Fwd Pkts_sum`,
   `TotLen Bwd Pkts_sum` stayed 0.0. These are among the highest-importance
   features in the model (TotLen Fwd Pkts family ≈ 5.1% of combined
   importance; Tot Fwd Pkts family ≈ 3.9%).

3. **92 model-relevant features stayed zero.**
   A practical attack input produced a 138-vector with **109 zeros**; a real
   attack row has only **18 zeros**. Every IAT, packet-length, initial-window,
   active/idle, rate-max, and flag-max feature the model relies on was 0.

4. **Input magnitudes were outside the training distribution.**
   Real windows contain thousands of flows (median ~8.6K benign / ~9.9K
   attack) and hundreds of destination ports. The old presets used
   `flow_count = 50` and `syn_flag_cnt = 18200` — SYN counts ~50× above any
   real window — while flag `max` features are constant **1** in the real
   data (a flow carries a flag at most once). The model was never trained on
   such vectors.

5. **Degenerate statistics.**
   The old transformer set `mean = max = min = scalar`. Real windows always
   have distinct per-flow statistics.

The model itself is healthy: genuine Phase 4 benign rows score
0.013 / 0.050 / 0.032 (BENIGN), genuine attack rows score
0.810 / 0.660 / 0.735 (ATTACK), and the all-zero vector reproduces the
0.126 / 0.373 / 0.250 benign reference from the task.

## 4. 138-feature dependency analysis

Phase 3 produced 68 flow-level (per-flow) features from CICFlowMeter.
Phase 4 grouped flows into 5-minute windows and aggregated each per-flow
feature with `sum` / `mean` / `std` / `min` / `max` (group-specific).
Phase 5 dropped constant columns (the window-level `_std` aggregations and
uninformative features), freezing the final 138.

Each model feature is therefore one of:

| Class | Count | Example | Reconstructable at runtime? |
|---|---|---|---|
| Window-level aggregate | 4 | `flow_count`, `unique_dst_ports`, `unique_protocols`, `total_flow_count` | **Direct** input |
| Window sum of per-flow counts/bytes | 12 | `Tot Fwd Pkts_sum`, `TotLen Bwd Pkts_sum` | **Direct** input (window totals) |
| Window mean of per-flow counts/bytes | 12 | `Tot Fwd Pkts_mean` | **Exact derivation** — mean = sum / flow_count (verified rel. err = 0 on all 50 rows) |
| Window max of per-flow counts/bytes | 12 | `Tot Fwd Pkts_max`, `TotLen Fwd Pkts_max` | **Direct** input (largest flow) |
| Per-flow profile mean (duration, IAT, packet len, rates, windows, active/idle, ratio, seg-size) | ~45 | `Flow Duration_mean`, `Flow IAT Mean_mean`, `Init Fwd Win Byts_mean` | **Direct** input ("typical" values) |
| Per-flow profile min (duration, IAT, packet len, windows, active/idle) | ~20 | `Flow IAT Mean_min`, `Init Fwd Win Byts_min` | **Constant** (verified 0 in data) or derived |
| Per-flow profile max (duration, IAT, packet len, windows, active/idle) | ~45 | `Flow IAT Max_mean`, `Pkt Len Max_max` | **Constant** (verified: MTU 1460, 120 s timeout cap, flag=1) or derived from profile |
| Flag sums + max | 20 | `SYN Flag Cnt_sum`, `SYN Flag Cnt_max` | Sum = **Direct** input; max = **constant 1** (verified unique value in all rows) |
| Header lengths | 4 | `Fwd Header Len_mean/max` | **Derived** — ≈ 20 × per-flow packet count (median rel. err 1.5%) |

### What cannot be derived from window totals (must be entered)

- `Bwd Pkts/s_mean` (rank #1 importance): per-flow rate dominated by short
  flows; window total / duration is off by ~3 orders of magnitude.
- `Flow Pkts/s_mean`, `Flow Byts/s_mean`: same reason.
- IAT statistics (rank #7/#9/#16/#18/#20/#23): window-level duration /
  packets does not reconstruct per-flow inter-arrival structure
  (median rel. err 360%).

### Empirically verified relationships (50 genuine rows)

| Relationship | Result |
|---|---|
| `Tot Fwd Pkts_mean = Tot Fwd Pkts_sum / flow_count` | exact |
| `SYN/ACK/RST/FIN/PSH/URG/ECE Flag Cnt_max` | constant = 1 |
| `CWE Flag Count_max`, `Fwd URG Flags_max` | constant = 0 |
| `Fwd Header Len_mean ≈ 20 × Tot Fwd Pkts_mean` | median rel. err 1.5% |
| `Bwd Header Len_mean ≈ 20 × Tot Bwd Pkts_mean` | median rel. err 4.5% |
| `Pkt Len Max_max`, `Bwd Pkt Len Max_max` | constant = 1460 (MTU) |
| `Flow Duration_min`, `Flow IAT Mean_min`, `Fwd IAT Mean_min`, `Init * Win Byts_min` | constant = 0 |
| `Fwd IAT Mean_mean ≈ Flow IAT Mean_mean` | median rel. err 5.8% |
| `Fwd IAT Max_mean ≈ Flow IAT Max_mean` | median rel. err 2.3% |
| `Fwd/Bwd IAT Std_mean ≈ Flow IAT Std_mean` | median rel. err ~8-10% |
| `Bwd IAT Min_mean ≈ 0.21 × Bwd IAT Mean_mean` | p50 ratio 0.21 |
| `Active Std_mean ≈ 0.5 × Active Mean_mean` | p50 ratio 0.50 |
| `Idle Std_mean ≈ 0.02 × Idle Mean_mean` | p50 ratio 0.02 |
| `Active Max_mean ≈ 1.54 × Active Mean_mean` | p50 ratio 1.54 |
| `Idle Max_mean ≈ 1.01 × Idle Mean_mean` | p50 ratio 1.01 |
| `Flow IAT Mean_max ≈ 0.75 × Flow Duration_max` | p50 ratio 0.75 |
| `Flow IAT Std_max ≈ 0.48 × Flow Duration_max` | p50 ratio 0.48 |
| `Flow IAT Max_max ≈ 0.95 × Flow Duration_max` | p50 ratio 0.95 |
| `Fwd IAT Mean_max / Std_max / Max_max ≈ 0.82 / 0.36 / 0.92 × Duration_max` | p50 ratios |
| `Bwd IAT Mean_max / Std_max / Max_max ≈ 0.73 / 0.35 / 0.82 × Duration_max` | p50 ratios |
| `Fwd/Bwd IAT Tot_max ≈ Flow Duration_max` | p50 ratio 1.00 |
| `Active Mean/Max/Min_max ≈ 618 × Active Mean_mean` | p50 ratio 618 |
| `Active Std_max ≈ 368 × Active Mean_mean` | p50 ratio 368 |
| `Idle Mean/Max/Min_max ≈ 24 × Idle Mean_mean` | p50 ratio 24 |
| `Idle Std_max ≈ 9.1 × Idle Mean_mean` | p50 ratio 9.1 |
| `Fwd Pkt Len Mean_max ≈ 20 × avg fwd packet size` (≤ MTU) | p50 ratio 20 |
| `Bwd Pkt Len Mean_max ≈ 13 × avg bwd packet size` (≤ MTU) | p50 ratio 13 |
| `Pkt Len Std_max ≈ (MTU − min packet)/2` | median rel. err 1.2% |
| `Pkt Len Var_max ≈ ((MTU − min packet)/2)²` | median rel. err 2.4% |
| `Down/Up Ratio_max ≈ 27.5 × Down/Up Ratio_mean` | p50 ratio 27.5 |

## 5. Current input limitations

1. No way to express window totals as window totals.
2. No per-flow distribution (mean/max) inputs.
3. No timing inputs (duration, IAT, active/idle) in usable units.
4. No packet-size profile inputs.
5. No TCP profile (initial windows, segment size).
6. Units were ambiguous (`flow_duration` labelled "ms" but model uses µs).
7. No guidance or realistic presets anchored to the training distribution.

## 6. Proposed input form architecture (Option B — selected)

**Option B: the form describes ONE 5-minute traffic observation window as a
"traffic profile", and the backend reconstructs the 138 features using the
Phase 4 aggregation semantics.** Option A (tweaking the existing single
scalar form) is rejected because no set of scalar tweaks can fix the
semantic inversion — the form must collect profile statistics, not totals
masquerading as per-flow values.

The 5-minute window was the unit the model was trained on (1 row = 1
window), so the form should describe one window *thoroughly* rather than
several sub-observations. Multiple sub-observations would need re-aggregation
with no Phase 4 reference implementation to guarantee equivalence.

The UI stays one practical form with 11 logical sections and short tooltips.
The complexity lives in the backend transformer, which uses only:

1. **DIRECT** — user input maps 1:1 to the feature slot;
2. **DERIVED-EXACT** — verified Phase 4 identities (mean = sum / flow_count);
3. **DERIVED-CONSTANT** — verified constants (flag max = 1, MTU 1460,
   timeout cap 120 s, min = 0, header ≈ 20 × pkts);
4. **DERIVED-PROFILE** — documented approximations from the table above.

No arbitrary formulas (e.g., "SYN × 2 = missing feature") are used, and no
value is chosen to push the probability toward a target.

## 7–9. Proposed fields, reasons, and feature mapping

All durations are entered in **seconds** and converted to µs (the model's
unit). Every field maps to at least one frozen feature; the mapping table
below gives the justification (importance = combined 50/50 XGB+RF importance).

### S1 — Observation window
| Field | → Model feature(s) | Why |
|---|---|---|
| `flow_count` | `flow_count`, `total_flow_count` | rank #14 (1.30%); the window size drives all per-flow means |
| `unique_dst_ports` | `unique_dst_ports` | rank #46 (0.80%); destination diversity separates scanning from normal |
| `unique_protocols` | `unique_protocols` | diversity signal (0.01%) |

### S2 — Traffic volume (window totals)
| Field | → Model feature(s) | Why |
|---|---|---|
| `forward_packets` | `Tot Fwd Pkts_sum` (+`_mean` derived) | rank #6 family #3 |
| `backward_packets` | `Tot Bwd Pkts_sum` (+`_mean` derived) | rank #22 |
| `forward_bytes` | `TotLen Fwd Pkts_sum` (+`_mean` derived) | rank #4 — single most important family |
| `backward_bytes` | `TotLen Bwd Pkts_sum` (+`_mean` derived) | rank #31 |

Per-flow means are derived exactly: `*_mean = *_sum / flow_count`.

### S3 — Largest flow (peak per-flow)
| Field | → Model feature(s) | Why |
|---|---|---|
| `max_fwd_packets_per_flow` | `Tot Fwd Pkts_max` | rank #54; feeds header max |
| `max_bwd_packets_per_flow` | `Tot Bwd Pkts_max` | rank #67 |
| `max_fwd_bytes_per_flow` | `TotLen Fwd Pkts_max` | rank #10 (1.66%) |
| `max_bwd_bytes_per_flow` | `TotLen Bwd Pkts_max` | rank #58 |

### S4 — Flow duration
| Field | → Model feature(s) | Why |
|---|---|---|
| `avg_flow_duration_sec` | `Flow Duration_mean` (×1e6) | rank #55 |
| `max_flow_duration_sec` | `Flow Duration_max` (×1e6) | rank #59; also used for IAT-max derivation |
| `min_flow_duration_sec` (optional) | `Flow Duration_min` | default 0 (verified constant) |

### S5 — Packet sizes
| Field | → Model feature(s) | Why |
|---|---|---|
| `avg_fwd_packet_size` | `Fwd Pkt Len Mean_mean` | rank #25 |
| `avg_bwd_packet_size` | `Bwd Pkt Len Mean_mean` | rank #76 |
| `max_fwd_packet_size` | `Fwd Pkt Len Max_mean` | rank #19 |
| `max_bwd_packet_size` | `Bwd Pkt Len Max_mean` | rank #96; overall `Pkt Len Max_mean` = max(fwd, bwd) |
| `min_fwd_packet_size` | `Fwd Pkt Len Min_mean` | rank #105 |
| `min_bwd_packet_size` | `Bwd Pkt Len Min_mean` | rank #56; overall `Pkt Len Min_mean` = min(fwd, bwd); `Pkt Len Min_max` = max(min_fwd, min_bwd, 54) |
| `pkt_len_std` | `Pkt Len Std_mean`, `Fwd/Bwd Pkt Len Std_mean` (approx), `Pkt Len Var_mean` = std² | rank #21/#57 |

Max-across-flow caps are verified constants: `Pkt Len Max_max` /
`Bwd Pkt Len Max_max` = 1460 (MTU), `Pkt Len Std_max`/`Var_max` derived from
profile.

### S6 — Traffic rates (per-flow, cannot be derived)
| Field | → Model feature(s) | Why |
|---|---|---|
| `avg_flow_bytes_per_sec` | `Flow Byts/s_mean` | rank #103 |
| `avg_flow_packets_per_sec` | `Flow Pkts/s_mean` | rank #26 |
| `avg_bwd_packets_per_sec` | `Bwd Pkts/s_mean` | rank #1 (3.19%) — the single most important feature |

`_max` rate variants (rank ≤ 0.3%) are approximated by the mean
(documentation: peak per-flow rate not collected).

### S7 — Inter-packet timing (IAT)
| Field | → Model feature(s) | Why |
|---|---|---|
| `avg_iat_sec` | `Flow IAT Mean_mean` (+ `Fwd IAT Mean_mean` ≈, rel err 5.8%) | rank #23 / #9 |
| `iat_std_sec` | `Flow IAT Std_mean` (+ Fwd/Bwd IAT Std ≈) | rank #18 |
| `max_iat_sec` | `Flow IAT Max_mean`, `Fwd IAT Max_mean` (rel err 2.3%) | rank #20 / #7 |
| `avg_bwd_iat_sec` | `Bwd IAT Mean_mean` (+ `Bwd IAT Min_mean` ≈ 0.21×) | rank #16 / #29 |

`Fwd/Bwd IAT Tot_mean` ≈ mean IAT × (packets per flow − 1); `*_max` IAT
variants capped at 120 000 000 µs (verified timeout cap); `*_min` = 0
(verified constant).

### S8 — TCP flags
| Field | → Model feature(s) | Why |
|---|---|---|
| `syn_flag_cnt` | `SYN Flag Cnt_sum` (max = 1 constant) | rank #73 |
| `ack_flag_cnt` | `ACK Flag Cnt_sum` (max = 1) | rank #24 |
| `rst_flag_cnt` | `RST Flag Cnt_sum` (max = 1) | rank #32 |
| `fin_flag_cnt` | `FIN Flag Cnt_sum` (max = 1) | rank #100 |
| `psh_flag_cnt` | `PSH Flag Cnt_sum` (max = 1) | rank #8 (1.75%) |
| `urg_flag_cnt` | `URG Flag Cnt_sum` (max = 1) | rank #64 |

`CWE`, `ECE`, `Fwd PSH`, `Fwd URG` remain optional keys (defaults 0/1
documented); the form keeps them out to stay practical.

### S9 — TCP profile
| Field | → Model feature(s) | Why |
|---|---|---|
| `init_fwd_win_byts` | `Init Fwd Win Byts_mean` (min 0 / max 65535 constants) | rank #11 |
| `init_bwd_win_byts` | `Init Bwd Win Byts_mean` (min 0 / max 65535) | rank #12 |
| `fwd_seg_size_min` | `Fwd Seg Size Min_mean` | rank #5 (2.52%) |

### S10 — Activity / idle behaviour
| Field | → Model feature(s) | Why |
|---|---|---|
| `active_mean_sec` | `Active Mean_mean` (+ Std ≈ 0.5×, Max ≈ 1.54×) | rank #50/#33/#36/#40 |
| `idle_mean_sec` | `Idle Mean_mean` (+ Std ≈ 0.02×, Max ≈ 1.01×) | rank #13 (1.32%) |

### S11 — Network balance
| Field | → Model feature(s) | Why |
|---|---|---|
| `down_up_ratio` | `Down/Up Ratio_mean` (+ `_max` ≈ mean) | rank #34 |

**40 practical fields** → 138 model features (≥120 populated non-zero for a
complete profile; only negligible-importance fields remain zero). This is the
same profile produced by the file-ingestion layer from raw flows or packets.

## 10. Are temporal observations needed?

No — one 5-minute window is the native model unit. The temporal dimension is
already captured by the window's profile statistics (duration, IAT,
active/idle) plus the Markov World Model downstream. Multi-observation
sub-windows would add UI complexity without a Phase 4-compatible aggregation
to justify it.

## 11. Backend transformation design

`RuntimeFeatureTransformer.transform(traffic)`:

1. Reads practical fields (new snake_case keys; **old keys remain
   supported** so existing scripts/tests keep working).
2. Converts seconds → µs where required.
3. Applies the DIRECT → DERIVED-EXACT → DERIVED-CONSTANT →
   DERIVED-PROFILE order and writes each of the 138 slots.
4. Rebuilds the DataFrame in exact `feature_names.json` order; NaN/Inf guard
   unchanged.

The pipeline, `POST /forecast`, World Model, XAI, and MITRE are untouched.

## 12. Test cases

| ID | Scenario | Source |
|---|---|---|
| TC1 | Normal benign web traffic | benign-row-derived practical profile |
| TC2 | High-volume attack-like traffic | attack-row-derived practical profile |
| TC3 | SYN-heavy flood | practical profile |
| TC4 | Scanning-like (port diversity + RST) | practical profile |
| TC5 | Mixed benign + suspicious | practical profile |
| TC6 | Real benign Phase 4 row | SHAP background row (direct 138) |
| TC7 | Real attack Phase 4 row | SHAP background row (direct 138) |

Each case prints the transformed vector audit (shape, zeros, NaN, Inf), XGB /
RF / ensemble probabilities, threshold, state, World Model forecasts, XAI top
features, MITRE correlations, and the comparison table.

## 13. Risks and limitations

1. **Approximation risk.** IAT/rate/active-idle `_max` and `_std` variants
   are reconstructed from documented ratios, not measured. They are neutral
   (same rule for benign and attack inputs) and low-importance, but they are
   not exact.
2. **Out-of-distribution remains possible.** A user may still enter
   unrealistic magnitudes (e.g., SYN count > flow count). The form presets
   and tooltips mitigate this; the model still decides.
3. **The 120 s timeout / 1460 MTU constants** reflect the CIC-IDS2018
   capture environment; other environments may differ slightly.
4. **Honest expectations.** A practical profile is an approximation of a
   real window; probabilities will not exactly equal a dataset row. The
   goal is that benign profiles stay low and attack-like profiles move
   across the threshold when the described traffic genuinely is attack-like.
5. **No new model training.** All results continue to come from the frozen
   ensemble.