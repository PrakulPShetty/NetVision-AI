"""
State transition model for the NetVision world model.

This module loads the Phase 6 first-order Markov transition
model and provides one-step and multi-step state forecasting.
"""

from pathlib import Path
import json
import numpy as np


class StateTransitionModel:
    """
    First-order Markov state-transition model.

    States:
        0 = BENIGN
        1 = ATTACK

    Each transition represents one 5-minute temporal window.
    """

    BENIGN = 0
    ATTACK = 1

    def __init__(self, model_path: str | Path):
        """Load the Phase 6 state-transition model."""

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"State transition model not found: {self.model_path}"
            )

        with open(self.model_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        self.states = {
            int(state): name
            for state, name in config["state_space"].items()
        }

        self.temporal_window_minutes = int(
            config["temporal_window_minutes"]
        )

        probabilities = config["transition_probabilities"]

        self.transition_matrix = np.array(
            [
                [
                    probabilities["BENIGN_to_BENIGN"],
                    probabilities["BENIGN_to_ATTACK"],
                ],
                [
                    probabilities["ATTACK_to_BENIGN"],
                    probabilities["ATTACK_to_ATTACK"],
                ],
            ],
            dtype=float,
        )

        self._validate_model()

    def _validate_model(self):
        """Validate the transition matrix."""

        if self.transition_matrix.shape != (2, 2):
            raise ValueError(
                "Transition matrix must have shape (2, 2)."
            )

        if np.any(self.transition_matrix < 0):
            raise ValueError(
                "Transition probabilities cannot be negative."
            )

        if not np.allclose(
            self.transition_matrix.sum(axis=1),
            1.0
        ):
            raise ValueError(
                "Each transition-matrix row must sum to 1."
            )

    def _validate_state(self, state: int):
        """Validate the network state."""

        if state not in (self.BENIGN, self.ATTACK):
            raise ValueError(
                "State must be 0 (BENIGN) or 1 (ATTACK)."
            )

    def get_transition_probability(
        self,
        current_state: int,
        next_state: int,
    ) -> float:
        """Return the one-step transition probability."""

        self._validate_state(current_state)
        self._validate_state(next_state)

        return float(
            self.transition_matrix[current_state, next_state]
        )

    def get_next_state_probabilities(
        self,
        current_state: int,
    ) -> dict:
        """Return probabilities for the next 5-minute state."""

        self._validate_state(current_state)

        return {
            "BENIGN": float(
                self.transition_matrix[
                    current_state,
                    self.BENIGN
                ]
            ),
            "ATTACK": float(
                self.transition_matrix[
                    current_state,
                    self.ATTACK
                ]
            ),
        }

    def forecast(
        self,
        current_state: int,
        steps: int = 1,
    ) -> dict:
        """
        Forecast network-state probabilities k steps ahead.

        One step represents one 5-minute window.
        """

        self._validate_state(current_state)

        if not isinstance(steps, int) or steps < 1:
            raise ValueError(
                "steps must be a positive integer."
            )

        initial_distribution = np.zeros(2, dtype=float)
        initial_distribution[current_state] = 1.0

        transition_power = np.linalg.matrix_power(
            self.transition_matrix,
            steps,
        )

        forecast_distribution = (
            initial_distribution @ transition_power
        )

        return {
            "steps": steps,
            "horizon_minutes": (
                steps * self.temporal_window_minutes
            ),
            "BENIGN": float(
                forecast_distribution[self.BENIGN]
            ),
            "ATTACK": float(
                forecast_distribution[self.ATTACK]
            ),
        }

    def attack_probability(
        self,
        current_state: int,
        steps: int = 1,
    ) -> float:
        """Return the k-step probability of ATTACK."""

        result = self.forecast(
            current_state=current_state,
            steps=steps,
        )

        return result["ATTACK"]