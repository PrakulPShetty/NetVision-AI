# File Ingestion Architecture

**Status:** Implemented  
**Scope:** Upload raw CICFlowMeter CSV files, PCAP/PCAPNG captures, aggregated
40-field profile CSVs, and 138-feature Phase 4 CSVs, then route the resulting
5-minute windows through the existing forecasting pipeline.

**Hard constraint honoured:** the ingestion layer does **not** modify the
trained models, the ensemble, `src/forecasting/*`, `src/features/runtime_transformer.py`,
`src/xai/*`, `src/mitre/*`, or the 138-feature contract. It is an input adapter
in front of the existing pipeline.

---

## 1. Why this layer exists

Before this change, the only runtime inputs were:

1. the 40-field practical traffic profile entered manually in the UI, and
2. a direct 138-feature model dictionary.

Analysts already hold the raw material those inputs summarize: CICFlowMeter
exports from the training pipeline and packet captures from a live or captured
network segment. The ingestion layer closes that gap without inventing a new
model contract:

```
raw flows / packets
        │
        ▼
5-minute observation windows
        │
        ├── 40-field practical profile ──► RuntimeFeatureTransformer ──► 138 features
        │                                                               │
        └── 138-feature Phase 4 row ────────────────────────────────────┤
                                                                        ▼
                                              existing ensemble → world model
                                              → SHAP → MITRE → unified forecast
```

The transformer and pipeline are reused verbatim. There is no second feature
engine and no alternate inference path.

---

## 2. Supported uploads

| Source type | Detection | What the user gets |
|---|---|---|
| Raw CICFlowMeter CSV | Flow-style headers such as `Tot Fwd Pkts`, `Flow Duration`, `Dst Port` | Rows are aggregated into 5-minute windows, each producing the 40-field profile |
| Aggregated profile CSV | All 40 practical profile fields are present as headers | Each row is treated as one observation window |
| 138-feature Phase 4 CSV | Exactly 138 feature-suffixed columns (`*_mean`, `*_max`, `*_min`, `*_sum`) plus four unsuffixed window fields | Each row bypasses the transformer and is scored directly |
| PCAP / PCAPNG | File magic (`d4 c3 b2 a1`, `a1 b2 c3 d4`, or the PCAPNG block header) | Packets are reconstructed into CICFlowMeter-style flows, then aggregated like a raw CSV |

Format detection is content-first. A `.csv` extension is not trusted and a
`.pcap` extension alone is not enough: the PCAP magic header must be present.
Compressed archives (`.zip`, `.gz`, `.tar`, …) are rejected with a clear
message so an analyst does not upload a file the server cannot inspect.

### Accepted column spellings

CICFlowMeter exports differ between the Java and Python versions and between
dataset releases. Headers are normalised (case, punctuation and whitespace
insensitive) and mapped onto canonical columns. Examples:

| Canonical | Accepted variants |
|---|---|
| `Dst Port` | `Destination Port`, `DstPort`, `DestinationPort` |
| `Tot Fwd Pkts` | `Total Fwd Packets`, `Total Forward Packets` |
| `TotLen Fwd Pkts` | `Total Length of Fwd Packets`, `Total Length Fwd Packets` |
| `Fwd Pkt Len Max` | `Fwd Packet Length Max`, `Fwd Paket Len Max` |
| `Flow Byts/s` | `Flow Bytes/s`, `Flow Bytes per Second` |
| `Init Fwd Win Byts` | `Init_Win_bytes_forward`, `Init Win Bytes Forward` |
| `Fwd Seg Size Min` | `min_seg_size_forward` |
| `SYN Flag Cnt` | `SYN Flag Count`, `SYN Flags` |
| `Label` | `Class`, `Attack Label` |

Duplicate canonical columns keep the first occurrence and emit a warning.

If a variant omits `Fwd Seg Size Min`, `Active Mean`, or `Idle Mean`, the
profile uses `0.0` for that field and records a warning. When `Down/Up Ratio`
is absent, the aggregator derives it from `backward_bytes / forward_bytes`
(falling back to `0.0` when forward bytes are also zero) and records that
assumption.

---

## 3. Window aggregation (Phase 4 semantics)

A raw flow table is grouped with the same key used to build the training
representation:

```python
window_key = Timestamp.dt.floor("5min")
```

Aggregation rules mirror Phase 4:

| Profile group | Source columns | Aggregation |
|---|---|---|
| Window size / diversity | `Dst Port`, `Protocol` | `nunique`; `flow_count` = group size |
| Volume totals | `Tot Fwd/Bwd Pkts`, `TotLen Fwd/Bwd Pkts` | `sum` |
| Largest flow | same columns | `max` |
| Flow duration | `Flow Duration` | `mean`, `min`, `max` (µs → s) |
| Packet profile | `Fwd/Bwd Pkt Len Mean/Min/Max`, `Pkt Len Std` | `mean` over per-flow columns |
| Rates | `Flow Byts/s`, `Flow Pkts/s`, `Bwd Pkts/s` | `mean` |
| Timing | `Flow IAT Mean/Std/Max`, `Bwd IAT Mean` | `mean` (µs → s) |
| TCP flags | `SYN/ACK/RST/FIN/PSH/URG Flag Cnt` | `sum` |
| TCP profile | `Init Fwd/Bwd Win Byts`, `Fwd Seg Size Min` | `mean` |
| Activity / idle | `Active Mean`, `Idle Mean` | `mean` (µs → s) |
| Balance | `Down/Up Ratio` | `mean` |

Timestamps are parsed tolerant of real exports:

1. Epoch seconds or milliseconds (numeric or numeric strings).
2. Day-first text such as `22/02/2018 08:00:00` (CIC-IDS2018 convention).
3. Month-first text such as `02/22/2018 08:00:00` when day-first resolves
   fewer rows.

Rows with an unparseable timestamp are dropped with a warning. If no timestamp
column exists at all, the whole file becomes one window and a warning explains
that assumption.

All windows are returned as naive UTC timestamps; no local-time conversion is
applied.

### Label handling

`Label`, `Class` and `Attack Label` are **metadata only**. They are summarized
per window (and globally) so an analyst can compare the capture against the
model output. They are never placed in the 40-field profile and never reach
the model. A row labelled `Attack` does not influence the forecast.

---

## 4. Profile and feature CSVs

### 40-field profile CSV

One row is one 5-minute window. Headers may use either the canonical snake_case
names (`avg_flow_duration_sec`) or friendly variants such as
`Average flow duration seconds`. An optional `window_start`, `window_end` or
`Timestamp` column is used only for display.

All 40 fields are required. The error message names the missing fields rather
than silently scoring a degenerate profile.

### 138-feature model CSV

This is the bonus fast path for exports of the Phase 4 temporal dataset. The
loader:

- excludes metadata columns such as `window_start`, `window_end`, `label`,
  `current_attack_state`, `future_attack_state`, and `attack_flow_count`;
- recognises the four unsuffixed window features (`flow_count`,
  `total_flow_count`, `unique_dst_ports`, `unique_protocols`) plus columns
  ending in `_mean`, `_max`, `_min`, `_sum`;
- requires exactly **138** such columns;
- rejects non-numeric or non-finite values before the API call.

These rows are passed to `pipeline.forecast(features)` directly. The runtime
transformer is not involved on this path.

---

## 5. PCAP / PCAPNG reconstruction

Packet captures do not contain CICFlowMeter flow records, so the layer
reconstructs approximate records using documented, conservative rules:

| Rule | Behaviour |
|---|---|
| Flow key | Bidirectional 5-tuple `(protocol, endpoint A, endpoint B)` |
| Direction | The first packet seen defines the forward direction |
| Idle timeout | A flow is finalised after 120 s without packets |
| Activity threshold | Active/idle bursts are split at gaps greater than 5 s |
| Packet length | IP total length excluding link-layer headers, capped at 1460 B |
| Standard deviation | Population standard deviation |
| TCP reassembly | None — retransmissions and out-of-order packets are counted as observed |
| Window assignment | Flow start timestamp (CICFlowMeter `Timestamp` semantics), not packet end time |
| Non-IP frames | Counted and skipped; the response reports the count |

Reconstructed records use exactly the canonical CICFlowMeter columns, so the
same Phase 4 aggregator is shared between CSV and PCAP paths.

### Consequences an analyst should know

- A flow that starts before a 5-minute boundary and continues after it is
  assigned entirely to the window containing its **start** time. This matches
  the training timestamp semantics, but it means a long-lived flow does not
  contribute to later windows.
- Because there is no stream reassembly, retransmissions can inflate packet and
  byte counters relative to a reassembled view.
- `Fwd Seg Size Min` uses the smallest observed TCP payload, not a negotiated
  MSS.
- `Init Fwd/Bwd Win Byts` uses the first observed advertised window per
  direction.

These approximations are also repeated in warnings on every PCAP response, so
the result is never presented as byte-exact CICFlowMeter output.

---

## 6. Limits and configuration

All limits are environment-configurable and enforced before expensive parsing
where possible:

| Variable | Default | Meaning |
|---|---|---|
| `NETVISION_MAX_UPLOAD_MB` | `200` | Maximum upload size |
| `NETVISION_MAX_CSV_ROWS` | `1_000_000` | Maximum raw CSV rows read |
| `NETVISION_MAX_PCAP_PACKETS` | `500_000` | Maximum packets parsed |
| `NETVISION_MAX_WINDOWS` | `500` | Maximum windows returned for preview/forecast |
| `NETVISION_WINDOW_MINUTES` | `5` | Window size (runtime contract is 5) |

Exceeding a limit raises a typed `IngestionLimitError` mapped to HTTP 413.
Empty files raise 422. Unsupported formats raise 415. Malformed files raise 422.

---

## 7. Error model

`src/ingestion/errors.py` defines user-correctable errors:

| Error | HTTP | Typical cause |
|---|---|---|
| `UnsupportedFileTypeError` | 415 | Binary file, archive, unknown CSV layout |
| `FileTooLargeError` | 413 | Upload above the configured size |
| `IngestionLimitError` | 413 | Row / packet / window limit |
| `EmptyFileError` | 422 | Zero-byte file or no usable rows/packets |
| `MalformedFileError` | 422 | Missing CICFlowMeter columns, corrupt PCAP, invalid feature row |

Unexpected exceptions stay 500s and are logged server-side. Analyst-facing
messages avoid stack traces and explain what to do next.

---

## 8. Backend integration

`backend/app/routes/ingestion.py` creates a router around the already
initialised pipeline:

- `POST /preprocess/file` — upload and inspect windows, no inference.
- `POST /forecast/file` — upload, choose a window, run the existing pipeline.

Both routes are multipart. Parsing runs in a thread pool so a large capture
does not block the event loop. The router is mounted in `backend/app/main.py`
with `app.include_router(create_ingestion_router(pipeline))`.

The ingestion package is independent of model construction:

```
src/ingestion/
├── __init__.py             public surface
├── constants.py            profile/flow contract, aliases, detection helpers
├── errors.py               typed HTTP-mapped errors
├── csv_loader.py           CSV shape detection and loading
├── profile_aggregator.py   Phase 4 aggregation and profile CSV conversion
├── pcap_flows.py           Scapy flow reconstruction
└── file_preprocessor.py    upload orchestration, limits, window selection
```

---

## 9. Frontend flow

`frontend/src/components/analysis/FileUploadPanel.jsx` sits on the Analyze
page:

1. Drop or choose a capture file.
2. The panel calls `POST /preprocess/file` and shows source type, file size,
   window count, packet/flow count, label distribution, and warnings.
3. The analyst selects any 5-minute window.
4. They can:
   - **Load into form** — populate the existing 40-field profile form for
     review and manual submission; or
   - **Analyze selected window** — submit the profile directly through the
     existing `POST /forecast`; or
   - **Analyze feature row** — for a 138-feature CSV, submit the row through
     the direct feature path.

The panel never computes predictions itself and never fabricates progress.
All results still come from the backend pipeline and feed the same global
analysis state used by the Forecast, Explain, and ATT&CK pages.

`frontend/src/services/upload.js` owns the multipart client and display
formatters. `frontend/src/services/api.js` owns the JSON forecasting calls,
including `submitFeatureForecast`.

---

## 10. Contract preservation checklist

- [x] 138-feature model contract unchanged.
- [x] `models/trained/*` artifacts untouched.
- [x] Ensemble weights, threshold, and world-model transitions untouched.
- [x] `RuntimeFeatureTransformer` reused, not replaced.
- [x] SHAP and MITRE mapping untouched.
- [x] Raw ingestion output is the existing 40-field practical profile.
- [x] Direct 138-feature CSV rows use the existing `pipeline.forecast`.
- [x] Labels never enter model inputs.
- [x] Upload limits prevent unbounded memory use.

---

## 11. Testing

`tests/test_file_ingestion.py` covers:

- Phase 4 aggregation arithmetic (sums, means, min/max, µs → s, ratio);
- header aliases and month-first timestamps;
- 40-field profile CSV ingestion;
- 138-feature CSV ingestion;
- no-timestamp single-window behaviour;
- upload, row, and window limits;
- invalid uploads and missing columns;
- window selection and payload mapping;
- PCAP and PCAPNG reconstruction;
- packet limits and non-IP skipping.

`tests/test_ingestion_api.py` covers the two multipart routes with a stub
pipeline, so it runs without trained artifacts.

These tests do not require `models/trained/*`; they exercise the ingestion
contract in isolation. End-to-end inference still requires the trained
artifacts and normal backend dependencies.

---

## 12. Known limitations / future work

- Live interface capture is not included; the feature works on uploaded files.
- PCAP flow reconstruction is approximate and intentionally documented as such.
- No TCP stream reassembly.
- No compressed-archive handling.
- No pagination beyond the configured window limit.
- The frontend holds the preprocessing result in component state; it is not
  persisted across page reloads.
