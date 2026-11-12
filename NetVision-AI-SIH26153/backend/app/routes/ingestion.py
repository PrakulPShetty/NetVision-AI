"""File-ingestion endpoints for the NetVision AI API.

Two multipart endpoints are exposed:

* ``POST /preprocess/file`` — upload a capture and return the extracted
  5-minute windows. No model inference is performed.
* ``POST /forecast/file`` — upload a capture, select one window, and run
  the existing forecasting pipeline unchanged.

The router is created with the already-initialised pipeline so this module
never constructs models or touches model code.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from src.ingestion import (
    IngestionError,
    preprocess_upload,
    select_window,
    window_forecast_payload,
)

logger = logging.getLogger("netvision.ingestion")


def _http_error(exc: IngestionError) -> HTTPException:
    return HTTPException(
        status_code=getattr(exc, "status_code", 422),
        detail=str(exc),
    )


def create_ingestion_router(pipeline) -> APIRouter:
    """Build the ingestion router around an initialised pipeline."""

    router = APIRouter(tags=["file ingestion"])

    @router.post("/preprocess/file")
    async def preprocess_file(
        file: UploadFile = File(
            ...,
            description=(
                "Raw CICFlowMeter flow CSV, PCAP/PCAPNG capture, aggregated "
                "40-field profile CSV, or 138-feature Phase 4 CSV."
            ),
        ),
    ) -> Dict[str, Any]:
        try:
            result = await run_in_threadpool(
                preprocess_upload,
                file.file,
                file.filename or "upload",
            )
            return result
        except IngestionError as exc:
            raise _http_error(exc) from exc
        except Exception as exc:  # noqa: BLE001 - reported as a 500
            logger.exception("Unexpected preprocessing failure")
            raise HTTPException(
                status_code=500,
                detail=f"Preprocessing failed: {exc}",
            ) from exc
        finally:
            await file.close()

    @router.post("/forecast/file")
    async def forecast_file(
        file: UploadFile = File(...),
        window_index: int = Form(
            0,
            ge=0,
            description="Zero-based window index from /preprocess/file.",
        ),
    ) -> Dict[str, Any]:
        try:
            preprocessed = await run_in_threadpool(
                preprocess_upload,
                file.file,
                file.filename or "upload",
            )
            window = select_window(preprocessed, window_index)
            payload = window_forecast_payload(window)

            if payload["mode"] == "features":
                forecast = await run_in_threadpool(
                    pipeline.forecast,
                    payload["features"],
                )
            else:
                forecast = await run_in_threadpool(
                    pipeline.forecast_from_traffic,
                    payload["profile"],
                )

            return {
                "source_type": preprocessed["source_type"],
                "filename": preprocessed["filename"],
                "window_index": window_index,
                "window_start": window.get("window_start"),
                "window_end": window.get("window_end"),
                "flow_count": window.get("flow_count"),
                "mode": payload["mode"],
                "forecast": forecast,
            }
        except IngestionError as exc:
            raise _http_error(exc) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unexpected file-forecast failure")
            raise HTTPException(
                status_code=500,
                detail=f"File forecast failed: {exc}",
            ) from exc
        finally:
            await file.close()

    return router
