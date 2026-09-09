"""
NetVision AI
State Transition World Model

Phase 6 / Phase 7 integration.

Two-state Markov model:

    0 = BENIGN
    1 = ATTACK

The Phase 6 JSON artifact stores transition probabilities
as a dictionary. This module converts that representation
into the validated 2x2 transition matrix used for
multi-step forecasting.
"""

from pathlib import Path
import json

import numpy as np


class StateTransitionModel:
    """
    Two-state Markov transition model.
    """

    BENIGN = 0
    ATTACK = 1

    def __init__(self, config_path):
        # =====================================================
        # 1. LOAD CONFIGURATION
        # =====================================================

        self.config_path = Path(config_path)

        if not self.config_path.exists():
            raise FileNotFoundError(
                f"State transition model not found: "
                f"{self.config_path}"
            )

        with open(
            self.config_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.config = json.load(f)

        # =====================================================
        # 2. STATE SPACE
        # =====================================================

        self.state_space = self.config.get(
            "state_space",
            ["BENIGN", "ATTACK"]
        )

        if len(self.state_space) != 2:
            raise ValueError(
                "Expected exactly two states."
            )

        # =====================================================
        # 3. TEMPORAL WINDOW
        # =====================================================

        self.temporal_window_minutes = float(
            self.config.get(
                "temporal_window_minutes",
                5
            )
        )

        if self.temporal_window_minutes <= 0:
            raise ValueError(
                "Temporal window must be greater than zero."
            )

        # =====================================================
        # 4. LOAD TRANSITION PROBABILITIES
        # =====================================================

        probabilities = self.config.get(
            "transition_probabilities"
        )
        if probabilities is None:
            probabilities = self.config.get(
                "transition_matrix"
            )

        if probabilities is None:
            raise ValueError(
                "transition_probabilities is missing "
                "from the state transition configuration."
            )

        # =====================================================
        # 5. CONVERT DICTIONARY TO MATRIX
        # =====================================================

        self.transition_matrix = (
            self._build_transition_matrix(
                probabilities
            )
        )

        # =====================================================
        # 6. VALIDATE MATRIX
        # =====================================================

        if self.transition_matrix.shape != (
            2,
            2
        ):
            raise ValueError(
                "Transition matrix must have shape (2, 2). "
                f"Found {self.transition_matrix.shape}."
            )

        if not np.isfinite(
            self.transition_matrix
        ).all():
            raise ValueError(
                "Transition matrix contains NaN or Inf."
            )

        row_sums = (
            self.transition_matrix.sum(
                axis=1
            )
        )

        if not np.allclose(
            row_sums,
            1.0,
            atol=1e-6
        ):
            raise ValueError(
                "Transition matrix rows must sum to 1. "
                f"Found row sums: {row_sums}"
            )

    # =========================================================
    # BUILD TRANSITION MATRIX
    # =========================================================

    def _build_transition_matrix(
        self,
        probabilities
    ):
        """
        Convert the Phase 6 transition-probability
        representation into:

            [[P(B->B), P(B->A)],
             [P(A->B), P(A->A)]]
        """

        # -----------------------------------------------------
        # Case 1: Already a matrix/list
        # -----------------------------------------------------

        if isinstance(
            probabilities,
            (list, tuple)
        ):

            matrix = np.asarray(
                probabilities,
                dtype=float
            )

            return matrix

        # -----------------------------------------------------
        # Case 2: Dictionary
        # -----------------------------------------------------

        if isinstance(
            probabilities,
            dict
        ):

            # -------------------------------------------------
            # Sub-case 2a: Flat keys ("BENIGN_to_BENIGN", etc.)
            # -------------------------------------------------

            flat_keys_present = (
                ("BENIGN_to_BENIGN" in probabilities or "0_to_0" in probabilities)
                and ("ATTACK_to_ATTACK" in probabilities or "1_to_1" in probabilities)
            )

            if flat_keys_present:
                benign_to_benign = probabilities.get("BENIGN_to_BENIGN", probabilities.get("0_to_0"))
                benign_to_attack = probabilities.get("BENIGN_to_ATTACK", probabilities.get("0_to_1"))
                attack_to_benign = probabilities.get("ATTACK_to_BENIGN", probabilities.get("1_to_0"))
                attack_to_attack = probabilities.get("ATTACK_to_ATTACK", probabilities.get("1_to_1"))

                values = [
                    [benign_to_benign, benign_to_attack],
                    [attack_to_benign, attack_to_attack]
                ]

                return np.asarray(
                    values,
                    dtype=float
                )

            # -------------------------------------------------
            # Sub-case 2b: Nested dictionary / Row keys
            # -------------------------------------------------

            benign_row = (
                probabilities.get(
                    "BENIGN"
                )
                or probabilities.get(
                    "0"
                )
            )

            attack_row = (
                probabilities.get(
                    "ATTACK"
                )
                or probabilities.get(
                    "1"
                )
            )

            if (
                benign_row is None
                or attack_row is None
            ):

                raise ValueError(
                    "Could not find BENIGN and ATTACK "
                    "transition rows."
                )

            # -------------------------------------------------
            # Each row may itself be a dictionary.
            # -------------------------------------------------

            if isinstance(
                benign_row,
                dict
            ):

                benign_to_benign = (
                    benign_row.get(
                        "BENIGN"
                    )
                    if "BENIGN" in benign_row
                    else benign_row.get("0")
                )

                benign_to_attack = (
                    benign_row.get(
                        "ATTACK"
                    )
                    if "ATTACK" in benign_row
                    else benign_row.get("1")
                )

            else:

                benign_to_benign = benign_row[0]
                benign_to_attack = benign_row[1]

            if isinstance(
                attack_row,
                dict
            ):

                attack_to_benign = (
                    attack_row.get(
                        "BENIGN"
                    )
                    if "BENIGN" in attack_row
                    else attack_row.get("0")
                )

                attack_to_attack = (
                    attack_row.get(
                        "ATTACK"
                    )
                    if "ATTACK" in attack_row
                    else attack_row.get("1")
                )

            else:

                attack_to_benign = attack_row[0]
                attack_to_attack = attack_row[1]

            values = [
                [
                    benign_to_benign,
                    benign_to_attack
                ],
                [
                    attack_to_benign,
                    attack_to_attack
                ]
            ]

            return np.asarray(
                values,
                dtype=float
            )

        # -----------------------------------------------------
        # Unsupported representation
        # -----------------------------------------------------

        raise TypeError(
            "Unsupported transition probability format: "
            f"{type(probabilities).__name__}"
        )

    # =========================================================
    # ONE-STEP PROBABILITIES
    # =========================================================

    def one_step_probabilities(
        self,
        current_state
    ):
        """
        Return the probability distribution after one step.
        """

        state = self._validate_state(
            current_state
        )

        return (
            self.transition_matrix[state]
            .copy()
        )

    # =========================================================
    # K-STEP PROBABILITIES
    # =========================================================

    def k_step_probabilities(
        self,
        current_state,
        k
    ):
        """
        Return state probabilities after k steps.
        """

        state = self._validate_state(
            current_state
        )

        if not isinstance(
            k,
            (int, np.integer)
        ):
            raise TypeError(
                "k must be an integer."
            )

        if k < 0:
            raise ValueError(
                "k must be >= 0."
            )

        # -----------------------------------------------------
        # Initial state distribution
        # -----------------------------------------------------

        distribution = np.zeros(
            2,
            dtype=float
        )

        distribution[state] = 1.0

        if k == 0:
            return distribution

        # -----------------------------------------------------
        # Matrix power
        # -----------------------------------------------------

        transition_power = (
            np.linalg.matrix_power(
                self.transition_matrix,
                k
            )
        )

        distribution = (
            distribution
            @ transition_power
        )

        return distribution

    # =========================================================
    # K-STEP ATTACK PROBABILITY
    # =========================================================

    def k_step_attack_probability(
        self,
        current_state,
        k
    ):
        """
        Return probability of being in ATTACK state
        after k temporal steps.
        """

        probabilities = (
            self.k_step_probabilities(
                current_state,
                k
            )
        )

        # State index 1 = ATTACK

        return float(
            probabilities[
                self.ATTACK
            ]
        )

    # =========================================================
    # FORECAST BY MINUTES
    # =========================================================

    def forecast_minutes(
        self,
        current_state,
        minutes
    ):
        """
        Forecast attack probability after the
        specified number of minutes.
        """

        if minutes < 0:
            raise ValueError(
                "minutes must be >= 0."
            )

        steps_float = (
            float(minutes)
            / self.temporal_window_minutes
        )

        steps = int(
            round(
                steps_float
            )
        )

        if not np.isclose(
            steps_float,
            steps
        ):
            raise ValueError(
                f"{minutes} minutes is not aligned "
                f"with the "
                f"{self.temporal_window_minutes}-minute "
                "temporal window."
            )

        attack_probability = (
            self.k_step_attack_probability(
                current_state,
                steps
            )
        )

        return {
            "minutes": int(minutes),
            "steps": steps,
            "attack_probability":
                attack_probability,
            "state":
                (
                    "ATTACK"
                    if attack_probability >= 0.5
                    else "BENIGN"
                )
        }

    # =========================================================
    # STATE VALIDATION
    # =========================================================

    def _validate_state(
        self,
        current_state
    ):
        """
        Accept:

            0
            1
            BENIGN
            ATTACK
        """

        if isinstance(
            current_state,
            str
        ):

            state = (
                current_state
                .strip()
                .upper()
            )

            if state == "BENIGN":
                return self.BENIGN

            if state == "ATTACK":
                return self.ATTACK

            if state == "0":
                return self.BENIGN

            if state == "1":
                return self.ATTACK

            raise ValueError(
                "Unknown state. "
                "Expected BENIGN or ATTACK."
            )

        if current_state in (
            self.BENIGN,
            self.ATTACK
        ):

            return int(
                current_state
            )

        raise ValueError(
            "State must be 0, 1, "
            "BENIGN, or ATTACK."
        )