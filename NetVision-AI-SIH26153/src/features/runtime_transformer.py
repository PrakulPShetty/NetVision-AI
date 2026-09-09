"""
NetVision AI - Runtime Traffic Feature Transformer

Converts practical 5-minute traffic-window statistics into the
138-feature representation expected by the Phase 5 forecasting model.

Important:
- This transformer is for deployment/demo input.
- It does not modify the trained model.
- The final output is always ordered using feature_names.json.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


class RuntimeFeatureTransformer:
    """Build the 138 model features from practical traffic statistics."""

    def __init__(self, feature_names: Sequence[str]):
        self.feature_names = list(feature_names)

        if len(self.feature_names) != 138:
            raise ValueError(
                f"Expected 138 model features, got {len(self.feature_names)}"
            )

    @staticmethod
    def _number(
        data: Mapping[str, Any],
        key: str,
        default: float = 0.0,
    ) -> float:
        """Read and validate a numeric input."""
        value = data.get(key, default)

        if value is None or value == "":
            return float(default)

        try:
            value = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Input '{key}' must be numeric."
            ) from exc

        if not np.isfinite(value):
            raise ValueError(
                f"Input '{key}' must be finite."
            )

        return value

    @staticmethod
    def _stats(
        value: float,
        prefix: str,
        include_min: bool = True,
    ) -> Dict[str, float]:
        """Create temporal statistics for a scalar traffic measurement."""
        result = {
            f"{prefix}_mean": value,
            f"{prefix}_max": value,
        }

        if include_min:
            result[f"{prefix}_min"] = value

        return result

    def transform(
        self,
        traffic: Mapping[str, Any],
    ) -> pd.DataFrame:
        """
        Convert practical traffic-window input into a 1-row,
        138-feature DataFrame.
        """

        fwd_pkts = self._number(
            traffic, "forward_packets"
        )
        bwd_pkts = self._number(
            traffic, "backward_packets"
        )

        fwd_bytes = self._number(
            traffic, "forward_bytes"
        )
        bwd_bytes = self._number(
            traffic, "backward_bytes"
        )

        flow_duration = self._number(
            traffic, "flow_duration"
        )

        flow_bytes_sec = self._number(
            traffic, "flow_bytes_per_sec"
        )

        flow_pkts_sec = self._number(
            traffic, "flow_packets_per_sec"
        )

        bwd_pkts_sec = self._number(
            traffic, "backward_packets_per_sec"
        )

        down_up_ratio = self._number(
            traffic, "down_up_ratio"
        )

        data: Dict[str, float] = {}

        # ---------------------------------------------------------
        # Packet counts
        # ---------------------------------------------------------

        data.update(
            self._stats(
                fwd_pkts,
                "Tot Fwd Pkts",
                include_min=False,
            )
        )

        data.update(
            self._stats(
                bwd_pkts,
                "Tot Bwd Pkts",
                include_min=False,
            )
        )

        # ---------------------------------------------------------
        # Packet byte counts
        # ---------------------------------------------------------

        data.update(
            self._stats(
                fwd_bytes,
                "TotLen Fwd Pkts",
                include_min=False,
            )
        )

        data.update(
            self._stats(
                bwd_bytes,
                "TotLen Bwd Pkts",
                include_min=False,
            )
        )

        # ---------------------------------------------------------
        # Flow duration
        # ---------------------------------------------------------

        data.update(
            self._stats(
                flow_duration,
                "Flow Duration",
            )
        )

        # ---------------------------------------------------------
        # Inter-arrival-time statistics
        # ---------------------------------------------------------

        iat_fields = [
            "Flow IAT Mean",
            "Flow IAT Std",
            "Flow IAT Max",
            "Fwd IAT Tot",
            "Fwd IAT Mean",
            "Fwd IAT Std",
            "Fwd IAT Max",
            "Bwd IAT Tot",
            "Bwd IAT Mean",
            "Bwd IAT Std",
            "Bwd IAT Max",
            "Bwd IAT Min",
        ]

        for field in iat_fields:
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            for suffix in ("mean", "max"):
                key = f"{field}_{suffix}"

                if key in self.feature_names:
                    data[key] = value

            min_key = f"{field}_min"

            if min_key in self.feature_names:
                data[min_key] = value

        # ---------------------------------------------------------
        # Packet-length statistics
        # ---------------------------------------------------------

        packet_fields = [
            "Fwd Pkt Len Max",
            "Fwd Pkt Len Min",
            "Fwd Pkt Len Mean",
            "Fwd Pkt Len Std",
            "Bwd Pkt Len Max",
            "Bwd Pkt Len Min",
            "Bwd Pkt Len Mean",
            "Bwd Pkt Len Std",
            "Pkt Len Min",
            "Pkt Len Max",
            "Pkt Len Mean",
            "Pkt Len Std",
            "Pkt Len Var",
            "Pkt Size Avg",
        ]

        for field in packet_fields:
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            for suffix in ("mean", "max"):
                key = f"{field}_{suffix}"

                if key in self.feature_names:
                    data[key] = value

        # ---------------------------------------------------------
        # Traffic rates
        # ---------------------------------------------------------

        rate_values = {
            "Flow Byts/s": flow_bytes_sec,
            "Flow Pkts/s": flow_pkts_sec,
            "Bwd Pkts/s": bwd_pkts_sec,
        }

        for field, value in rate_values.items():
            data[f"{field}_mean"] = value
            data[f"{field}_max"] = value

        # ---------------------------------------------------------
        # TCP flags
        # ---------------------------------------------------------

        flag_fields = [
            "Fwd PSH Flags",
            "Fwd URG Flags",
            "FIN Flag Cnt",
            "SYN Flag Cnt",
            "RST Flag Cnt",
            "PSH Flag Cnt",
            "ACK Flag Cnt",
            "URG Flag Cnt",
            "CWE Flag Count",
            "ECE Flag Cnt",
        ]

        for field in flag_fields:
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            data[f"{field}_sum"] = value
            data[f"{field}_max"] = value

        # ---------------------------------------------------------
        # Ratio
        # ---------------------------------------------------------

        data["Down/Up Ratio_mean"] = down_up_ratio
        data["Down/Up Ratio_max"] = down_up_ratio

        # ---------------------------------------------------------
        # Header / TCP fields
        # ---------------------------------------------------------

        header_fields = [
            "Fwd Header Len",
            "Bwd Header Len",
            "Fwd Seg Size Min",
        ]

        for field in header_fields:
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            data[f"{field}_mean"] = value
            data[f"{field}_max"] = value

        # ---------------------------------------------------------
        # TCP initial windows
        # ---------------------------------------------------------

        for field in (
            "Init Fwd Win Byts",
            "Init Bwd Win Byts",
        ):
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            data[f"{field}_mean"] = value
            data[f"{field}_min"] = value
            data[f"{field}_max"] = value

        # ---------------------------------------------------------
        # Active / idle behaviour
        # ---------------------------------------------------------

        activity_fields = [
            "Active Mean",
            "Active Std",
            "Active Max",
            "Active Min",
            "Idle Mean",
            "Idle Std",
            "Idle Max",
            "Idle Min",
        ]

        for field in activity_fields:
            value = self._number(
                traffic,
                field.lower().replace(" ", "_"),
            )

            data[f"{field}_mean"] = value
            data[f"{field}_max"] = value

            min_key = f"{field}_min"

            if min_key in self.feature_names:
                data[min_key] = value

        # ---------------------------------------------------------
        # Network diversity
        # ---------------------------------------------------------

        flow_count = self._number(
            traffic,
            "flow_count",
            1,
        )

        unique_dst_ports = self._number(
            traffic,
            "unique_dst_ports",
            1,
        )

        unique_protocols = self._number(
            traffic,
            "unique_protocols",
            1,
        )

        data["flow_count"] = flow_count
        data["unique_dst_ports"] = unique_dst_ports
        data["unique_protocols"] = unique_protocols
        data["total_flow_count"] = flow_count

        # ---------------------------------------------------------
        # Final schema enforcement
        # ---------------------------------------------------------

        output = pd.DataFrame(
            [[data.get(name, 0.0) for name in self.feature_names]],
            columns=self.feature_names,
        )

        # Numeric conversion
        output = output.apply(
            pd.to_numeric,
            errors="coerce",
        )

        # Runtime safety
        if output.isna().any().any():
            missing = output.columns[
                output.isna().any()
            ].tolist()

            raise ValueError(
                f"Runtime transformation produced invalid values: {missing}"
            )

        if np.isinf(output.to_numpy(dtype=float)).any():
            raise ValueError(
                "Runtime transformation produced infinite values."
            )

        return output