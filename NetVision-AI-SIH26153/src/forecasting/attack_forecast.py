"""
Unified ML + World Model forecasting pipeline.

The ML ensemble determines the current network attack state.
The World Model then forecasts future attack probabilities.
"""

from pathlib import Path
import json

import pandas as pd
import xgboost as xgb
import joblib

from src.transition.state_transition import StateTransitionModel


class AttackForecastPipeline:
    """
    Combines the Phase 7 ML ensemble with the Phase 6 World Model.

    ML:
        XGBoost + Random Forest-SMOTE
        50:50 probability ensemble
        threshold = 0.40

    World Model:
        First-order Markov model
        5-minute temporal window
    """

    def __init__(
        self,
        xgb_model_path: str | Path,
        rf_model_path: str | Path,
        feature_names_path: str | Path,
        ensemble_config_path: str | Path,
        transition_model_path: str | Path,
    ):
        """Load all required forecasting components."""

        self.xgb_model = xgb.XGBClassifier()
        self.xgb_model.load_model(str(xgb_model_path))

        self.rf_model = joblib.load(rf_model_path)

        with open(feature_names_path, "r", encoding="utf-8") as file:
            self.feature_names = json.load(file)

        with open(ensemble_config_path, "r", encoding="utf-8") as file:
            self.ensemble_config = json.load(file)

        self.threshold = float(
            self.ensemble_config["threshold"]
        )

        self.world_model = StateTransitionModel(
            transition_model_path
        )

        self._validate_components()

    def _validate_components(self):
        """Validate model compatibility."""

        if len(self.feature_names) != 138:
            raise ValueError(
                f"Expected 138 features, "
                f"found {len(self.feature_names)}."
            )

        if self.xgb_model.n_features_in_ != 138:
            raise ValueError(
                "XGBoost model does not expect 138 features."
            )

        if self.rf_model.n_features_in_ != 138:
            raise ValueError(
                "Random Forest model does not expect 138 features."
            )

    def _prepare_input(self, X):
        """Validate and arrange model input."""

        if isinstance(X, dict):
            X = pd.DataFrame([X])

        elif not isinstance(X, pd.DataFrame):
            X = pd.DataFrame(X)

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

        X = X[self.feature_names].copy()

        if X.isna().any().any():
            raise ValueError(
                "Input contains NaN values."
            )

        if X.isin([float("inf"), float("-inf")]).any().any():
            raise ValueError(
                "Input contains infinite values."
            )

        return X

    def predict_ml(self, X):
        """
        Run the ML ensemble.

        Returns the attack probability and current state.
        """

        X = self._prepare_input(X)

        xgb_probability = float(
            self.xgb_model.predict_proba(X)[0, 1]
        )

        rf_probability = float(
            self.rf_model.predict_proba(X)[0, 1]
        )

        ensemble_probability = (
            0.5 * xgb_probability
            + 0.5 * rf_probability
        )

        current_state = int(
            ensemble_probability >= self.threshold
        )

        return {
            "xgb_attack_probability": xgb_probability,
            "rf_attack_probability": rf_probability,
            "ensemble_attack_probability": ensemble_probability,
            "current_state": current_state,
            "current_state_label": (
                "ATTACK"
                if current_state == 1
                else "BENIGN"
            ),
        }

    def forecast(
        self,
        X,
        horizons_minutes=(10, 20, 30, 45, 60),
    ):
        """
        Run the complete ML + World Model forecast.

        The ML ensemble determines the current state.
        The World Model forecasts future attack probabilities.
        """

        ml_result = self.predict_ml(X)

        current_state = ml_result["current_state"]

        forecasts = []

        for horizon in horizons_minutes:

            if horizon % self.world_model.temporal_window_minutes != 0:
                raise ValueError(
                    f"Horizon {horizon} minutes is not aligned "
                    f"with the {self.world_model.temporal_window_minutes}-"
                    f"minute temporal window."
                )

            steps = (
                horizon
                // self.world_model.temporal_window_minutes
            )

            world_result = self.world_model.forecast(
                current_state=current_state,
                steps=steps,
            )

            forecasts.append(
                {
                    "horizon_minutes": horizon,
                    "steps": steps,
                    "future_attack_probability": (
                        world_result["ATTACK"]
                    ),
                    "future_benign_probability": (
                        world_result["BENIGN"]
                    ),
                }
            )

        return {
            "ml": ml_result,
            "world_model": {
                "current_state": ml_result["current_state_label"],
                "forecasts": forecasts,
            },
        }