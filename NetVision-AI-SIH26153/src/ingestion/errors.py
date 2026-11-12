"""User-correctable ingestion errors.

The FastAPI router maps ``IngestionError.status_code`` onto the HTTP
response, while unexpected exceptions remain 500s. Messages are written
for an analyst uploading a capture, not for a developer reading a stack
trace.
"""

from __future__ import annotations


class IngestionError(ValueError):
    """Base class for failed uploads / preprocessing."""

    status_code = 422


class UnsupportedFileTypeError(IngestionError):
    """The upload is not a CSV, PCAP or PCAPNG file we can parse."""

    status_code = 415


class FileTooLargeError(IngestionError):
    """The upload exceeds the configured size limit."""

    status_code = 413


class IngestionLimitError(IngestionError):
    """The upload exceeds a row / packet / window safety limit."""

    status_code = 413


class EmptyFileError(IngestionError):
    """The upload contains no usable rows or packets."""

    status_code = 422


class MalformedFileError(IngestionError):
    """The file is the right type but cannot be parsed."""

    status_code = 422
