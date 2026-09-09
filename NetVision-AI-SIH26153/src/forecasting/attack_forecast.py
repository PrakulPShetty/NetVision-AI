"""
NetVision AI
Unified Network Attack Forecasting Pipeline

Phase 7 / Phase 8 / Phase 9

Pipeline:

Practical Traffic Input
        |
        v
Runtime Feature Transformer
        |
        v
138 Model Features
        |
        v
XGBoost + Random Forest Ensemble
        |
        v
Current Attack State
        |
        v
World Model Forecasting
        |
        v
SHAP Explainability
        |
        v
MITRE ATT&CK Mapping
        |
        v
Unified Forecast Output
"""

from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb

from src.features.runtime_transformer import (
    RuntimeFeatureTransformer
)

from src.temporal.state_transition import (
    StateTransitionModel
)

from src.xai.shap_explainer import (
    SHAPExplainer
)

from src.mitre.attack_mapping import (
    MITREAttackMapper
)


class AttackForecastPipeline:
    """
    Unified NetVision AI attack forecasting pipeline.

    Supported input modes:

    1. forecast()
       Directly accepts the already-engineered 138 model features.

    2. forecast_from_traffic()
       Accepts practical traffic-level input and transforms it
       into the exact 138-feature model schema.
    """

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        xgb_model_path=None,
        rf_model_path=None,
        feature_names_path=None,
        ensemble_config_path=None,
        transition_model_path=None,
        shap_background_data=None,
        shap_background_path=None,
        project_root=None,
    ):
        """
        Initialize the complete forecasting pipeline.

        Parameters
        ----------
        xgb_model_path : str or Path, optional
            Path to XGBoost model.

        rf_model_path : str or Path, optional
            Path to Random Forest model.

        feature_names_path : str or Path, optional
            Path to feature_names.json.

        ensemble_config_path : str or Path, optional
            Path to ensemble configuration.

        transition_model_path : str or Path, optional
            Path to world-model transition configuration.

        shap_background_data : pandas.DataFrame, optional
            Already-loaded SHAP background data.

        shap_background_path : str or Path, optional
            Path to SHAP background CSV.

        project_root : str or Path, optional
            Project root directory.
        """

        # =====================================================
        # 1. PROJECT ROOT
        # =====================================================

        if project_root is None:

            project_root = (
                Path(__file__)
                .resolve()
                .parents[2]
            )

        else:

            project_root = Path(
                project_root
            )

        self.project_root = project_root

        # =====================================================
        # 2. DIRECTORIES
        # =====================================================

        self.models_dir = (
            self.project_root
            / "models"
            / "trained"
        )

        self.forecasting_dir = (
            self.project_root
            / "models"
            / "forecasting"
        )

        self.xai_dir = (
            self.project_root
            / "models"
            / "xai"
        )

        # =====================================================
        # 3. DEFAULT ARTIFACT PATHS
        # =====================================================

        default_xgb_path = (
            self.models_dir
            / "xgb_model.json"
        )

        default_rf_path = (
            self.models_dir
            / "rf_smote_model.pkl"
        )

        default_feature_names_path = (
            self.models_dir
            / "feature_names.json"
        )

        default_ensemble_config_path = (
            self.models_dir
            / "ensemble_config.json"
        )

        default_transition_model_path = (
            self.forecasting_dir
            / "state_transition_model.json"
        )

        default_shap_background_path = (
            self.xai_dir
            / "shap_background.csv"
        )

        # =====================================================
        # 4. RESOLVE ARTIFACT PATHS
        # =====================================================

        self.xgb_model_path = Path(
            xgb_model_path
            if xgb_model_path is not None
            else default_xgb_path
        )

        self.rf_model_path = Path(
            rf_model_path
            if rf_model_path is not None
            else default_rf_path
        )

        self.feature_names_path = Path(
            feature_names_path
            if feature_names_path is not None
            else default_feature_names_path
        )

        self.ensemble_config_path = Path(
            ensemble_config_path
            if ensemble_config_path is not None
            else default_ensemble_config_path
        )

        self.transition_model_path = Path(
            transition_model_path
            if transition_model_path is not None
            else default_transition_model_path
        )

        # =====================================================
        # 5. VALIDATE REQUIRED MODEL ARTIFACTS
        # =====================================================

        required_files = {
            "xgb_model.json":
                self.xgb_model_path,

            "rf_smote_model.pkl":
                self.rf_model_path,

            "feature_names.json":
                self.feature_names_path,

            "ensemble_config.json":
                self.ensemble_config_path,

            "state_transition_model.json":
                self.transition_model_path,
        }

        for name, path in required_files.items():

            if not path.exists():

                raise FileNotFoundError(
                    f"Missing required artifact: {name}\n"
                    f"Expected path: {path}"
                )

        # =====================================================
        # 6. LOAD FEATURE NAMES
        # =====================================================

        with open(
            self.feature_names_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.feature_names = json.load(f)

        if not isinstance(
            self.feature_names,
            list
        ):

            raise ValueError(
                "feature_names.json must contain a list."
            )

        if len(
            self.feature_names
        ) != 138:

            raise ValueError(
                "Expected exactly 138 model features. "
                f"Found {len(self.feature_names)}."
            )

        if len(
            set(self.feature_names)
        ) != 138:

            raise ValueError(
                "Duplicate feature names detected."
            )

        # =====================================================
        # 7. LOAD XGBOOST MODEL
        # =====================================================

        self.xgb_model = (
            xgb.XGBClassifier()
        )

        self.xgb_model.load_model(
            str(
                self.xgb_model_path
            )
        )

        # =====================================================
        # 8. LOAD RANDOM FOREST MODEL
        # =====================================================

        self.rf_model = joblib.load(
            self.rf_model_path
        )

        # =====================================================
        # 9. LOAD ENSEMBLE CONFIGURATION
        # =====================================================

        with open(
            self.ensemble_config_path,
            "r",
            encoding="utf-8"
        ) as f:

            self.ensemble_config = json.load(f)

        self.xgb_weight = float(
            self.ensemble_config.get(
                "xgb_weight",
                0.5
            )
        )

        self.rf_weight = float(
            self.ensemble_config.get(
                "rf_weight",
                0.5
            )
        )

        self.threshold = float(
            self.ensemble_config.get(
                "threshold",
                0.40
            )
        )

        # =====================================================
        # 10. VALIDATE ENSEMBLE CONFIGURATION
        # =====================================================

        if self.xgb_weight < 0:

            raise ValueError(
                "XGBoost weight cannot be negative."
            )

        if self.rf_weight < 0:

            raise ValueError(
                "Random Forest weight cannot be negative."
            )

        weight_sum = (
            self.xgb_weight
            + self.rf_weight
        )

        if not np.isclose(
            weight_sum,
            1.0,
            atol=1e-6
        ):

            raise ValueError(
                "Ensemble weights must sum to 1. "
                f"Found {weight_sum}."
            )

        if not (
            0.0
            <= self.threshold
            <= 1.0
        ):

            raise ValueError(
                "Decision threshold must be "
                "between 0 and 1."
            )

        # =====================================================
        # 11. RUNTIME FEATURE TRANSFORMER
        # =====================================================

        self.runtime_transformer = (
            RuntimeFeatureTransformer(
                self.feature_names
            )
        )

        # =====================================================
        # 12. WORLD MODEL
        # =====================================================

        self.world_model = (
            StateTransitionModel(
                self.transition_model_path
            )
        )

        # =====================================================
        # 13. LOAD SHAP BACKGROUND
        # =====================================================

        if (
            shap_background_data
            is not None
        ):

            if isinstance(
                shap_background_data,
                pd.DataFrame
            ):

                self.shap_background = (
                    shap_background_data.copy()
                )

            else:

                self.shap_background = (
                    pd.DataFrame(
                        shap_background_data
                    )
                )

        else:

            if (
                shap_background_path
                is not None
            ):

                resolved_shap_path = (
                    Path(
                        shap_background_path
                    )
                )

            else:

                resolved_shap_path = (
                    default_shap_background_path
                )

            if not resolved_shap_path.exists():

                raise FileNotFoundError(
                    "SHAP background file not found:\n"
                    f"{resolved_shap_path}"
                )

            self.shap_background = (
                pd.read_csv(
                    resolved_shap_path
                )
            )

        # =====================================================
        # 14. VALIDATE SHAP BACKGROUND
        # =====================================================

        if self.shap_background.shape != (
            50,
            138
        ):

            raise ValueError(
                "Invalid SHAP background shape. "
                "Expected (50, 138), "
                f"found {self.shap_background.shape}."
            )

        if (
            self.shap_background.columns.tolist()
            != self.feature_names
        ):

            raise ValueError(
                "SHAP background columns do not "
                "match the model feature schema."
            )

        # =====================================================
        # 15. INITIALIZE SHAP EXPLAINER
        # =====================================================

        self.xai = (
            SHAPExplainer(
                xgb_model=self.xgb_model,
                rf_model=self.rf_model,
                background=self.shap_background,
                feature_names=self.feature_names,
            )
        )

        # =====================================================
        # 16. INITIALIZE MITRE ATT&CK MAPPER
        # =====================================================

        self.mitre = (
            MITREAttackMapper(
                self.feature_names
            )
        )

    # =========================================================
    # FEATURE VALIDATION
    # =========================================================

    def _validate_features(
        self,
        features
    ):
        """
        Validate already-engineered 138 model features.

        Additional keys are ignored.

        The returned DataFrame always follows the exact
        feature order stored in feature_names.json.
        """

        if not isinstance(
            features,
            dict
        ):

            raise TypeError(
                "features must be a dictionary."
            )

        # -----------------------------------------------------
        # Find missing features
        # -----------------------------------------------------

        missing_features = [
            feature
            for feature in self.feature_names
            if feature not in features
        ]

        if missing_features:

            raise ValueError(
                "Missing model features: "
                + ", ".join(
                    missing_features
                )
            )

        # -----------------------------------------------------
        # Preserve exact feature order
        # -----------------------------------------------------

        ordered_features = {
            feature: features[feature]
            for feature in self.feature_names
        }

        # -----------------------------------------------------
        # Convert values to float
        # -----------------------------------------------------

        try:

            values = np.asarray(
                list(
                    ordered_features.values()
                ),
                dtype=float
            )

        except (
            TypeError,
            ValueError
        ) as exc:

            raise ValueError(
                "All model features must be numeric."
            ) from exc

        # -----------------------------------------------------
        # Validate NaN / Inf
        # -----------------------------------------------------

        if not np.isfinite(
            values
        ).all():

            raise ValueError(
                "Model features contain "
                "NaN or Inf."
            )

        # -----------------------------------------------------
        # Return one-row DataFrame
        # -----------------------------------------------------

        return pd.DataFrame(
            [ordered_features],
            columns=self.feature_names
        )

    # =========================================================
    # DIRECT 138-FEATURE FORECAST
    # =========================================================

    def forecast(
        self,
        features
    ):
        """
        Run the complete NetVision AI forecasting pipeline.

        Input:
            Dictionary containing the 138 model features.

        Output:
            ML forecast
            World-model forecast
            SHAP explanation
            MITRE ATT&CK mapping
        """

        # =====================================================
        # 1. VALIDATE MODEL FEATURES
        # =====================================================

        feature_df = (
            self._validate_features(
                features
            )
        )

        # =====================================================
        # 2. XGBOOST PROBABILITY
        # =====================================================

        xgb_probability = float(
            self.xgb_model
            .predict_proba(
                feature_df
            )[0, 1]
        )

        # =====================================================
        # 3. RANDOM FOREST PROBABILITY
        # =====================================================

        rf_probability = float(
            self.rf_model
            .predict_proba(
                feature_df
            )[0, 1]
        )

        # =====================================================
        # 4. 50:50 SOFT-VOTING ENSEMBLE
        # =====================================================

        ensemble_probability = (
            self.xgb_weight
            * xgb_probability
            +
            self.rf_weight
            * rf_probability
        )

        # =====================================================
        # 5. CURRENT ATTACK STATE
        # =====================================================

        current_attack_state = int(
            ensemble_probability
            >= self.threshold
        )

        current_state_name = (
            "ATTACK"
            if current_attack_state == 1
            else "BENIGN"
        )

        # =====================================================
        # 6. WORLD MODEL FORECASTING
        # =====================================================

        forecast_horizons = [
            10,
            20,
            30,
            45,
            60
        ]

        world_forecasts = {}

        for minutes in forecast_horizons:

            # Phase 6 temporal window = 5 minutes.

            steps = int(
                minutes / 5
            )

            attack_probability = float(
                self.world_model
                .k_step_attack_probability(
                    current_state=current_attack_state,
                    k=steps
                )
            )

            future_state = (
                "ATTACK"
                if attack_probability >= 0.5
                else "BENIGN"
            )

            world_forecasts[
                f"{minutes}_minutes"
            ] = {

                "attack_probability":
                    attack_probability,

                "state":
                    future_state
            }

        # =====================================================
        # 7. SHAP EXPLANATION
        # =====================================================

        xai_result = (
            self.xai.explain(
                feature_df
            )
        )

        # =====================================================
        # 8. MITRE ATT&CK MAPPING
        # =====================================================

        mitre_result = (
            self.mitre.map(
                features
            )
        )

        # =====================================================
        # 9. UNIFIED OUTPUT
        # =====================================================

        result = {

            "ml_forecast": {

                "xgb_attack_probability":
                    xgb_probability,

                "rf_attack_probability":
                    rf_probability,

                "ensemble_attack_probability":
                    ensemble_probability,

                "decision_threshold":
                    self.threshold,

                "predicted_current_state":
                    current_state_name,
            },

            "world_model_forecast":
                world_forecasts,

            "xai":
                xai_result,

            "mitre_attack":
                mitre_result,
        }

        return result

    # =========================================================
    # PRACTICAL TRAFFIC INPUT
    # =========================================================

    def forecast_from_traffic(
        self,
        traffic
    ):
        """
        Run the forecasting pipeline using practical
        traffic-level input.

        The practical traffic dictionary is transformed
        into the exact 138-feature model representation.

        Parameters
        ----------
        traffic : dict
            Practical traffic input.

        Returns
        -------
        dict
            Unified forecast result.
        """

        # =====================================================
        # 1. VALIDATE INPUT
        # =====================================================

        if not isinstance(
            traffic,
            dict
        ):

            raise TypeError(
                "traffic must be a dictionary."
            )

        # =====================================================
        # 2. TRANSFORM PRACTICAL INPUT
        # =====================================================

        feature_df = (
            self.runtime_transformer
            .transform(
                traffic
            )
        )

        # =====================================================
        # 3. CONVERT TO DICTIONARY
        # =====================================================

        features = (
            feature_df
            .iloc[0]
            .to_dict()
        )

        # =====================================================
        # 4. RUN STANDARD FORECAST
        # =====================================================

        result = (
            self.forecast(
                features
            )
        )

        # =====================================================
        # 5. ADD INPUT METADATA
        # =====================================================

        result["input"] = {

            "type":
                "practical_traffic",

            "feature_count":
                len(features),

            "runtime_transformation":
                "RuntimeFeatureTransformer",
        }

        return result