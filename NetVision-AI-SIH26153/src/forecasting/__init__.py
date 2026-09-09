"""Forecasting utilities."""
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
    Initialize the unified forecasting pipeline.

    Supports the existing Phase 7/8 test interface and the
    newer runtime practical-traffic input path.

    SHAP background can be supplied either as:
        - shap_background_data: DataFrame
        - shap_background_path: CSV path

    If neither is supplied, the default project artifact is used.
    """

    # =========================================================
    # 1. PROJECT ROOT
    # =========================================================

    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]
    else:
        project_root = Path(project_root)

    self.project_root = project_root

    # =========================================================
    # 2. DEFAULT DIRECTORIES
    # =========================================================

    models_dir = (
        self.project_root
        / "models"
        / "trained"
    )

    forecasting_dir = (
        self.project_root
        / "models"
        / "forecasting"
    )

    xai_dir = (
        self.project_root
        / "models"
        / "xai"
    )

    # =========================================================
    # 3. DEFAULT PATHS
    # =========================================================

    default_xgb_path = (
        models_dir / "xgb_model.json"
    )

    default_rf_path = (
        models_dir / "rf_smote_model.pkl"
    )

    default_feature_names_path = (
        models_dir / "feature_names.json"
    )

    default_ensemble_config_path = (
        models_dir / "ensemble_config.json"
    )

    default_transition_model_path = (
        forecasting_dir
        / "state_transition_model.json"
    )

    default_shap_background_path = (
        xai_dir / "shap_background.csv"
    )

    # =========================================================
    # 4. RESOLVE MODEL PATHS
    # =========================================================

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

    # =========================================================
    # 5. VALIDATE MODEL FILES
    # =========================================================

    required_files = {
        "xgb_model.json": self.xgb_model_path,
        "rf_smote_model.pkl": self.rf_model_path,
        "feature_names.json": self.feature_names_path,
        "ensemble_config.json": self.ensemble_config_path,
        "state_transition_model.json":
            self.transition_model_path,
    }

    for name, path in required_files.items():

        if not path.exists():

            raise FileNotFoundError(
                f"Missing required artifact: {name}\n"
                f"Expected path: {path}"
            )

    # =========================================================
    # 6. LOAD FEATURE NAMES
    # =========================================================

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

    if len(self.feature_names) != 138:

        raise ValueError(
            "Expected 138 model features, "
            f"found {len(self.feature_names)}."
        )

    if len(
        set(self.feature_names)
    ) != 138:

        raise ValueError(
            "Duplicate feature names detected."
        )

    # =========================================================
    # 7. LOAD XGBOOST
    # =========================================================

    self.xgb_model = xgb.XGBClassifier()

    self.xgb_model.load_model(
        str(self.xgb_model_path)
    )

    # =========================================================
    # 8. LOAD RANDOM FOREST
    # =========================================================

    self.rf_model = joblib.load(
        self.rf_model_path
    )

    # =========================================================
    # 9. LOAD ENSEMBLE CONFIG
    # =========================================================

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

    # =========================================================
    # 10. VALIDATE ENSEMBLE CONFIG
    # =========================================================

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
        0.0 <= self.threshold <= 1.0
    ):

        raise ValueError(
            "Decision threshold must be between 0 and 1."
        )

    # =========================================================
    # 11. RUNTIME FEATURE TRANSFORMER
    # =========================================================

    self.runtime_transformer = (
        RuntimeFeatureTransformer(
            self.feature_names
        )
    )

    # =========================================================
    # 12. WORLD MODEL
    # =========================================================

    self.world_model = (
        StateTransitionModel(
            self.transition_model_path
        )
    )

    # =========================================================
    # 13. SHAP BACKGROUND
    # =========================================================

    if shap_background_data is not None:

        self.shap_background = (
            shap_background_data.copy()
            if hasattr(
                shap_background_data,
                "copy"
            )
            else pd.DataFrame(
                shap_background_data
            )
        )

    else:

        if shap_background_path is not None:

            resolved_shap_path = Path(
                shap_background_path
            )

        else:

            resolved_shap_path = (
                default_shap_background_path
            )

        if not resolved_shap_path.exists():

            raise FileNotFoundError(
                "SHAP background not found: "
                f"{resolved_shap_path}"
            )

        self.shap_background = (
            pd.read_csv(
                resolved_shap_path
            )
        )

    # =========================================================
    # 14. VALIDATE SHAP BACKGROUND
    # =========================================================

    if self.shap_background.shape != (
        50,
        138
    ):

        raise ValueError(
            "Invalid SHAP background shape. "
            f"Expected (50, 138), "
            f"found {self.shap_background.shape}."
        )

    if (
        self.shap_background.columns.tolist()
        != self.feature_names
    ):

        raise ValueError(
            "SHAP background columns do not match "
            "the 138-feature model schema."
        )

    # =========================================================
    # 15. SHAP EXPLAINER
    # =========================================================

    self.xai = SHAPExplainer(
        xgb_model=self.xgb_model,
        rf_model=self.rf_model,
        background=self.shap_background,
        feature_names=self.feature_names,
    )

    # =========================================================
    # 16. MITRE ATT&CK MAPPER
    # =========================================================

    self.mitre = MITREAttackMapper(
        self.feature_names
    )