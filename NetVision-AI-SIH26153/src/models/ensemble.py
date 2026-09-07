"""
NetVision-AI-SIH26153
Final Ensemble Model

Final architecture:
    XGBoost + Random Forest (SMOTE-trained)
    -> 50/50 soft voting
    -> threshold = 0.40

This module contains inference-side ensemble logic.

The trained model artifact is stored separately in:

    models/trained/netvision_final_ensemble_v1.pkl
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class NetVisionEnsemble:
    """
    Final NetVision attack-forecasting ensemble.

    The ensemble combines:
        1. XGBoost
        2. Random Forest trained using SMOTE

    Their attack probabilities are averaged with equal weights.

    Final prediction:
        probability >= 0.40 -> ATTACK
        probability < 0.40 -> BENIGN
    """

    def __init__(
        self,
        xgb_model,
        rf_smote_model,
        feature_names: list[str],
        xgb_weight: float = 0.50,
        rf_smote_weight: float = 0.50,
        threshold: float = 0.40,
    ):
        self.xgb_model = xgb_model
        self.rf_smote_model = rf_smote_model

        self.feature_names = list(feature_names)

        self.xgb_weight = float(xgb_weight)
        self.rf_smote_weight = float(rf_smote_weight)

        self.threshold = float(threshold)

        self.model_name = (
            "XGBoost + Random Forest (SMOTE) "
            "Soft-Voting Ensemble"
        )

        self.model_version = "v1"

        self.forecast_window_minutes = 5
        self.forecast_horizon_minutes = 10

        # Validate ensemble configuration.
        if not np.isclose(
            self.xgb_weight + self.rf_smote_weight,
            1.0,
        ):
            raise ValueError(
                "Ensemble weights must sum to 1.0."
            )

        if not 0.0 < self.threshold < 1.0:
            raise ValueError(
                "Threshold must be between 0 and 1."
            )

        if len(self.feature_names) != 138:
            raise ValueError(
                f"Expected 138 features, "
                f"received {len(self.feature_names)}."
            )

    def _prepare_input(
        self,
        X: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Validate and arrange inference input.

        The backend must provide exactly the same
        138 features used during model training.
        """

        if not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

        # Check for missing required features.
        missing_features = [
            feature
            for feature in self.feature_names
            if feature not in X.columns
        ]

        if missing_features:
            raise ValueError(
                f"Missing required features: "
                f"{missing_features}"
            )

        # Check for unexpected features.
        unexpected_features = [
            feature
            for feature in X.columns
            if feature not in self.feature_names
        ]

        if unexpected_features:
            raise ValueError(
                f"Unexpected features received: "
                f"{unexpected_features}"
            )

        # Restore exact training feature order.
        X = X[self.feature_names].copy()

        # Ensure all values are numeric.
        X = X.apply(pd.to_numeric, errors="raise")

        # Reject missing values.
        if X.isna().any().any():
            raise ValueError(
                "Inference input contains NaN values."
            )

        # Reject infinite values.
        if np.isinf(
            X.to_numpy(dtype=np.float64)
        ).any():
            raise ValueError(
                "Inference input contains infinite values."
            )

        return X

    def predict_proba(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Calculate final ensemble attack probability.

        Returns:
            NumPy array containing probability of ATTACK.
        """

        X = self._prepare_input(X)

        # Class 1 = ATTACK.
        xgb_probability = (
            self.xgb_model.predict_proba(X)[:, 1]
        )

        rf_probability = (
            self.rf_smote_model.predict_proba(X)[:, 1]
        )

        # 50/50 soft voting.
        ensemble_probability = (
            self.xgb_weight * xgb_probability
            + self.rf_smote_weight * rf_probability
        )

        return ensemble_probability

    def predict(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Generate binary predictions.

        Returns:
            0 = BENIGN
            1 = ATTACK
        """

        probability = self.predict_proba(X)

        return (
            probability >= self.threshold
        ).astype(int)

    def predict_label(
        self,
        X: pd.DataFrame,
    ) -> np.ndarray:
        """
        Generate human-readable predictions.

        Returns:
            BENIGN or ATTACK
        """

        predictions = self.predict(X)

        return np.where(
            predictions == 1,
            "ATTACK",
            "BENIGN",
        )