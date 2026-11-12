# File Ingestion API

**Base URL (local):** `http://127.0.0.1:8000`  
**Content type:** `multipart/form-data`  
**Interactive schema:** `/docs` (FastAPI/OpenAPI)

Two endpoints are added by the ingestion router. They do not replace
`POST /forecast`; they prepare or select a 5-minute window and then reuse the
existing pipeline.

---

## 1. `POST /preprocess/file`

Upload a capture and receive its 5-minute observation windows. **No model
inference is performed.**

### Form fields

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | yes | Raw CICFlowMeter CSV, PCAP/PCAPNG capture, aggregated 40-field profile CSV, or 138-feature Phase 4 CSV |

The backend detects the format from file content and headers, not just the
extension.

### Example

```bash
curl -X POST http://127.0.0.1:8000/preprocess/file \
  -F "file=@flows.csv"
```

```bash
curl -X POST http://127.0.0.1:8000/preprocess/file \
  -F "file=@capture.pcapng"
```

### Response — raw flow CSV

```json
{
  "source_type": "cicflowmeter_csv",
  "filename": "flows.csv",
  "file_size_bytes": 184320,
  "generated_at": "2026-11-12T14:05:00+00:00",
  "window_seconds": 300,
  "window_count": 12,
  "profile_field_count": 40,
  "model_feature_count": 138,
  "row_count": 8421,
  "used_row_count": 8421,
  "dropped_row_count": 0,
  "label_summary": {
    "Benign": 8200,
    "DoS attacks-Hulk": 221
  },
  "warnings": [],
  "has_profiles": true,
  "has_features": false,
  "windows": [
    {
      "index": 0,
      "window_start": "2018-02-22T08:00:00",
      "window_end": "2018-02-22T08:05:00",
      "flow_count": 702,
      "label_counts": { "Benign": 702 },
      "attack_flow_count": 0,
      "benign_flow_count": 702,
      "profile": {
        "flow_count": 702,
        "unique_dst_ports": 41,
        "unique_protocols": 3,
        "forward_packets": 18342,
        "backward_packets": 20118,
        "forward_bytes": 1048224,
        "backward_bytes": 2884910,
        "max_fwd_packets_per_flow": 812,
        "max_bwd_packets_per_flow": 901,
        "max_fwd_bytes_per_flow": 48620,
        "max_bwd_bytes_per_flow": 77120,
        "avg_flow_duration_sec": 12.41,
        "max_flow_duration_sec": 119.98,
        "min_flow_duration_sec": 0.0,
        "avg_fwd_packet_size": 57.1,
        "avg_bwd_packet_size": 143.4,
        "max_fwd_packet_size": 1460.0,
        "max_bwd_packet_size": 1460.0,
        "min_fwd_packet_size": 0.0,
        "min_bwd_packet_size": 0.0,
        "pkt_len_std": 411.2,
        "avg_flow_bytes_per_sec": 62018.4,
        "avg_flow_packets_per_sec": 92.1,
        "avg_bwd_packets_per_sec": 48.7,
        "avg_iat_sec": 4.12,
        "iat_std_sec": 9.82,
        "max_iat_sec": 119.4,
        "avg_bwd_iat_sec": 0.53,
        "syn_flag_cnt": 688,
        "ack_flag_cnt": 701,
        "rst_flag_cnt": 2,
        "fin_flag_cnt": 640,
        "psh_flag_cnt": 402,
        "urg_flag_cnt": 0,
        "init_fwd_win_byts": 8700.0,
        "init_bwd_win_byts": 24120.0,
        "fwd_seg_size_min": 17.0,
        "active_mean_sec": 0.13,
        "idle_mean_sec": 4.8,
        "down_up_ratio": 2.75
      }
    }
  ]
}
```

`profile` always contains exactly the 40 practical fields. Values are
non-negative finite numbers; durations and inter-arrival times are in seconds.

### Additional fields for PCAP / PCAPNG

```json
{
  "source_type": "pcapng",
  "packet_count": 481233,
  "ip_packet_count": 479901,
  "skipped_non_ip_packet_count": 1332,
  "capture_start": "2018-02-22T08:00:00",
  "capture_end": "2018-02-22T09:00:00",
  "row_count": 9042,
  "warnings": [
    "PCAP flows are reconstructed approximately: 120 s idle timeout, 5 s activity threshold, no TCP stream reassembly, and IP packet lengths capped at 1460 B."
  ]
}
```

`row_count` for a capture is the number of reconstructed flows; `packet_count`
is the number of packets read.

### Response — 138-feature CSV

```json
{
  "source_type": "feature_csv",
  "has_profiles": false,
  "has_features": true,
  "feature_count": 138,
  "windows": [
    {
      "index": 0,
      "window_start": "2018-02-22T08:00:00",
      "window_end": "2018-02-22T08:05:00",
      "flow_count": 702,
      "label_counts": {},
      "attack_flow_count": null,
      "benign_flow_count": null,
      "profile": null,
      "features": {
        "flow_count": 702,
        "...": "136 more model features"
      }
    }
  ]
}
```

Exactly one of `profile` or `features` is non-null per window.

### Response — aggregated 40-field profile CSV

```json
{
  "source_type": "profile_csv",
  "has_profiles": true,
  "has_features": false,
  "window_count": 24,
  "windows": [
    {
      "index": 0,
      "window_start": "2018-02-22T08:00:00",
      "window_end": "2018-02-22T08:05:00",
      "flow_count": 500,
      "profile": { "flow_count": 500, "...": "39 more fields" }
    }
  ]
}
```

### Shared window fields

| Field | Description |
|---|---|
| `index` | Zero-based position; use this value as `window_index` |
| `window_start` / `window_end` | Naive UTC ISO timestamps, or `null` when the file had no timestamps |
| `flow_count` | Flows contributing to the window |
| `label_counts` | Source-label distribution (metadata only) |
| `attack_flow_count` / `benign_flow_count` | Label-derived counts, or `null` when labels are absent |
| `profile` | 40 practical fields, or `null` for a feature CSV |
| `features` | 138 model features, or `null` for a profile/raw CSV |

### Warnings

`warnings` is always present and may include:

- missing optional flow columns defaulted to `0.0`;
- unparseable timestamps that were dropped;
- no timestamp column found (whole file treated as one window);
- duplicate canonical columns ignored;
- the standard PCAP approximation notice.

Warnings are informational; they do not invalidate the response.

---

## 2. `POST /forecast/file`

Upload a capture, select one window, and run the **existing** forecasting
pipeline on it.

### Form fields

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | yes | Same formats as `/preprocess/file` |
| `window_index` | integer | no (default `0`) | Zero-based window index from `/preprocess/file` |

### Example

```bash
curl -X POST http://127.0.0.1:8000/forecast/file \
  -F "file=@capture.pcap" \
  -F "window_index=3"
```

### Response

```json
{
  "source_type": "pcap",
  "filename": "capture.pcap",
  "window_index": 3,
  "window_start": "2018-02-22T08:15:00",
  "window_end": "2018-02-22T08:20:00",
  "flow_count": 812,
  "mode": "profile",
  "forecast": {
    "ml": {
      "xgb_attack_probability": 0.91,
      "rf_attack_probability": 0.88,
      "ensemble_attack_probability": 0.895,
      "decision_threshold": 0.4,
      "predicted_current_state": "ATTACK",
      "current_state": 1,
      "current_state_label": "ATTACK"
    },
    "world_model": {
      "current_state": "ATTACK",
      "forecasts": [
        {
          "horizon_minutes": 10,
          "steps": 2,
          "future_attack_probability": 0.93,
          "future_benign_probability": 0.07,
          "attack_probability": 0.93,
          "state": "ATTACK",
          "forecast_state": "ATTACK"
        }
      ],
      "horizons": { "10_minutes": { "...": "same item" } }
    },
    "xai": { "...": "SHAP explanation payload" },
    "mitre_attack": { "...": "ATT&CK mapping payload" },
    "input": {
      "type": "practical_traffic",
      "feature_count": 138,
      "runtime_transformation": "RuntimeFeatureTransformer"
    }
  }
}
```

`mode` is:

- `"profile"` — the window contains a 40-field profile. The router calls
  `pipeline.forecast_from_traffic(profile)`, which invokes the runtime
  transformer.
- `"features"` — the window came from a 138-feature CSV. The router calls
  `pipeline.forecast(features)` directly.

The `forecast` object is the unchanged unified pipeline response. Its fields
are documented in `docs/PROJECT_COMPLETE_TECHNICAL_DOCUMENTATION.md`.

---

## 3. Error responses

Errors use FastAPI's standard shape:

```json
{ "detail": "Human-readable explanation." }
```

| Status | Meaning | Example detail |
|---|---|---|
| `413` | Upload or processing limit exceeded | `The uploaded file is 312.4 MB; the limit is 200.0 MB...` |
| `415` | Unsupported file type | `The upload looks like a binary file, not a CSV, PCAP or PCAPNG capture.` |
| `422` | Empty / malformed / out-of-range input | `window_index 99 is outside the available range 0..11.` |
| `500` | Unexpected server failure | Logged server-side; response says preprocessing/forecast failed |

Specific 422 cases include:

- empty file;
- unknown CSV layout;
- missing required CICFlowMeter columns;
- more than the configured number of windows;
- feature CSV with a column count other than 138;
- non-numeric or non-finite feature values;
- `window_index` outside the available range.

---

## 4. Limits

Defaults (override with environment variables):

| Variable | Default |
|---|---|
| `NETVISION_MAX_UPLOAD_MB` | 200 |
| `NETVISION_MAX_CSV_ROWS` | 1,000,000 |
| `NETVISION_MAX_PCAP_PACKETS` | 500,000 |
| `NETVISION_MAX_WINDOWS` | 500 |
| `NETVISION_WINDOW_MINUTES` | 5 |

---

## 5. Operational notes

- Both endpoints parse uploads off the event loop via a thread pool.
- Uploaded file handles are closed in a `finally` block.
- Labels and timestamps are metadata; they never enter the 138-feature model
  input.
- `POST /preprocess/file` is safe to call before deciding whether to forecast;
  it performs no inference.
- The router is constructed with the already-initialised pipeline. There is no
  model loading, retraining, or artifact write during a request.
