# NetVision AI — Forecasting API Specification

## 1. Overview

The NetVision AI Forecasting API provides HTTP endpoints for real-time cyber attack forecasting, health inspection, and multi-step temporal risk projection. The API accepts 5-minute practical traffic profiles (40 parameters) or raw capture files (PCAP/CSV), expands them via the Runtime Feature Transformer into the frozen 138-feature representation, evaluates the XGBoost + Random Forest SMOTE ensemble, propagates the state through the Markov World Model (10 to 60 minutes), and attaches probability-space SHAP feature attributions and MITRE ATT&CK behavioral mappings.

- **Base URL**: `http://127.0.0.1:8000`
- **Specification**: OpenAPI 3.1.0 (`/docs` for Swagger UI, `/redoc` for ReDoc)
- **Content Type**: `application/json` (or `multipart/form-data` for capture upload)

---

## 2. Endpoints Summary

| Method | Endpoint | Description | Content-Type |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Root service descriptor and version metadata | `application/json` |
| `GET` | `/health` | Engine status, loaded models, and feature counts | `application/json` |
| `POST` | `/forecast` | Single-window forecast from 40 practical traffic inputs | `application/json` |
| `POST` | `/forecast/file` | End-to-end file upload, ingestion, and forecast | `multipart/form-data` |
| `POST` | `/preprocess/file` | Ingests and inspects capture windows without running forecast | `multipart/form-data` |

---

## 3. Detailed Endpoint Specifications

### 3.1 `GET /` — Root Service Descriptor

Returns operational metadata, version info, and active documentation routes.

#### Request
```http
GET / HTTP/1.1
Host: 127.0.0.1:8000
Accept: application/json
```

#### Response (`200 OK`)
```json
{
  "service": "NetVision AI Attack Forecasting API",
  "status": "online",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

---

### 3.2 `GET /health` — Pipeline & Model Health

Verifies that the inference engine, trained model weights (`xgb_model.json`, `rf_smote_model.pkl`), World Model transition matrix, and SHAP explainer are loaded in memory and healthy.

#### Request
```http
GET /health HTTP/1.1
Host: 127.0.0.1:8000
Accept: application/json
```

#### Response (`200 OK`)
```json
{
  "status": "healthy",
  "engine": "ready",
  "models_loaded": {
    "xgboost": true,
    "random_forest": true,
    "world_model": true,
    "shap_explainer": true
  },
  "features_expected": 138,
  "ensemble_threshold": 0.40,
  "weights": {
    "xgboost": 0.50,
    "random_forest": 0.50
  }
}
```

---

### 3.3 `POST /forecast` — 40-Field Traffic Profile Forecast

Primary synchronous forecasting endpoint. Accepts a 5-minute aggregated traffic profile containing practical network metrics, transforms it via `RuntimeFeatureTransformer`, and outputs immediate threat assessment, 5 future forecasting horizons, top SHAP attributions, and MITRE ATT&CK recommendations.

#### Request Headers
- `Content-Type: application/json`
- `Accept: application/json`

#### Request Body Schema (`ForecastRequest`)
All numeric fields are optional in raw JSON (defaulting safely to `0.0` or standard domain defaults), but the full 40 practical parameters represent a standard observation window:

```json
{
  "flow_count": 50,
  "total_flow_count": 50,
  "forward_packets": 300,
  "backward_packets": 250,
  "forward_bytes": 20000,
  "backward_bytes": 18000,
  "flow_duration": 300000000,
  "flow_bytes_per_sec": 126.67,
  "flow_packets_per_sec": 1.83,
  "backward_packets_per_sec": 0.83,
  "flow_iat_mean": 6000000.0,
  "flow_iat_std": 1200000.0,
  "flow_iat_max": 15000000.0,
  "flow_iat_min": 1000.0,
  "fwd_iat_tot": 250000000.0,
  "fwd_iat_mean": 5000000.0,
  "fwd_iat_std": 1000000.0,
  "fwd_iat_max": 12000000.0,
  "fwd_iat_min": 2000.0,
  "bwd_iat_tot": 220000000.0,
  "bwd_iat_mean": 4500000.0,
  "bwd_iat_std": 900000.0,
  "bwd_iat_max": 10000000.0,
  "bwd_iat_min": 3000.0,
  "fwd_pkt_len_max": 1460,
  "fwd_pkt_len_min": 54,
  "fwd_pkt_len_mean": 66.67,
  "fwd_pkt_len_std": 120.5,
  "bwd_pkt_len_max": 1460,
  "bwd_pkt_len_min": 54,
  "bwd_pkt_len_mean": 72.0,
  "bwd_pkt_len_std": 135.2,
  "pkt_len_min": 54,
  "pkt_len_max": 1460,
  "pkt_len_mean": 69.09,
  "pkt_len_std": 128.4,
  "pkt_len_var": 16486.56,
  "pkt_size_avg": 69.09,
  "fwd_header_len": 6000,
  "bwd_header_len": 5000,
  "fwd_seg_size_min": 20,
  "init_fwd_win_byts": 29200,
  "init_bwd_win_byts": 29200,
  "fwd_psh_flags": 0,
  "fwd_urg_flags": 0,
  "fin_flag_cnt": 0,
  "syn_flag_cnt": 0,
  "rst_flag_cnt": 0,
  "psh_flag_cnt": 0,
  "ack_flag_cnt": 0,
  "urg_flag_cnt": 0,
  "ece_flag_cnt": 0,
  "cwe_flag_count": 0,
  "down_up_ratio": 0.83,
  "active_mean": 0.0,
  "active_std": 0.0,
  "active_max": 0.0,
  "active_min": 0.0,
  "idle_mean": 0.0,
  "idle_std": 0.0,
  "idle_max": 0.0,
  "idle_min": 0.0,
  "unique_dst_ports": 1,
  "unique_protocols": 1
}
```

#### Response (`200 OK`)
```json
{
  "current_assessment": {
    "attack_probability": 0.2968,
    "attack_state": "BENIGN",
    "decision_threshold": 0.40,
    "confidence_level": "High",
    "model_contributions": {
      "xgboost_probability": 0.2812,
      "random_forest_probability": 0.3124,
      "weights": {"xgb": 0.5, "rf": 0.5}
    }
  },
  "world_model_forecast": {
    "horizons": [
      {
        "horizon_step": 1,
        "horizon_label": "10_minutes",
        "attack_probability": 0.3214,
        "predicted_state": "BENIGN",
        "state_probabilities": {
          "BENIGN": 0.6786,
          "ATTACK": 0.3214
        }
      },
      {
        "horizon_step": 2,
        "horizon_label": "20_minutes",
        "attack_probability": 0.3421,
        "predicted_state": "BENIGN",
        "state_probabilities": {
          "BENIGN": 0.6579,
          "ATTACK": 0.3421
        }
      },
      {
        "horizon_step": 3,
        "horizon_label": "30_minutes",
        "attack_probability": 0.3580,
        "predicted_state": "BENIGN",
        "state_probabilities": {
          "BENIGN": 0.6420,
          "ATTACK": 0.3580
        }
      },
      {
        "horizon_step": 4,
        "horizon_label": "45_minutes",
        "attack_probability": 0.3695,
        "predicted_state": "BENIGN",
        "state_probabilities": {
          "BENIGN": 0.6305,
          "ATTACK": 0.3695
        }
      },
      {
        "horizon_step": 5,
        "horizon_label": "60_minutes",
        "attack_probability": 0.3778,
        "predicted_state": "BENIGN",
        "state_probabilities": {
          "BENIGN": 0.6222,
          "ATTACK": 0.3778
        }
      }
    ]
  },
  "explainability": {
    "method": "TreeExplainer (Probability-Space)",
    "base_value": 0.3631,
    "top_contributing_features": [
      {
        "feature": "Fwd Seg Size Min_mean",
        "display_name": "Minimum Segment Size (Fwd)",
        "value": 20.0,
        "shap_value": -0.0452,
        "impact": "Decreases Attack Risk"
      },
      {
        "feature": "Bwd Pkts/s_mean",
        "display_name": "Backward Packets Rate",
        "value": 0.83,
        "shap_value": -0.0381,
        "impact": "Decreases Attack Risk"
      }
    ]
  },
  "mitre_mapping": {
    "status": "No mapped techniques (Traffic is Benign)",
    "techniques": []
  }
}
```

---

### 3.4 `POST /forecast/file` — Ingest & Forecast File

Accepts an uploaded network traffic capture (`.pcap`, `.pcapng`, `.csv`), performs intelligent windowing, extracts features, and returns predictions across all parsed observation windows.

#### Request Headers
- `Content-Type: multipart/form-data`

#### Form Parameters
- `file`: Binary file stream (max 200 MB).
- `max_windows`: (Optional integer, default: 12) Maximum 5-minute windows to evaluate.
- `window_index`: (Optional integer, default: 0) Specific window to evaluate.

#### Curl Example
```bash
curl -X POST "http://127.0.0.1:8000/forecast/file" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@capture.pcap;type=application/octet-stream"
```

---

## 4. Error Codes & Handling

| Status Code | Error Key | Cause | Resolution |
| :--- | :--- | :--- | :--- |
| `400 Bad Request` | `EmptyFileError` | Uploaded file contains 0 bytes. | Provide a non-empty PCAP/CSV file. |
| `413 Payload Too Large` | `FileTooLargeError` | Uploaded file exceeds 200 MB limit. | Filter capture to a specific time interval. |
| `415 Unsupported Media Type`| `UnsupportedFileTypeError` | File is neither PCAP, PCAPNG, nor recognized CSV. | Provide standard CICFlowMeter CSV or libpcap capture. |
| `422 Unprocessable Entity`| `ValidationError` | Non-numeric value in profile fields. | Verify all traffic counts and metrics are numeric. |
| `500 Internal Server Error`| `PipelineExecutionError` | Unexpected runtime error in model or explainer. | Inspect server logs at `backend/app/main.py`. |
