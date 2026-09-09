"""
NetVision AI
MITRE ATT&CK Behavioral Mapper

Phase 8 finalized implementation.

This module maps observable network-traffic behavior to a limited
set of MITRE ATT&CK techniques.

Current scope:
    T1046      Network Service Discovery
    T1498      Network Denial of Service
    T1498.001  Direct Network Flood

Important:
    This is evidence-based behavioral mapping, not a standalone
    attack classifier. A technique is returned only when the
    configured minimum number of behavioral signal groups are present.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class MITREAttackMapper:
    """
    Maps model-ready temporal network features to MITRE ATT&CK
    behavioral techniques.
    """

    # --------------------------------------------------------
    # Behavioral signal groups
    # --------------------------------------------------------

    SIGNAL_GROUPS = {
        "destination_diversity": [
            "unique_dst_ports",
            "unique_protocols",
        ],

        "traffic_volume": [
            "flow_count",
            "total_flow_count",
            "Tot Fwd Pkts_sum",
            "TotLen Fwd Pkts_sum",
        ],

        "packet_rate": [
            "Bwd Pkts/s_mean",
        ],

        "temporal_concentration": [
            "Flow Duration_max",
        ],
    }

    # --------------------------------------------------------
    # MITRE technique rules
    # --------------------------------------------------------

    TECHNIQUE_RULES = {
        "T1046": {
            "technique_name": "Network Service Discovery",
            "tactic": "Discovery",
            "required_groups": [
                "destination_diversity",
                "traffic_volume",
                "temporal_concentration",
            ],
            "minimum_groups": 2,
            "confidence": "Medium",
            "interpretation": (
                "Observed network diversity and traffic behavior "
                "may be consistent with network service discovery."
            ),
            "limitation": (
                "Flow-level evidence alone cannot confirm that "
                "the observed activity was malicious."
            ),
        },

        "T1498": {
            "technique_name": "Network Denial of Service",
            "tactic": "Impact",
            "required_groups": [
                "traffic_volume",
                "packet_rate",
                "temporal_concentration",
            ],
            "minimum_groups": 3,
            "confidence": "Medium",
            "interpretation": (
                "High-volume or concentrated traffic behavior "
                "may be consistent with network denial-of-service activity."
            ),
            "limitation": (
                "Traffic volume alone cannot distinguish malicious "
                "denial-of-service activity from legitimate high traffic."
            ),
        },

        "T1498.001": {
            "technique_name": "Direct Network Flood",
            "tactic": "Impact",
            "required_groups": [
                "traffic_volume",
                "packet_rate",
                "temporal_concentration",
            ],
            "minimum_groups": 3,
            "confidence": "Low-Medium",
            "interpretation": (
                "Concentrated high-volume traffic behavior may be "
                "consistent with a direct network flood."
            ),
            "limitation": (
                "Network flow data cannot by itself establish that "
                "the traffic represents a deliberate direct flood."
            ),
        },
    }

    ALLOWED_CONFIDENCE = {
        "High",
        "Medium",
        "Low-Medium",
        "Low",
    }

    # ========================================================
    # Constructor
    # ========================================================

    def __init__(
        self,
        feature_names: list[str],
    ) -> None:

        self.feature_names = list(feature_names)

        if len(self.feature_names) != 138:
            raise ValueError(
                "MITRE mapper expects the finalized 138-feature schema. "
                f"Received {len(self.feature_names)} features."
            )

        self._validate_feature_schema()

    # ========================================================
    # Schema validation
    # ========================================================

    def _validate_feature_schema(self) -> None:
        """
        Ensure every feature used by the MITRE rules exists
        in the finalized 138-feature schema.
        """

        available_features = set(
            self.feature_names
        )

        missing = []

        for group_features in self.SIGNAL_GROUPS.values():

            for feature in group_features:

                if feature not in available_features:
                    missing.append(feature)

        if missing:
            raise ValueError(
                "MITRE mapping references unavailable features: "
                f"{sorted(set(missing))}"
            )

    # ========================================================
    # Input validation
    # ========================================================

    def _validate_input(
        self,
        X: Any,
    ) -> pd.DataFrame:

        if isinstance(X, dict):
            X = pd.DataFrame([X])
        elif isinstance(X, pd.Series):
            X = pd.DataFrame([X.to_dict()])
        elif not isinstance(X, pd.DataFrame):
            raise TypeError(
                "MITRE mapper input must be a pandas DataFrame, Series, or dict."
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

        if len(X) != 1:
            raise ValueError(
                "MITRE mapping currently expects exactly "
                "one temporal traffic window."
            )

        if X.isna().any().any():
            raise ValueError(
                "MITRE mapper input contains NaN values."
            )

        values = X.to_numpy(
            dtype=float
        )

        if np.isinf(values).any():
            raise ValueError(
                "MITRE mapper input contains infinite values."
            )

        return X

    # ========================================================
    # Signal-group evaluation
    # ========================================================

    def _evaluate_signal_groups(
        self,
        X: pd.DataFrame,
    ) -> dict[str, dict[str, Any]]:

        group_results = {}

        for group_name, features in self.SIGNAL_GROUPS.items():

            supporting_features = []

            for feature in features:

                value = float(
                    X.iloc[0][feature]
                )

                # Design-level behavioral signal:
                # finite positive value indicates presence.
                if np.isfinite(value) and value > 0:
                    supporting_features.append(
                        feature
                    )

            group_results[group_name] = {
                "present": (
                    len(supporting_features) > 0
                ),
                "supporting_features":
                    supporting_features,
            }

        return group_results

    # ========================================================
    # Technique evaluation
    # ========================================================

    def _evaluate_technique(
        self,
        technique_id: str,
        group_results: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:

        rule = self.TECHNIQUE_RULES[
            technique_id
        ]

        present_groups = []

        supporting_features = []

        for group_name in rule[
            "required_groups"
        ]:

            result = group_results[
                group_name
            ]

            if result["present"]:

                present_groups.append(
                    group_name
                )

                supporting_features.extend(
                    result[
                        "supporting_features"
                    ]
                )

        # Remove duplicate features while preserving order
        supporting_features = list(
            dict.fromkeys(
                supporting_features
            )
        )

        if len(present_groups) < rule[
            "minimum_groups"
        ]:
            return None

        evidence = [
            {
                "signal_group": group_name,
                "supporting_features":
                    group_results[
                        group_name
                    ]["supporting_features"],
            }
            for group_name in present_groups
        ]

        confidence = rule[
            "confidence"
        ]

        if confidence not in self.ALLOWED_CONFIDENCE:
            raise ValueError(
                f"Invalid confidence level: {confidence}"
            )

        return {
            "technique_id":
                technique_id,

            "technique_name":
                rule["technique_name"],

            "tactic":
                rule["tactic"],

            "confidence":
                confidence,

            "evidence":
                evidence,

            "supporting_features":
                supporting_features,

            "interpretation":
                rule["interpretation"],

            "limitation":
                rule["limitation"],
        }

    # ========================================================
    # Public mapping method
    # ========================================================

    def map(
        self,
        X: pd.DataFrame,
    ) -> dict[str, Any]:

        X = self._validate_input(X)

        group_results = (
            self._evaluate_signal_groups(X)
        )

        techniques = []

        for technique_id in self.TECHNIQUE_RULES:

            result = self._evaluate_technique(
                technique_id,
                group_results,
            )

            if result is not None:
                techniques.append(result)

        # ----------------------------------------------------
        # No confident mapping
        # ----------------------------------------------------

        if not techniques:

            return {
                "mapping_status":
                    "No confident MITRE mapping identified",

                "techniques":
                    [],

                "reason":
                    "Insufficient behavioral evidence "
                    "to satisfy the configured MITRE "
                    "decision rules.",

                "signal_groups":
                    group_results,
            }

        # ----------------------------------------------------
        # Mapping found
        # ----------------------------------------------------

        return {
            "mapping_status":
                "MITRE ATT&CK mapping identified",

            "techniques":
                techniques,

            "signal_groups":
                group_results,
        }