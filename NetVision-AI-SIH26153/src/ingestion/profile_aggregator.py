"""Phase-4-compatible aggregation of flow records into 5-minute windows.

The aggregation mirrors the temporal representation used to train the
forecasting model (``notebooks/phase-4/04_CIC_IDS2018_Temporal_Representation``):

* window key: ``Timestamp.dt.floor("5min")``
* counts / volume: ``sum``, ``mean``, ``max``
* timing / packet / other: ``mean``, ``min``, ``max``
* rates / ratio: ``mean``, ``max`` (the 40-field profile keeps the mean)
* TCP flags: ``sum``, ``max``

The output of this module is always the existing 40-field practical
profile. ``RuntimeFeatureTransformer`` remains the only component that
expands a profile into the 138 model features.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from src.ingestion.constants import (
    PROFILE_FIELDS,
    REQUIRED_FLOW_COLUMNS,
    OPTIONAL_FLOW_COLUMNS,
    NUMERIC_FLOW_COLUMNS,
    resolve_flow_column,
    resolve_profile_field,
)
from src.ingestion.errors import (
    EmptyFileError,
    IngestionLimitError,
    MalformedFileError,
)

SECONDS_TO_MICROSECONDS = 1_000_000.0


# ------------------------------------------------------------------
# Normalisation helpers
# ------------------------------------------------------------------


def standardize_flow_frame(frame: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Rename raw headers to canonical flow columns.

    Duplicate canonical columns (a file containing both ``Tot Fwd Pkts``
    and ``Total Fwd Packets``) keep the first occurrence.
    """

    warnings: List[str] = []
    rename: Dict[str, str] = {}
    used: set = set()

    for column in frame.columns:
        canonical = resolve_flow_column(column)
        if not canonical:
            continue
        if canonical in used:
            warnings.append(
                f"Ignored duplicate column '{column}' "
                f"(canonical '{canonical}' already present)."
            )
            continue
        rename[column] = canonical
        used.add(canonical)

    frame = frame.rename(columns=rename)
    frame = frame.loc[:, ~frame.columns.duplicated()]
    return frame, warnings


def _coerce_numeric(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    """Convert columns to numeric in place, tolerating thousands separators."""

    for column in columns:
        if column not in frame.columns:
            continue
        series = frame[column]
        if series.dtype == object:
            series = (
                series.astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
        frame[column] = pd.to_numeric(series, errors="coerce")


def _parse_datetime_text(series: pd.Series, dayfirst: bool) -> pd.Series:
    """Parse mixed timestamp text, returning naive UTC timestamps."""

    try:
        parsed = pd.to_datetime(
            series,
            format="mixed",
            dayfirst=dayfirst,
            errors="coerce",
            utc=True,
        )
    except (TypeError, ValueError):
        parsed = pd.to_datetime(
            series,
            dayfirst=dayfirst,
            errors="coerce",
            utc=True,
        )
    return parsed.dt.tz_convert(None)


def parse_timestamp_series(series: pd.Series) -> Optional[pd.Series]:
    """Parse a ``Timestamp`` column into naive UTC ``datetime64`` values.

    CIC-IDS2018 exports use ``DD/MM/YYYY HH:MM``. Month-first files are
    also accepted: the parser tries day-first, then month-first, and keeps
    whichever interpretation resolves more rows.
    """

    if series is None or len(series) == 0:
        return None

    if pd.api.types.is_numeric_dtype(series):
        numeric = pd.to_numeric(series, errors="coerce")
        median = numeric.dropna().median()
        if pd.isna(median):
            return None
        unit = "ms" if median > 1e12 else "s"
        return pd.to_datetime(
            numeric,
            unit=unit,
            errors="coerce",
            utc=True,
        ).dt.tz_convert(None)

    text = series.astype(str).str.strip()

    # Some exports serialise epoch values as strings.
    numeric = pd.to_numeric(text, errors="coerce")
    if numeric.notna().mean() >= 0.9:
        median = numeric.dropna().median()
        if not pd.isna(median) and median > 1e9:
            unit = "ms" if median > 1e12 else "s"
            return pd.to_datetime(
                numeric,
                unit=unit,
                errors="coerce",
                utc=True,
            ).dt.tz_convert(None)

    parsed = _parse_datetime_text(text, dayfirst=True)
    if parsed.notna().mean() < 0.5:
        alternative = _parse_datetime_text(text, dayfirst=False)
        if alternative.notna().sum() > parsed.notna().sum():
            parsed = alternative

    return parsed


def _clean_number(value: Any) -> float:
    """Finite, non-negative float; invalid values become 0.0."""

    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0

    if not math.isfinite(number) or number < 0.0:
        return 0.0

    return number


def clean_profile(profile: Mapping[str, Any]) -> Dict[str, float]:
    """Project arbitrary values onto the frozen 40-field profile."""

    cleaned = {
        field: _clean_number(profile.get(field, 0.0)) for field in PROFILE_FIELDS
    }
    cleaned["flow_count"] = float(int(round(cleaned["flow_count"])))
    return cleaned


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(timestamp):
        return None
    return timestamp.isoformat(timespec="seconds")


# ------------------------------------------------------------------
# Flow-table aggregation
# ------------------------------------------------------------------


def aggregate_flow_frame(
    frame: pd.DataFrame,
    *,
    window_minutes: int = 5,
    max_windows: int = 500,
) -> Dict[str, Any]:
    """Aggregate a canonical flow table into 5-minute practical profiles.

    Parameters
    ----------
    frame:
        One row per flow. Headers are normalised onto ``FLOW_COLUMNS``.
    window_minutes:
        Model window size. Kept configurable for audit scripts; the
        runtime contract is 5 minutes.
    max_windows:
        Safety limit to keep uploads previewable.
    """

    if frame is None or len(frame) == 0:
        raise EmptyFileError("The uploaded file contains no flow rows.")

    frame, warnings = standardize_flow_frame(frame)

    missing = [column for column in REQUIRED_FLOW_COLUMNS if column not in frame]
    if missing:
        raise MalformedFileError(
            "The flow CSV is missing required CICFlowMeter columns: "
            + ", ".join(missing)
            + ". Supported headers include both 'Tot Fwd Pkts' and "
            "'Total Fwd Packets' spellings."
        )

    had_down_up_ratio = "Down/Up Ratio" in frame.columns

    for column in OPTIONAL_FLOW_COLUMNS:
        if column not in frame:
            frame[column] = 0.0
            if column == "Down/Up Ratio":
                warnings.append(
                    "Column 'Down/Up Ratio' is absent; deriving it from "
                    "backward_bytes / forward_bytes."
                )
            else:
                warnings.append(
                    f"Column '{column}' is absent; the profile uses 0.0 for it."
                )

    _coerce_numeric(frame, NUMERIC_FLOW_COLUMNS)

    # A label is metadata only. It is never sent to the model.
    if "Label" in frame.columns:
        frame["Label"] = frame["Label"].astype(str).str.strip()

    # ----------------------------------------------------------
    # Window key: Phase 4 uses Timestamp.dt.floor("5min").
    # ----------------------------------------------------------
    has_timestamps = False
    dropped_rows = 0

    if "Timestamp" in frame.columns:
        timestamps = parse_timestamp_series(frame["Timestamp"])
        if timestamps is not None and timestamps.notna().any():
            has_timestamps = True
            valid = timestamps.notna()
            dropped_rows = int((~valid).sum())
            if dropped_rows:
                warnings.append(
                    f"Dropped {dropped_rows:,} row(s) with an unparseable Timestamp."
                )
            frame = frame.loc[valid].copy()
            frame["__window_key__"] = timestamps.loc[valid].dt.floor(
                f"{window_minutes}min"
            )
            if len(frame) == 0:
                raise MalformedFileError(
                    "No rows have a parseable Timestamp. Expected values such as "
                    "'22/02/2018 08:00:00' or an epoch timestamp."
                )

    if not has_timestamps:
        frame["__window_key__"] = pd.Timestamp("1970-01-01 00:00:00")
        warnings.append(
            "No Timestamp column was found; the whole file is treated as one "
            "5-minute observation window."
        )

    grouped = frame.groupby("__window_key__", sort=True, dropna=False)

    if grouped.ngroups > max_windows:
        raise IngestionLimitError(
            f"The file produces {grouped.ngroups:,} five-minute windows; the "
            f"preview limit is {max_windows:,}. Split the capture into smaller "
            "files or narrow the time range."
        )

    # ----------------------------------------------------------
    # Aggregation (Phase 4 semantics)
    # ----------------------------------------------------------
    agg = pd.DataFrame(index=grouped.size().index)

    agg["flow_count"] = grouped.size()
    agg["unique_dst_ports"] = grouped["Dst Port"].nunique()
    agg["unique_protocols"] = grouped["Protocol"].nunique()

    # Counts / volume: sum, mean, max.
    agg["forward_packets"] = grouped["Tot Fwd Pkts"].sum()
    agg["backward_packets"] = grouped["Tot Bwd Pkts"].sum()
    agg["forward_bytes"] = grouped["TotLen Fwd Pkts"].sum()
    agg["backward_bytes"] = grouped["TotLen Bwd Pkts"].sum()

    agg["max_fwd_packets_per_flow"] = grouped["Tot Fwd Pkts"].max()
    agg["max_bwd_packets_per_flow"] = grouped["Tot Bwd Pkts"].max()
    agg["max_fwd_bytes_per_flow"] = grouped["TotLen Fwd Pkts"].max()
    agg["max_bwd_bytes_per_flow"] = grouped["TotLen Bwd Pkts"].max()

    # Timing: mean / min / max. CICFlowMeter stores microseconds.
    agg["avg_flow_duration_sec"] = (
        grouped["Flow Duration"].mean() / SECONDS_TO_MICROSECONDS
    )
    agg["max_flow_duration_sec"] = (
        grouped["Flow Duration"].max() / SECONDS_TO_MICROSECONDS
    )
    agg["min_flow_duration_sec"] = (
        grouped["Flow Duration"].min() / SECONDS_TO_MICROSECONDS
    )

    # Packet profile: Phase 4 uses AVG over the per-flow columns.
    agg["avg_fwd_packet_size"] = grouped["Fwd Pkt Len Mean"].mean()
    agg["avg_bwd_packet_size"] = grouped["Bwd Pkt Len Mean"].mean()
    agg["max_fwd_packet_size"] = grouped["Fwd Pkt Len Max"].mean()
    agg["max_bwd_packet_size"] = grouped["Bwd Pkt Len Max"].mean()
    agg["min_fwd_packet_size"] = grouped["Fwd Pkt Len Min"].mean()
    agg["min_bwd_packet_size"] = grouped["Bwd Pkt Len Min"].mean()
    agg["pkt_len_std"] = grouped["Pkt Len Std"].mean()

    # Rates / ratio: mean.
    agg["avg_flow_bytes_per_sec"] = grouped["Flow Byts/s"].mean()
    agg["avg_flow_packets_per_sec"] = grouped["Flow Pkts/s"].mean()
    agg["avg_bwd_packets_per_sec"] = grouped["Bwd Pkts/s"].mean()

    # IAT: mean / std / max, microseconds -> seconds.
    agg["avg_iat_sec"] = grouped["Flow IAT Mean"].mean() / SECONDS_TO_MICROSECONDS
    agg["iat_std_sec"] = grouped["Flow IAT Std"].mean() / SECONDS_TO_MICROSECONDS
    agg["max_iat_sec"] = grouped["Flow IAT Max"].mean() / SECONDS_TO_MICROSECONDS
    agg["avg_bwd_iat_sec"] = (
        grouped["Bwd IAT Mean"].mean() / SECONDS_TO_MICROSECONDS
    )

    # TCP flags: sum, max (the profile keeps the sum).
    for flag, column in (
        ("syn_flag_cnt", "SYN Flag Cnt"),
        ("ack_flag_cnt", "ACK Flag Cnt"),
        ("rst_flag_cnt", "RST Flag Cnt"),
        ("fin_flag_cnt", "FIN Flag Cnt"),
        ("psh_flag_cnt", "PSH Flag Cnt"),
        ("urg_flag_cnt", "URG Flag Cnt"),
    ):
        agg[flag] = grouped[column].sum()

    # TCP profile: mean.
    agg["init_fwd_win_byts"] = grouped["Init Fwd Win Byts"].mean()
    agg["init_bwd_win_byts"] = grouped["Init Bwd Win Byts"].mean()
    agg["fwd_seg_size_min"] = grouped["Fwd Seg Size Min"].mean()

    # Activity / idle: mean, microseconds -> seconds.
    agg["active_mean_sec"] = (
        grouped["Active Mean"].mean() / SECONDS_TO_MICROSECONDS
    )
    agg["idle_mean_sec"] = grouped["Idle Mean"].mean() / SECONDS_TO_MICROSECONDS

    # Network balance: mean.
    agg["down_up_ratio"] = grouped["Down/Up Ratio"].mean()
    # If a variant omits the ratio, derive it from the window totals.
    missing_ratio = agg["down_up_ratio"].isna() | (not had_down_up_ratio)
    if missing_ratio.any():
        derived = agg["backward_bytes"] / agg["forward_bytes"].replace(0, np.nan)
        agg.loc[missing_ratio, "down_up_ratio"] = derived[missing_ratio]

    # ----------------------------------------------------------
    # Optional label metadata (never a model input)
    # ----------------------------------------------------------
    label_counts_by_window: Dict[Any, Dict[str, int]] = {}
    label_summary: Dict[str, int] = {}

    if "Label" in frame.columns:
        label_frame = frame.loc[frame["Label"].notna()].copy()
        label_frame["Label"] = label_frame["Label"].replace(
            {"": "UNKNOWN", "nan": "UNKNOWN", "None": "UNKNOWN"}
        )
        label_group = label_frame.groupby(
            ["__window_key__", "Label"], sort=True
        ).size()
        for (window_key, label), count in label_group.items():
            label_counts_by_window.setdefault(window_key, {})[str(label)] = int(
                count
            )
            label_summary[str(label)] = label_summary.get(str(label), 0) + int(
                count
            )

    # ----------------------------------------------------------
    # Serialise windows
    # ----------------------------------------------------------
    windows: List[Dict[str, Any]] = []

    for index, (window_key, row) in enumerate(agg.iterrows()):
        profile = clean_profile(row.to_dict())

        label_counts = label_counts_by_window.get(window_key, {})
        if label_counts:
            attack_flow_count = sum(
                count
                for label, count in label_counts.items()
                if label.strip().lower() != "benign"
            )
            benign_flow_count = sum(
                count
                for label, count in label_counts.items()
                if label.strip().lower() == "benign"
            )
        else:
            attack_flow_count = None
            benign_flow_count = None

        if has_timestamps:
            window_start = _iso(window_key)
            window_end = _iso(
                pd.Timestamp(window_key) + pd.Timedelta(minutes=window_minutes)
            )
        else:
            window_start = None
            window_end = None

        windows.append(
            {
                "index": index,
                "window_start": window_start,
                "window_end": window_end,
                "flow_count": int(profile["flow_count"]),
                "label_counts": label_counts,
                "attack_flow_count": attack_flow_count,
                "benign_flow_count": benign_flow_count,
                "profile": profile,
            }
        )

    return {
        "windows": windows,
        "row_count": int(len(frame) + dropped_rows),
        "used_row_count": int(len(frame)),
        "dropped_row_count": dropped_rows,
        "label_summary": label_summary,
        "warnings": warnings,
    }


# ------------------------------------------------------------------
# Already-aggregated 40-field profile CSV
# ------------------------------------------------------------------


def profile_frame_to_windows(
    frame: pd.DataFrame,
    *,
    window_minutes: int = 5,
    max_windows: int = 500,
) -> Dict[str, Any]:
    """Convert a CSV of pre-aggregated 40-field profiles into windows.

    Each row is one observation window. A ``window_start`` / ``timestamp``
    column is optional and used only for display.
    """

    if frame is None or len(frame) == 0:
        raise EmptyFileError("The profile CSV contains no rows.")

    warnings: List[str] = []
    rename: Dict[str, str] = {}
    used: set = set()

    for column in frame.columns:
        field = resolve_profile_field(column)
        if field and field not in used:
            rename[column] = field
            used.add(field)

    frame = frame.rename(columns=rename)

    missing = [field for field in PROFILE_FIELDS if field not in frame.columns]
    if missing:
        raise MalformedFileError(
            "The profile CSV does not contain all 40 practical profile fields. "
            "Missing: " + ", ".join(missing)
        )

    if len(frame) > max_windows:
        raise IngestionLimitError(
            f"The profile CSV contains {len(frame):,} rows; the preview limit "
            f"is {max_windows:,} windows."
        )

    # Optional display timestamp.
    timestamp_column = ""
    for candidate in ("window_start", "window_end", "Timestamp", "timestamp"):
        if candidate in frame.columns:
            timestamp_column = candidate
            break

    timestamps = None
    if timestamp_column:
        timestamps = parse_timestamp_series(frame[timestamp_column])
        if timestamps is None:
            warnings.append(
                f"Could not parse '{timestamp_column}'; window times are omitted."
            )

    _coerce_numeric(frame, [field for field in PROFILE_FIELDS])

    windows: List[Dict[str, Any]] = []
    for position, (_, row) in enumerate(frame.iterrows()):
        profile = clean_profile(row.to_dict())

        window_start = None
        window_end = None
        if timestamps is not None and not pd.isna(timestamps.iloc[position]):
            window_start = _iso(timestamps.iloc[position])
            window_end = _iso(
                pd.Timestamp(timestamps.iloc[position])
                + pd.Timedelta(minutes=window_minutes)
            )

        windows.append(
            {
                "index": position,
                "window_start": window_start,
                "window_end": window_end,
                "flow_count": int(profile["flow_count"]),
                "label_counts": {},
                "attack_flow_count": None,
                "benign_flow_count": None,
                "profile": profile,
            }
        )

    return {
        "windows": windows,
        "row_count": int(len(frame)),
        "used_row_count": int(len(frame)),
        "dropped_row_count": 0,
        "label_summary": {},
        "warnings": warnings,
    }
