"""
NetVision AI
Probability-Space SHAP Explainer

Phase 8 finalized XAI implementation.

This module explains the ensemble attack probability using:
    - XGBoost
    - Random Forest-SMOTE

The explanations are generated in probability space and combined
using the same 50:50 ensemble weights used by the forecasting model.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import numpy as np
import pandas as pd
import shap


class SHAPExplainer:
    """
    Probability-space SHAP explainer for the NetVision ensemble.
    """

    def __init__(
        self,
        xgb_model: Any,
        rf_model: Any,
        feature_names: list[str],
        xgb_weight: float = 0.5,
        rf_weight: float = 0.5,
        background_data: pd.DataFrame | None = None,
    ) -> None:

        self.xgb_model = xgb_model
        self.rf_model = rf_model
        self.feature_names = feature_names

        self.xgb_weight = xgb_weight
        self.rf_weight = rf_weight

        if not np.isclose(
            self.xgb_weight + self.rf_weight,
            1.0,
        ):
            raise ValueError(
                "XAI ensemble weights must sum to 1.0."
            )

        self.background_data = background_data

        # ----------------------------------------------------
        # XGBoost explainer
        # ----------------------------------------------------

        if background_data is not None:

            self.xgb_explainer = shap.TreeExplainer(
                self.xgb_model,
                data=background_data,
                feature_perturbation="interventional",
                model_output="probability",
            )

        else:

            raise ValueError(
                "Background data is required for "
                "probability-space SHAP."
            )

        # ----------------------------------------------------
        # Random Forest explainer
        # ----------------------------------------------------

        self.rf_explainer = shap.TreeExplainer(
            self.rf_model
        )

    # ========================================================
    # Validation
    # ========================================================

    def _validate_input(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:

        if not isinstance(X, pd.DataFrame):
            raise TypeError(
                "X must be a pandas DataFrame."
            )

        missing = [
            feature
            for feature in self.feature_names
            if feature not in X.columns
        ]

        unexpected = [
            feature
            for feature in X.columns
            if feature not in self.feature_names
        ]

        if missing:
            raise ValueError(
                f"Missing features: {missing}"
            )

        if unexpected:
            raise ValueError(
                f"Unexpected features: {unexpected}"
            )

        X = X[
            self.feature_names
        ].copy()

        if X.isna().any().any():
            raise ValueError(
                "Input contains NaN values."
            )

        if np.isinf(
            X.to_numpy(dtype=float)
        ).any():

            raise ValueError(
                "Input contains infinite values."
            )

        return X

    # ========================================================
    # XGBoost probability-space SHAP
    # ========================================================

    def _xgb_shap(
        self,
        X: pd.DataFrame,
    ) -> tuple[np.ndarray, float]:

        shap_values = self.xgb_explainer.shap_values(
            X
        )

        shap_values = np.asarray(
            shap_values,
            dtype=float,
        )

        if shap_values.ndim == 1:
            shap_values = shap_values.reshape(
                1,
                -1,
            )

        base_value = self.xgb_explainer.expected_value

        base_value = float(
            np.asarray(
                base_value
            ).reshape(-1)[0]
        )

        return shap_values, base_value

    # ========================================================
    # Random Forest probability-space SHAP
    # ========================================================

    def _rf_shap(
        self,
        X: pd.DataFrame,
    ) -> tuple[np.ndarray, float]:

        explanation = self.rf_explainer(
            X
        )

        values = np.asarray(
            explanation.values,
            dtype=float,
        )

        base_values = np.asarray(
            explanation.base_values,
            dtype=float,
        )

        # Binary Random Forest:
        # [:, :, 1] corresponds to ATTACK probability.
        if values.ndim == 3:

            attack_shap = values[
                :,
                :,
                1
            ]

        elif values.ndim == 2:

            attack_shap = values

        else:

            raise ValueError(
                "Unexpected Random Forest SHAP shape: "
                f"{values.shape}"
            )

        if base_values.ndim == 2:

            attack_base = base_values[
                :,
                1
            ]

        else:

            attack_base = base_values

        attack_base = float(
            attack_base.reshape(-1)[0]
        )

        return attack_shap, attack_base

    # ========================================================
    # Explain
    # ========================================================

    def explain(
        self,
        X: pd.DataFrame,
        top_n: int = 10,
    ) -> dict[str, Any]:

        X = self._validate_input(X)

        # ----------------------------------------------------
        # Individual model predictions
        # ----------------------------------------------------

        xgb_probability = float(
            self.xgb_model.predict_proba(
                X
            )[0, 1]
        )

        rf_probability = float(
            self.rf_model.predict_proba(
                X
            )[0, 1]
        )

        ensemble_probability = (
            self.xgb_weight * xgb_probability
            +
            self.rf_weight * rf_probability
        )

        # ----------------------------------------------------
        # SHAP values
        # ----------------------------------------------------

        xgb_shap, xgb_base = self._xgb_shap(
            X
        )

        rf_shap, rf_base = self._rf_shap(
            X
        )

        # ----------------------------------------------------
        # Weighted probability-space ensemble SHAP
        # ----------------------------------------------------

        ensemble_shap = (
            self.xgb_weight * xgb_shap
            +
            self.rf_weight * rf_shap
        )

        ensemble_base = (
            self.xgb_weight * xgb_base
            +
            self.rf_weight * rf_base
        )

        reconstructed_probability = (
            ensemble_base
            +
            float(
                ensemble_shap[0].sum()
            )
        )

        reconstruction_error = abs(
            reconstructed_probability
            -
            ensemble_probability
        )

        # ----------------------------------------------------
        # Feature contributions
        # ----------------------------------------------------

        contributions = pd.DataFrame(
            {
                "feature": self.feature_names,
                "shap_value": ensemble_shap[0],
            }
        )

        contributions[
            "absolute_shap"
        ] = contributions[
            "shap_value"
        ].abs()

        contributions = (
            contributions
            .sort_values(
                "absolute_shap",
                ascending=False,
            )
            .reset_index(drop=True)
        )

        top_contributions = (
            contributions
            .head(top_n)
            .to_dict(
                orient="records"
            )
        )

        # ----------------------------------------------------
        # Positive / negative contributors
        # ----------------------------------------------------

        positive = (
            contributions[
                contributions[
                    "shap_value"
                ] > 0
            ]
            .head(top_n)
            .to_dict(
                orient="records"
            )
        )

        negative = (
            contributions[
                contributions[
                    "shap_value"
                ] < 0
            ]
            .sort_values(
                "shap_value"
            )
            .head(top_n)
            .to_dict(
                orient="records"
            )
        )

        return {
            "method": "Probability-space SHAP",

            "ensemble": {
                "xgb_weight": self.xgb_weight,
                "rf_weight": self.rf_weight,
                "xgb_attack_probability": xgb_probability,
                "rf_attack_probability": rf_probability,
                "ensemble_attack_probability":
                    ensemble_probability,
            },

            "base_probability":
                ensemble_base,

            "reconstructed_probability":
                reconstructed_probability,

            "reconstruction_error":
                reconstruction_error,

            "validation_passed":
                reconstruction_error < 1e-5,

            "top_contributions":
                top_contributions,

            "positive_contributors":
                positive,

            "negative_contributors":
                negative,
        }