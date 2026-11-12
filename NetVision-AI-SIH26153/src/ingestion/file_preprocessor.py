"""Upload orchestration: detect file type, parse, aggregate, summarise.

The FastAPI layer stays thin: it hands a seekable file object to
``preprocess_upload`` and maps ``IngestionError`` onto HTTP status codes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from src.ingestion.constants import (
    MODEL_FEATURE_COUNT,
    PROFILE_FIELD_COUNT,
    WINDOW_MINUTES,
)
from src.ingestion.csv_loader import load_csv_file
from src.ingestion.errors import (
    EmptyFileError,
    FileTooLargeError,
    IngestionError,
    MalformedFileError,
    UnsupportedFileTypeError,
)
from src.ingestion.pcap_flows import (
    extract_flow_frame,
    looks_like_pcap,
)
from src.ingestion.profile_aggregator import aggregate_flow_frame

PCAP_SUFFIXES = frozenset({".pcap", ".pcapng", ".cap", ".pcapng.gz"})


def _env_int(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return default
    return max(value, minimum)


@dataclass(frozen=True)
class IngestionSettings:
    """Limits and window configuration for one upload."""

    max_upload_bytes: int = 200 * 1024 * 1024
    max_csv_rows: int = 1_000_000
    max_pcap_packets: int = 500_000
    max_windows: int = 500
    window_minutes: int = WINDOW_MINUTES

    @classmethod
    def from_env(cls) -> "IngestionSettings":
        return cls(
            max_upload_bytes=_env_int(
                "NETVISION_MAX_UPLOAD_MB", 200
            )
            * 1024
            * 1024,
            max_csv_rows=_env_int("NETVISION_MAX_CSV_ROWS", 1_000_000),
            max_pcap_packets=_env_int(
                "NETVISION_MAX_PCAP_PACKETS", 500_000
            ),
            max_windows=_env_int("NETVISION_MAX_WINDOWS", 500),
            window_minutes=_env_int("NETVISION_WINDOW_MINUTES", WINDOW_MINUTES),
        )


def _file_size(fileobj) -> int:
    position = fileobj.tell()
    fileobj.seek(0, os.SEEK_END)
    size = int(fileobj.tell())
    fileobj.seek(position)
    return size


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} bytes"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def preprocess_upload(
    fileobj,
    filename: Optional[str],
    *,
    settings: Optional[IngestionSettings] = None,
) -> Dict[str, Any]:
    """Parse an uploaded capture and return 5-minute windows.

    Returns a JSON-serialisable dictionary containing the source type,
    file metadata, warnings, and one entry per window. Each window carries
    either a 40-field practical ``profile`` or a 138-key ``features``
    dictionary.
    """

    settings = settings or IngestionSettings.from_env()
    filename = Path(filename or "upload").name or "upload"

    try:
        size = _file_size(fileobj)
    except (AttributeError, OSError):
        size = 0

    if size == 0:
        raise EmptyFileError("The uploaded file is empty.")

    if size > settings.max_upload_bytes:
        raise FileTooLargeError(
            f"The uploaded file is {_format_size(size)}; the limit is "
            f"{_format_size(settings.max_upload_bytes)}. Split the capture "
            "or raise NETVISION_MAX_UPLOAD_MB on the server."
        )

    fileobj.seek(0)
    prefix = fileobj.read(8) or b""
    fileobj.seek(0)

    suffix = Path(filename).suffix.lower()
    is_pcap = looks_like_pcap(prefix)

    if suffix in {".gz", ".zip", ".tar", ".7z", ".rar"}:
        raise UnsupportedFileTypeError(
            "Compressed archives are not supported. Decompress the capture "
            "and upload the CSV, PCAP or PCAPNG file directly."
        )

    warnings: list = []

    if is_pcap:
        source_type = "pcapng" if prefix[:4] == b"\x0a\x0d\x0d\x0a" else "pcap"
        try:
            frame, packet_stats = extract_flow_frame(
                fileobj,
                max_packets=settings.max_pcap_packets,
            )
        except IngestionError:
            raise
        except Exception as exc:  # noqa: BLE001 - scapy raises many types
            raise MalformedFileError(
                f"Could not parse the packet capture: {exc}"
            ) from exc
        aggregated = aggregate_flow_frame(
            frame,
            window_minutes=settings.window_minutes,
            max_windows=settings.max_windows,
        )
        warnings.extend(aggregated.get("warnings", []))
        warnings.append(
            "PCAP flows are reconstructed approximately: 120 s idle timeout, "
            "5 s activity threshold, no TCP stream reassembly, and IP packet "
            "lengths capped at 1460 B."
        )
        row_count = packet_stats["flow_count"]
        used_row_count = aggregated.get("used_row_count", row_count)
        dropped_row_count = aggregated.get("dropped_row_count", 0)
        label_summary = aggregated.get("label_summary", {})
        windows = aggregated["windows"]
        extra = {
            "packet_count": packet_stats["packet_count"],
            "ip_packet_count": packet_stats["ip_packet_count"],
            "skipped_non_ip_packet_count": packet_stats["skipped_non_ip"],
            "capture_start": packet_stats["first_timestamp"],
            "capture_end": packet_stats["last_timestamp"],
        }
    else:
        if suffix in PCAP_SUFFIXES:
            raise MalformedFileError(
                "The file name suggests a packet capture, but the file does "
                "not start with a valid PCAP/PCAPNG header."
            )

        if b"\x00" in prefix:
            raise UnsupportedFileTypeError(
                "The upload looks like a binary file, not a CSV, PCAP or "
                "PCAPNG capture."
            )

        loaded = load_csv_file(
            fileobj,
            max_rows=settings.max_csv_rows,
            max_windows=settings.max_windows,
        )
        source_type = loaded["source_type"]
        warnings.extend(loaded.get("warnings", []))
        windows = loaded["windows"]
        row_count = loaded.get("row_count", 0)
        used_row_count = loaded.get("used_row_count", row_count)
        dropped_row_count = loaded.get("dropped_row_count", 0)
        label_summary = loaded.get("label_summary", {})
        extra = {}

    if not windows:
        raise IngestionError(
            "No observation windows could be produced from this file."
        )

    response: Dict[str, Any] = {
        "source_type": source_type,
        "filename": filename,
        "file_size_bytes": int(size),
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_seconds": settings.window_minutes * 60,
        "window_count": len(windows),
        "profile_field_count": PROFILE_FIELD_COUNT,
        "model_feature_count": MODEL_FEATURE_COUNT,
        "row_count": int(row_count),
        "used_row_count": int(used_row_count),
        "dropped_row_count": int(dropped_row_count),
        "label_summary": label_summary,
        "warnings": warnings,
        "has_profiles": any(window.get("profile") is not None for window in windows),
        "has_features": any(window.get("features") is not None for window in windows),
        "windows": windows,
    }
    response.update(extra)

    return response


def select_window(result: Dict[str, Any], window_index: int) -> Dict[str, Any]:
    """Return one window from a preprocessing result."""

    windows = result.get("windows") or []
    if not windows:
        raise IngestionError("The preprocessing result contains no windows.")

    if window_index < 0 or window_index >= len(windows):
        raise IngestionError(
            f"window_index {window_index} is outside the available range "
            f"0..{len(windows) - 1}."
        )

    return windows[window_index]


def window_forecast_payload(window: Dict[str, Any]) -> Dict[str, Any]:
    """Build the input for the existing forecasting pipeline.

    Returns ``{"mode": "features", "features": {...}}`` for a model-feature
    row or ``{"mode": "profile", "profile": {...}}`` for a practical profile.
    """

    if window.get("features") is not None:
        return {"mode": "features", "features": window["features"]}

    if window.get("profile") is not None:
        return {"mode": "profile", "profile": window["profile"]}

    raise IngestionError(
        "The selected window has neither a practical profile nor model features."
    )
