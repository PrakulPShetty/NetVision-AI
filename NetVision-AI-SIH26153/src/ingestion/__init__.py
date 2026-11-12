"""NetVision AI file ingestion.

Public surface used by the FastAPI router and tests:

* ``preprocess_upload`` — detect CSV / PCAP / PCAPNG, produce 5-minute
  windows with either a 40-field practical profile or 138 model features.
* ``select_window`` — pick one window from a preprocessing response.
* ``window_forecast_payload`` — map a window onto the existing pipeline
  entry point (``forecast`` or ``forecast_from_traffic``).
* ``IngestionError`` and subclasses — user-correctable failures with HTTP
  status codes.
"""

from src.ingestion.errors import (
    EmptyFileError,
    FileTooLargeError,
    IngestionError,
    IngestionLimitError,
    MalformedFileError,
    UnsupportedFileTypeError,
)
from src.ingestion.file_preprocessor import (
    IngestionSettings,
    preprocess_upload,
    select_window,
    window_forecast_payload,
)

__all__ = [
    "EmptyFileError",
    "FileTooLargeError",
    "IngestionError",
    "IngestionLimitError",
    "MalformedFileError",
    "UnsupportedFileTypeError",
    "IngestionSettings",
    "preprocess_upload",
    "select_window",
    "window_forecast_payload",
]
