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
    FEATURE_METADATA_NORMALIZED,
    FEATURE_SUFFIXES,
    MODEL_FEATURE_COUNT,
    OPTIONAL_FLOW_COLUMNS,
    PROFILE_FIELDS,
    REQUIRED_FLOW_COLUMNS,
    WINDOW_FEATURE_NORMALIZED,
    normalize_column,
    resolve_flow_column,
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

    selected = [profile_map[field] for field in PROFILE_FIELDS]
    selected.extend(timestamp_columns)

    frame = _read_selected(fileobj, selected, max_rows=max_windows)

    result = profile_frame_to_windows(
        frame,
        max_windows=max_windows,
    )

    return {
        "source_type": "profile_csv",
        **result,
    }


def load_feature_csv(
    fileobj,
    *,
    max_windows: int,
    header_columns: Sequence[str],
) -> Dict[str, Any]:
    feature_columns = _feature_columns(header_columns)
    if len(feature_columns) != MODEL_FEATURE_COUNT:
        raise MalformedFileError(
            f"Feature CSV detection found {len(feature_columns)} feature-like "
            f"columns; exactly {MODEL_FEATURE_COUNT} are required."
        )

    timestamp_columns = [
        column
        for column in header_columns
        if normalize_column(column) in ("window start", "timestamp")
    ]
    selected = feature_columns + timestamp_columns

    frame = _read_selected(fileobj, selected, max_rows=max_windows)

    timestamps = None
    if timestamp_columns:
        timestamps = parse_timestamp_series(frame[timestamp_columns[0]])

    numeric = frame[feature_columns].apply(pd.to_numeric, errors="coerce")
    bad_columns = [
        column for column in numeric.columns if not np.isfinite(numeric[column]).all()
    ]
    if bad_columns:
        raise MalformedFileError(
            "The feature CSV contains non-numeric or non-finite values in: "
            + ", ".join(bad_columns[:8])
            + (" ..." if len(bad_columns) > 8 else "")
        )

    windows: List[Dict[str, Any]] = []
    for position, (_, row) in enumerate(numeric.iterrows()):
        features = {column: float(row[column]) for column in feature_columns}

        window_start = None
        window_end = None
        if timestamps is not None and not pd.isna(timestamps.iloc[position]):
            window_start = pd.Timestamp(timestamps.iloc[position]).isoformat(
                timespec="seconds"
            )
            window_end = (
                pd.Timestamp(timestamps.iloc[position]) + pd.Timedelta(minutes=5)
            ).isoformat(timespec="seconds")

        windows.append(
            {
                "index": position,
                "window_start": window_start,
                "window_end": window_end,
                "flow_count": int(float(features.get("flow_count", 0.0))),
                "label_counts": {},
                "attack_flow_count": None,
                "benign_flow_count": None,
                "profile": None,
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
        "warnings": [
            "Model-feature rows bypass the practical-profile transformer and "
            "are scored directly by the frozen 138-feature contract."
        ],
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
    """Detect and load any supported CSV shape."""

    header_columns = _read_header(fileobj)

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

    if has_flow_shape:
        return load_cicflowmeter_csv(
            fileobj,
            max_rows=max_rows,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    profile_map = _profile_header_map(header_columns)
    if all(field in profile_map for field in PROFILE_FIELDS):
        return load_profile_csv(
            fileobj,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    feature_columns = _feature_columns(header_columns)
    if feature_columns:
        return load_feature_csv(
            fileobj,
            max_windows=max_windows,
            header_columns=header_columns,
        )

    if profile_map:
        missing = [field for field in PROFILE_FIELDS if field not in profile_map]
        raise MalformedFileError(
            "The CSV resembles a practical-profile export but is missing "
            f"{len(missing)} of the 40 required fields: "
            + ", ".join(missing[:10])
            + (" ..." if len(missing) > 10 else "")
        )

    raise UnsupportedFileTypeError(
        "Unrecognised CSV layout. Upload a raw CICFlowMeter flow CSV, an "
        "aggregated 40-field profile CSV, or a 138-feature Phase 4 CSV."
    )
