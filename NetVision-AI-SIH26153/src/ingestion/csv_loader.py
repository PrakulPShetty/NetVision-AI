"""CSV ingestion for CICFlowMeter exports and pre-aggregated profiles.

Three CSV shapes are recognised automatically:

1. **Raw CICFlowMeter flow CSV** (Phase 3 style) — one row per flow.
   Rows are aggregated into 5-minute windows with the Phase 4 semantics.
2. **Aggregated practical-profile CSV** — one row per window with the
   40 profile fields.
3. **Model-feature CSV** (bonus) — one row per window with exactly the
   138 Phase 4 feature columns. These rows bypass the transformer and go
   straight to the frozen ensemble through ``/forecast``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.ingestion.constants import (
    CANONICAL_MODEL_FEATURES,
    FEATURE_METADATA_NORMALIZED,
    FEATURE_SUFFIXES,
    MODEL_FEATURE_COUNT,
    OPTIONAL_FLOW_COLUMNS,
    PROFILE_FIELDS,
    REQUIRED_FLOW_COLUMNS,
    WINDOW_FEATURE_NORMALIZED,
    normalize_column,
    resolve_flow_column,
    resolve_model_feature,
    resolve_profile_field,
)
from src.ingestion.errors import (
    EmptyFileError,
    IngestionLimitError,
    MalformedFileError,
    UnsupportedFileTypeError,
)
from src.ingestion.profile_aggregator import (
    aggregate_flow_frame,
    parse_timestamp_series,
    profile_frame_to_windows,
)

_CSV_ENCODINGS: Tuple[str, ...] = ("utf-8-sig", "latin-1")
_DELIMITERS: Tuple[str, ...] = (",", ";", "\t", "|")


# ------------------------------------------------------------------
# Low-level CSV helpers
# ------------------------------------------------------------------


def _detect_delimiter(fileobj) -> str:
    position = fileobj.tell()
    fileobj.seek(0)
    sample = fileobj.readline()
    if isinstance(sample, bytes):
        sample = sample.decode("utf-8-sig", errors="replace")
    fileobj.seek(position)

    counts = {delimiter: sample.count(delimiter) for delimiter in _DELIMITERS}
    delimiter = max(counts, key=counts.get)
    return delimiter if counts[delimiter] > 0 else ","


def _read_header(fileobj) -> List[str]:
    delimiter = _detect_delimiter(fileobj)

    last_error: Optional[Exception] = None
    for encoding in _CSV_ENCODINGS:
        fileobj.seek(0)
        try:
            header = pd.read_csv(
                fileobj,
                sep=delimiter,
                nrows=0,
                encoding=encoding,
            )
            columns = [str(column).replace("\ufeff", "") for column in header.columns]
            if not columns:
                raise EmptyFileError("The CSV file has no header row.")
            return columns
        except EmptyFileError:
            raise
        except pd.errors.EmptyDataError as exc:
            raise EmptyFileError("The CSV file is empty.") from exc
        except Exception as exc:  # noqa: BLE001 - reported to the analyst
            last_error = exc

    raise MalformedFileError(
        f"Could not read the CSV header: {last_error}"
    )


def _read_selected(
    fileobj,
    columns: Sequence[str],
    *,
    max_rows: int,
) -> pd.DataFrame:
    """Read only the selected columns, with an explicit row limit."""

    delimiter = _detect_delimiter(fileobj)
    selected = set(columns)
    last_error: Optional[Exception] = None

    for encoding in _CSV_ENCODINGS:
        fileobj.seek(0)
        try:
            frame = pd.read_csv(
                fileobj,
                sep=delimiter,
                usecols=lambda name: name in selected,
                nrows=max_rows + 1,
                low_memory=False,
                encoding=encoding,
            )
            break
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.EmptyDataError as exc:
            raise EmptyFileError("The CSV file contains no data rows.") from exc
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    else:
        raise MalformedFileError(f"Could not read the CSV data: {last_error}")

    if frame is None or len(frame) == 0:
        raise EmptyFileError("The CSV file contains no data rows.")

    if len(frame) > max_rows:
        raise IngestionLimitError(
            f"The CSV contains more than {max_rows:,} rows. Split the file "
            "into smaller captures before uploading."
        )

    return frame


# ------------------------------------------------------------------
# Shape detection
# ------------------------------------------------------------------


def _flow_header_map(columns: Sequence[str]) -> Dict[str, str]:
    """Map canonical flow column -> original header (first match wins)."""

    mapping: Dict[str, str] = {}
    for column in columns:
        canonical = resolve_flow_column(column)
        if canonical and canonical not in mapping:
            mapping[canonical] = column
    return mapping


def _profile_header_map(columns: Sequence[str]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for column in columns:
        field = resolve_profile_field(column)
        if field and field not in mapping:
            mapping[field] = column
    return mapping


def _is_feature_column(column: str) -> bool:
    normalized = normalize_column(column)
    if normalized in FEATURE_METADATA_NORMALIZED:
        return False
    if normalized in WINDOW_FEATURE_NORMALIZED:
        return True
    text = str(column).strip().lower()
    return text.endswith(FEATURE_SUFFIXES)


def _feature_columns(columns: Sequence[str]) -> List[str]:
    return [column for column in columns if _is_feature_column(column)]


# ------------------------------------------------------------------
# Loaders
# ------------------------------------------------------------------


def load_cicflowmeter_csv(
    fileobj,
    *,
    max_rows: int,
    max_windows: int,
    header_columns: Sequence[str],
) -> Dict[str, Any]:
    flow_map = _flow_header_map(header_columns)

    missing = [column for column in REQUIRED_FLOW_COLUMNS if column not in flow_map]
    if missing:
        raise MalformedFileError(
            "The CSV looks like a CICFlowMeter export but is missing required "
            "columns: " + ", ".join(missing)
        )

    wanted = [
        column
        for column in (
            "Timestamp",
            *REQUIRED_FLOW_COLUMNS,
            *OPTIONAL_FLOW_COLUMNS,
            "Label",
        )
        if column in flow_map
    ]

    frame = _read_selected(
        fileobj,
        [flow_map[column] for column in wanted],
        max_rows=max_rows,
    )

    result = aggregate_flow_frame(
        frame,
        max_windows=max_windows,
    )

    return {
        "source_type": "cicflowmeter_csv",
        **result,
    }


def extract_profile_from_features_or_row(row_dict: Mapping[str, Any]) -> Dict[str, float]:
    """Given a dictionary of feature/profile columns, extract and synthesize the
    40 practical profile fields expected by the UI and RuntimeFeatureTransformer.
    """
    def _get(keys: Sequence[str], default: float = 0.0) -> float:
        for k in keys:
            if k in row_dict and row_dict[k] is not None and not pd.isna(row_dict[k]):
                try:
                    val = float(row_dict[k])
                    if np.isfinite(val):
                        return val
                except (ValueError, TypeError):
                    pass
        return default

    profile: Dict[str, float] = {}

    # S1 - Observation window
    fc = _get(["flow_count", "total_flow_count", "Tot Fwd Pkts_sum", "forward_packets"], default=1.0)
    profile["flow_count"] = max(1.0, fc)
    profile["unique_dst_ports"] = max(1.0, _get(["unique_dst_ports"], default=1.0))
    profile["unique_protocols"] = max(1.0, _get(["unique_protocols"], default=1.0))

    # S2 - Traffic volume (window totals)
    profile["forward_packets"] = _get(["forward_packets", "Tot Fwd Pkts_sum"], default=0.0)
    profile["backward_packets"] = _get(["backward_packets", "Tot Bwd Pkts_sum"], default=0.0)
    profile["forward_bytes"] = _get(["forward_bytes", "TotLen Fwd Pkts_sum"], default=0.0)
    profile["backward_bytes"] = _get(["backward_bytes", "TotLen Bwd Pkts_sum"], default=0.0)

    # S3 - Largest flow (peak per-flow)
    profile["max_fwd_packets_per_flow"] = _get(["max_fwd_packets_per_flow", "Tot Fwd Pkts_max"], default=0.0)
    profile["max_bwd_packets_per_flow"] = _get(["max_bwd_packets_per_flow", "Tot Bwd Pkts_max"], default=0.0)
    profile["max_fwd_bytes_per_flow"] = _get(["max_fwd_bytes_per_flow", "TotLen Fwd Pkts_max"], default=0.0)
    profile["max_bwd_bytes_per_flow"] = _get(["max_bwd_bytes_per_flow", "TotLen Bwd Pkts_max"], default=0.0)

    # S4 - Flow duration (convert from microseconds if > 1000)
    dur_mean = _get(["avg_flow_duration_sec", "Flow Duration_mean"], default=0.0)
    if dur_mean > 1000.0:
        dur_mean /= 1_000_000.0
    profile["avg_flow_duration_sec"] = dur_mean

    dur_max = _get(["max_flow_duration_sec", "Flow Duration_max"], default=0.0)
    if dur_max > 1000.0:
        dur_max /= 1_000_000.0
    profile["max_flow_duration_sec"] = max(dur_max, dur_mean)

    dur_min = _get(["min_flow_duration_sec", "Flow Duration_min"], default=0.0)
    if dur_min > 1000.0:
        dur_min /= 1_000_000.0
    profile["min_flow_duration_sec"] = dur_min

    # S5 - Packet profile (bytes)
    profile["avg_fwd_packet_size"] = _get(["avg_fwd_packet_size", "Fwd Pkt Len Mean_mean"], default=0.0)
    profile["avg_bwd_packet_size"] = _get(["avg_bwd_packet_size", "Bwd Pkt Len Mean_mean"], default=0.0)
    profile["max_fwd_packet_size"] = _get(["max_fwd_packet_size", "Fwd Pkt Len Max_max"], default=0.0)
    profile["max_bwd_packet_size"] = _get(["max_bwd_packet_size", "Bwd Pkt Len Max_max"], default=0.0)
    profile["min_fwd_packet_size"] = _get(["min_fwd_packet_size", "Fwd Pkt Len Min_min", "Fwd Pkt Len Min_mean"], default=0.0)
    profile["min_bwd_packet_size"] = _get(["min_bwd_packet_size", "Bwd Pkt Len Min_min", "Bwd Pkt Len Min_mean"], default=0.0)
    profile["pkt_len_std"] = _get(["pkt_len_std", "Pkt Len Std_mean"], default=0.0)

    # S6 - Traffic rates
    profile["avg_flow_bytes_per_sec"] = _get(["avg_flow_bytes_per_sec", "Flow Byts/s_mean"], default=0.0)
    profile["avg_flow_packets_per_sec"] = _get(["avg_flow_packets_per_sec", "Flow Pkts/s_mean"], default=0.0)
    profile["avg_bwd_packets_per_sec"] = _get(["avg_bwd_packets_per_sec", "Bwd Pkts/s_mean"], default=0.0)

    # S7 - Timing (IAT, convert microseconds if > 1000)
    iat_mean = _get(["avg_iat_sec", "Flow IAT Mean_mean"], default=0.0)
    if iat_mean > 1000.0:
        iat_mean /= 1_000_000.0
    profile["avg_iat_sec"] = iat_mean

    iat_std = _get(["iat_std_sec", "Flow IAT Std_mean"], default=0.0)
    if iat_std > 1000.0:
        iat_std /= 1_000_000.0
    profile["iat_std_sec"] = iat_std

    iat_max = _get(["max_iat_sec", "Flow IAT Max_max"], default=0.0)
    if iat_max > 1000.0:
        iat_max /= 1_000_000.0
    profile["max_iat_sec"] = iat_max

    bwd_iat = _get(["avg_bwd_iat_sec", "Bwd IAT Mean_mean"], default=0.0)
    if bwd_iat > 1000.0:
        bwd_iat /= 1_000_000.0
    profile["avg_bwd_iat_sec"] = bwd_iat

    # S8 - TCP Flags
    profile["syn_flag_cnt"] = _get(["syn_flag_cnt", "SYN Flag Cnt_sum"], default=0.0)
    profile["ack_flag_cnt"] = _get(["ack_flag_cnt", "ACK Flag Cnt_sum"], default=0.0)
    profile["rst_flag_cnt"] = _get(["rst_flag_cnt", "RST Flag Cnt_sum"], default=0.0)
    profile["fin_flag_cnt"] = _get(["fin_flag_cnt", "FIN Flag Cnt_sum"], default=0.0)
    profile["psh_flag_cnt"] = _get(["psh_flag_cnt", "PSH Flag Cnt_sum"], default=0.0)
    profile["urg_flag_cnt"] = _get(["urg_flag_cnt", "URG Flag Cnt_sum"], default=0.0)

    # S9 - TCP Profile
    profile["init_fwd_win_byts"] = _get(["init_fwd_win_byts", "Init Fwd Win Byts_mean"], default=0.0)
    profile["init_bwd_win_byts"] = _get(["init_bwd_win_byts", "Init Bwd Win Byts_mean"], default=0.0)
    profile["fwd_seg_size_min"] = _get(["fwd_seg_size_min", "Fwd Seg Size Min_mean"], default=0.0)

    # S10 - Activity / Idle (seconds)
    act_mean = _get(["active_mean_sec", "Active Mean_mean"], default=0.0)
    if act_mean > 1000.0:
        act_mean /= 1_000_000.0
    profile["active_mean_sec"] = act_mean

    idle_mean = _get(["idle_mean_sec", "Idle Mean_mean"], default=0.0)
    if idle_mean > 1000.0:
        idle_mean /= 1_000_000.0
    profile["idle_mean_sec"] = idle_mean

    # S11 - Network balance
    profile["down_up_ratio"] = _get(["down_up_ratio", "Down/Up Ratio_mean"], default=0.0)

    return profile


def load_profile_csv(
    fileobj,
    *,
    max_windows: int,
    header_columns: Sequence[str],
) -> Dict[str, Any]:
    profile_map = _profile_header_map(header_columns)
    timestamp_columns = [
        column
        for column in header_columns
        if normalize_column(column) in ("window start", "window end", "timestamp")
    ]

    selected = list(profile_map.values()) + timestamp_columns
    frame = _read_selected(fileobj, selected, max_rows=max_windows)

    # For missing profile fields, default gracefully to 0.0
    for field in PROFILE_FIELDS:
        if field not in profile_map:
            frame[field] = 0.0

    result = profile_frame_to_windows(
        frame,
        max_windows=max_windows,
    )

    missing = [field for field in PROFILE_FIELDS if field not in profile_map]
    warnings = list(result.get("warnings", []))
    if missing:
        warnings.append(
            f"Intelligently defaulted {len(missing)} missing profile field(s) to 0.0."
        )

    return {
        "source_type": "profile_csv",
        **result,
        "warnings": warnings,
    }


def load_feature_csv(
    fileobj,
    *,
    max_windows: int,
    header_columns: Sequence[str],
) -> Dict[str, Any]:
    """Load a feature-level CSV with any number of columns (e.g. 138, 186, etc.).

    Captures only the required 138 model features, defaults any missing ones
    to 0.0, ignores unneeded extra columns, and synthesizes a 40-field profile
    for frontend inspection.
    """
    feature_map: Dict[str, str] = {}
    for column in header_columns:
        canonical = resolve_model_feature(column)
        if canonical and canonical not in feature_map:
            feature_map[canonical] = column

    # If canonical resolution found none, fallback to generic suffix matching
    if not feature_map:
        for column in _feature_columns(header_columns):
            feature_map[column] = column

    timestamp_columns = [
        column
        for column in header_columns
        if normalize_column(column) in ("window start", "timestamp", "time")
    ]

    read_cols = list(set(list(feature_map.values()) + timestamp_columns))
    frame = _read_selected(fileobj, read_cols, max_rows=max_windows)

    timestamps = None
    if timestamp_columns:
        timestamps = parse_timestamp_series(frame[timestamp_columns[0]])

    cols_to_numeric = [col for col in feature_map.values() if col in frame.columns]
    numeric_frame = frame[cols_to_numeric].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    windows: List[Dict[str, Any]] = []
    matched_count = len(feature_map)
    extra_count = max(0, len(header_columns) - matched_count)
    missing_count = max(0, MODEL_FEATURE_COUNT - matched_count)

    warnings: List[str] = [
        f"Captured {matched_count} model features from {len(header_columns)} columns."
    ]
    if extra_count > 0:
        warnings.append(f"{extra_count} extra columns were safely ignored.")
    if missing_count > 0:
        warnings.append(
            f"{missing_count} of {MODEL_FEATURE_COUNT} model features were missing from the file and intelligently defaulted to 0.0."
        )
    warnings.append(
        "Synthesized 40-field practical profile ready for inspection and expansion via RuntimeFeatureTransformer."
    )

    for position, (_, row) in enumerate(numeric_frame.iterrows()):
        row_dict = {col: float(row[col]) for col in numeric_frame.columns}

        # Build exactly the 138 canonical features expected by the ensemble
        features: Dict[str, float] = {}
        for feat_name in CANONICAL_MODEL_FEATURES:
            if feat_name in feature_map:
                csv_col = feature_map[feat_name]
                val = row_dict.get(csv_col, 0.0)
                features[feat_name] = float(val) if np.isfinite(val) else 0.0
            else:
                features[feat_name] = 0.0

        # Synthesize the 40 practical profile fields for UI inspection & transformer expansion
        # if real traffic / flow features are present
        profile = extract_profile_from_features_or_row(row_dict)
        has_meaningful_profile = any(
            k in row_dict
            for k in (
                "Tot Fwd Pkts_sum", "forward_packets",
                "TotLen Fwd Pkts_sum", "forward_bytes",
                "Flow Duration_mean", "avg_flow_duration_sec",
                "SYN Flag Cnt_sum", "syn_flag_cnt",
            )
        )
        if not has_meaningful_profile:
            profile = None

        window_start = None
        window_end = None
        if timestamps is not None and not pd.isna(timestamps.iloc[position]):
            window_start = pd.Timestamp(timestamps.iloc[position]).isoformat(timespec="seconds")
            window_end = (pd.Timestamp(timestamps.iloc[position]) + pd.Timedelta(minutes=5)).isoformat(timespec="seconds")

        profile_fc = profile.get("flow_count", 1.0) if profile is not None else 1.0
        flow_count = int(float(features.get("flow_count", profile_fc)))
        if flow_count <= 0:
            flow_count = 1

        windows.append(
            {
                "index": position,
                "window_start": window_start,
                "window_end": window_end,
                "flow_count": flow_count,
                "label_counts": {},
                "attack_flow_count": None,
                "benign_flow_count": None,
                "profile": profile,
                "features": features,
            }
        )

    return {
        "source_type": "feature_csv",
        "windows": windows,
        "row_count": int(len(frame)),
        "used_row_count": int(len(frame)),
        "dropped_row_count": 0,
        "label_summary": {},
        "warnings": warnings,
        "feature_count": MODEL_FEATURE_COUNT,
    }


# ------------------------------------------------------------------
# Public entry point
# ------------------------------------------------------------------


def load_csv_file(
    fileobj,
    *,
    max_rows: int,
    max_windows: int,
) -> Dict[str, Any]:
    """Detect and load any supported CSV shape intelligently."""

    header_columns = _read_header(fileobj)

    # 1. Flow CSV detection
    flow_map = _flow_header_map(header_columns)
    has_flow_shape = any(
        key in flow_map
        for key in (
            "Tot Fwd Pkts",
            "Tot Bwd Pkts",
            "TotLen Fwd Pkts",
            "TotLen Bwd Pkts",
            "Flow Duration",
        )
    )
    is_temporal = any(str(col).strip().lower().endswith(FEATURE_SUFFIXES) for col in header_columns)

    if has_flow_shape and not is_temporal:
        return load_cicflowmeter_csv(
            fileobj,
            max_rows=max_rows,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    # 2. Practical Profile CSV detection (checked before feature CSV if full profile or no temporal suffixes)
    profile_map = _profile_header_map(header_columns)
    if all(field in profile_map for field in PROFILE_FIELDS) or (len(profile_map) >= 15 and not is_temporal):
        return load_profile_csv(
            fileobj,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    # 3. Model Feature CSV detection (any number of columns: 138, 186, etc.)
    matched_features = [col for col in header_columns if resolve_model_feature(col)]
    if len(matched_features) >= 5 or is_temporal:
        return load_feature_csv(
            fileobj,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    # 4. Partial Profile CSV fallback
    if len(profile_map) >= 3:
        return load_profile_csv(
            fileobj,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    # 4. Fallback if flow columns exist
    if has_flow_shape:
        return load_cicflowmeter_csv(
            fileobj,
            max_rows=max_rows,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    raise UnsupportedFileTypeError(
        f"Unrecognised CSV layout ({len(header_columns)} columns found). "
        "Upload a raw CICFlowMeter flow CSV, an aggregated practical profile CSV, "
        "or a model feature CSV."
    )
