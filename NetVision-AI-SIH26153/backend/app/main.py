"""
NetVision AI
FastAPI Backend

Unified Network Attack Forecasting API

Pipeline:
    Model-ready traffic features
        ↓
    ML Ensemble
        ↓
    World Model
        ↓
    Probability-Space SHAP
        ↓
    MITRE ATT&CK Mapping
        ↓
    Unified Forecast Response
"""

from pathlib import Path

import pandas as pd

from fastapi import FastAPI, HTTPException

from backend.app.schemas.forecast import ForecastRequest

from src.forecasting.attack_forecast import (
    AttackForecastPipeline
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "trained"
)

WORLD_MODEL_DIR = (
    PROJECT_ROOT
    / "models"
    / "forecasting"
)

XAI_BACKGROUND_PATH = (
    PROJECT_ROOT
    / "models"
    / "xai"
    / "shap_background.csv"
)


# ============================================================
# LOAD SHAP BACKGROUND
# ============================================================

if not XAI_BACKGROUND_PATH.exists():

    raise FileNotFoundError(
        "SHAP background dataset not found: "
        f"{XAI_BACKGROUND_PATH}"
    )

shap_background = pd.read_csv(
    XAI_BACKGROUND_PATH
)


# ============================================================
# VALIDATE SHAP BACKGROUND
# ============================================================

if shap_background.shape != (
    50,
    138
):

    raise ValueError(
        "Invalid SHAP background shape. "
        f"Expected (50, 138), "
        f"received {shap_background.shape}."
    )


if shap_background.isna().any().any():

    raise ValueError(
        "SHAP background contains NaN values."
    )


# ============================================================
# INITIALIZE FORECASTING PIPELINE
# ============================================================

pipeline = AttackForecastPipeline(

    xgb_model_path=(
        MODEL_DIR
        / "xgb_model.json"
    ),

    rf_model_path=(
        MODEL_DIR
        / "rf_smote_model.pkl"
    ),

    feature_names_path=(
        MODEL_DIR
        / "feature_names.json"
    ),

    ensemble_config_path=(
        MODEL_DIR
        / "ensemble_config.json"
    ),

    transition_model_path=(
        WORLD_MODEL_DIR
        / "state_transition_model.json"
    ),

    shap_background_data=(
        shap_background
    ),
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="NetVision AI",
    description=(
        "AI-based Network Attack "
        "Forecasting from Network Traffic Data"
    ),
    version="1.0.0",
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "project": "NetVision AI",
        "status": "running",
        "service": (
            "Network Attack Forecasting"
        ),
    }


# ============================================================
# HEALTH ENDPOINT
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "ml_model": "loaded",
        "world_model": "loaded",
        "xai": "loaded",
        "mitre_attack": "loaded",
    }


# ============================================================
# FORECAST ENDPOINT
# ============================================================

@app.post("/forecast")
def forecast(
    request: ForecastRequest
):

    try:

        result = pipeline.forecast(
            request.features
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                "Forecast processing failed: "
                f"{str(exc)}"
            ),
        )