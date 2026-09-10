"""
NetVision AI - Runtime Traffic Feature Transformer
==================================================

Converts a practical 5-minute traffic-window profile into the exact
138-feature representation expected by the frozen Phase 5 forecasting model.

Architecture (see docs/architecture/runtime_input_design.md):

    Practical Traffic Profile (one 5-minute observation window)
            |
            v
    DIRECT inputs .......... window fields, totals, profile values
    DERIVED-EXACT ......... mean = sum / flow_count  (Phase 4 identity,
                            verified exact on genuine rows)
    DERIVED-CONSTANT ...... flag max = 1, MTU cap = 1460,
                            CICFlowMeter 120 s timeout cap = 120,000,000 us,
                            min values = 0, header ~ 20 x pkts
    DERIVED-PROFILE ....... documented approximations (IAT / active / idle /
                            packet-length statistics) using ratios verified
                            on the genuine Phase 4 SHAP background
            |
            v
    138 model features (feature_names.json order)

No values are chosen to push the prediction toward a target; every
derivation is documented and identical for benign and attack inputs.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

# ------------------------------------------------------------------
# Documented physical / environmental constants (verified on the
# 50 genuine Phase 4 rows in models/xai/shap_background.csv)
# ------------------------------------------------------------------

MICROSECONDS_PER_SECOND = 1_000_000.0

# CICFlowMeter applies a 120-second flow idle timeout; per-flow IAT /
# duration / activity statistics observed in the data are capped near
# 120,000,000 microseconds.
IAT_CAP_US = 120_000_000.0

# Maximum Ethernet payload size observed for max-across-flows packet
# length features (Pkt Len Max_max == 1460 in all 50 genuine rows).
MTU_BYTES = 1460.0

# Smallest possible IPv4 TCP packet (20 IP + 20 TCP + no payload).
TCP_MIN_PACKET_BYTES = 54.0

# 16-bit TCP window field maximum (Init * Win Byts_max == 65535 in data).
TCP_WINDOW_MAX = 65535.0

# Flag counters: a TCP flag appears at most once per flow in CICFlowMeter
# (verified: SYN/ACK/RST/FIN/PSH/URG/ECE max == 1, CWE/URG-fwd max == 0).
FLAG_MAX_PRESENT = 1.0
FLAG_MAX_ABSENT = 0.0

# Fwd/Bwd Header Len ~= 20 bytes per packet (median relative error 1.5% /
# 4.5% on genuine rows).
HEADER_BYTES_PER_PACKET = 20.0

# Documented profile ratios (p50 across genuine Phase 4 rows).
BWD_IAT_MIN_RATIO = 0.21      # Bwd IAT Min_mean / Bwd IAT Mean_mean
ACTIVE_STD_RATIO = 0.50       # Active Std_mean / Active Mean_mean
ACTIVE_MAX_RATIO = 1.54       # Active Max_mean / Active Mean_mean
ACTIVE_MIN_RATIO = 0.67       # Active Min_mean / Active Mean_mean
IDLE_STD_RATIO = 0.02         # Idle Std_mean / Idle Mean_mean
IDLE_MAX_RATIO = 1.01         # Idle Max_mean / Idle Mean_mean

# Max-across-flows IAT statistics scale with the longest flow duration
# (verified p50 ratios on genuine rows).
IAT_MEAN_MAX_RATIO = 0.75     # Flow IAT Mean_max / Flow Duration_max
IAT_STD_MAX_RATIO = 0.48      # Flow IAT Std_max / Flow Duration_max
IAT_MAX_MAX_RATIO = 0.95      # Flow IAT Max_max / Flow Duration_max
FWD_IAT_MEAN_MAX_RATIO = 0.82 # Fwd IAT Mean_max / Flow Duration_max
FWD_IAT_STD_MAX_RATIO = 0.36  # Fwd IAT Std_max / Flow Duration_max
FWD_IAT_MAX_MAX_RATIO = 0.92  # Fwd IAT Max_max / Flow Duration_max
BWD_IAT_MEAN_MAX_RATIO = 0.73 # Bwd IAT Mean_max / Flow Duration_max
BWD_IAT_STD_MAX_RATIO = 0.35  # Bwd IAT Std_max / Flow Duration_max
BWD_IAT_MAX_MAX_RATIO = 0.82  # Bwd IAT Max_max / Flow Duration_max

# Max-across-flows active / idle statistics scale with the window's
# mean active / idle time (verified p50 ratios on genuine rows).
ACTIVE_MAX_ACROSS_RATIO = 618.0    # Active Mean/Max/Min_max / Active Mean_mean
ACTIVE_STD_ACROSS_RATIO = 368.0    # Active Std_max / Active Mean_mean
IDLE_MAX_ACROSS_RATIO = 24.0       # Idle Mean/Max/Min_max / Idle Mean_mean
IDLE_STD_ACROSS_RATIO = 9.1        # Idle Std_max / Idle Mean_mean

# Largest per-flow mean packet length (max across flows) approaches the
# maximum TCP segment; verified p50 ratios scale with the window mean
# packet size and are capped at the MTU.
FWD_PKT_MEAN_MAX_RATIO = 20.0  # Fwd Pkt Len Mean_max / avg fwd packet
BWD_PKT_MEAN_MAX_RATIO = 13.0  # Bwd Pkt Len Mean_max / avg bwd packet


class RuntimeFeatureTransformer:
    """Build the 138 model features from a practical traffic profile."""

    def __init__(self, feature_names: Sequence[str]):
        self.feature_names = list(feature_names)

        if len(self.feature_names) != 138:
            raise ValueError(
                f"Expected 138 model features, got {len(self.feature_names)}"
            )

    # ================================================================
    # Numeric helpers
    # ================================================================

    @staticmethod
    def _number(
        data: Mapping[str, Any],
        key: str,
        default: float = 0.0,
    ) -> float:
        """Read and validate a numeric input (first matching key)."""
        if isinstance(key, (tuple, list)):
            for candidate in key:
                if candidate in data and data[candidate] not in (None, ""):
                    return RuntimeFeatureTransformer._number(
                        data, candidate, default
                    )
            return float(default)

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
    def _safe_div(numerator: float, denominator: float) -> float:
        """Division that yields 0.0 when the denominator is zero."""
        if denominator == 0.0:
            return 0.0
        return float(numerator) / float(denominator)

    # ================================================================
    # Practical profile parsing (new keys, with legacy fallback)
    # ================================================================

    def _parse_profile(self, traffic: Mapping[str, Any]) -> Dict[str, float]:
        """Extract the semantic traffic-profile variables from the input."""

        num = self._number
        p: Dict[str, float] = {}

        # ---------------- Observation window ----------------
        p["flow_count"] = num(traffic, "flow_count", 0.0)
        p["unique_dst_ports"] = num(traffic, "unique_dst_ports", 0.0)
        p["unique_protocols"] = num(traffic, "unique_protocols", 0.0)

        # ---------------- Traffic volume (window totals) ----------------
        p["fwd_pkts_sum"] = num(traffic, "forward_packets", 0.0)
        p["bwd_pkts_sum"] = num(traffic, "backward_packets", 0.0)
        p["fwd_bytes_sum"] = num(traffic, "forward_bytes", 0.0)
        p["bwd_bytes_sum"] = num(traffic, "backward_bytes", 0.0)

        # ---------------- Largest flow (peak per-flow) ----------------
        p["max_fwd_pkts_flow"] = num(
            traffic, "max_fwd_packets_per_flow", 0.0
        )
        p["max_bwd_pkts_flow"] = num(
            traffic, "max_bwd_packets_per_flow", 0.0
        )
        p["max_fwd_bytes_flow"] = num(
            traffic, "max_fwd_bytes_per_flow", 0.0
        )
        p["max_bwd_bytes_flow"] = num(
            traffic, "max_bwd_bytes_per_flow", 0.0
        )

        # ---------------- Flow duration (seconds -> us) ----------------
        # Legacy key "flow_duration" is microseconds (preserved contract).
        p["dur_mean_us"] = num(
            traffic,
            ("avg_flow_duration_sec",),
            0.0,
        )
        if p["dur_mean_us"] == 0.0:
            p["dur_mean_us"] = num(traffic, "flow_duration", 0.0)
        else:
            p["dur_mean_us"] *= MICROSECONDS_PER_SECOND

        p["dur_max_us"] = num(
            traffic, ("max_flow_duration_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND
        p["dur_min_us"] = num(
            traffic, ("min_flow_duration_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND

        # ---------------- Packet profile (bytes) ----------------
        p["avg_fwd_pkt"] = num(traffic, "avg_fwd_packet_size", 0.0)
        p["avg_bwd_pkt"] = num(traffic, "avg_bwd_packet_size", 0.0)
        p["max_fwd_pkt"] = num(traffic, "max_fwd_packet_size", 0.0)
        p["max_bwd_pkt"] = num(traffic, "max_bwd_packet_size", 0.0)
        p["min_fwd_pkt"] = num(traffic, "min_fwd_packet_size", 0.0)
        p["min_bwd_pkt"] = num(traffic, "min_bwd_packet_size", 0.0)
        p["pkt_std"] = num(traffic, "pkt_len_std", 0.0)

        # ---------------- Traffic rates (per-flow, cannot derive) ------
        p["rate_bytes_ps"] = num(
            traffic, ("avg_flow_bytes_per_sec", "flow_bytes_per_sec"), 0.0
        )
        p["rate_pkts_ps"] = num(
            traffic, ("avg_flow_packets_per_sec", "flow_packets_per_sec"), 0.0
        )
        p["rate_bwd_ps"] = num(
            traffic,
            ("avg_bwd_packets_per_sec", "backward_packets_per_sec"),
            0.0,
        )

        # ---------------- Inter-packet timing (seconds -> us) ----------
        p["iat_mean_us"] = num(
            traffic, ("avg_iat_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND
        p["iat_std_us"] = num(
            traffic, ("iat_std_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND
        p["iat_max_us"] = num(
            traffic, ("max_iat_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND
        p["iat_bwd_mean_us"] = num(
            traffic, ("avg_bwd_iat_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND

        # ---------------- TCP flags ----------------
        p["syn_cnt"] = num(traffic, "syn_flag_cnt", 0.0)
        p["ack_cnt"] = num(traffic, "ack_flag_cnt", 0.0)
        p["rst_cnt"] = num(traffic, "rst_flag_cnt", 0.0)
        p["fin_cnt"] = num(traffic, "fin_flag_cnt", 0.0)
        p["psh_cnt"] = num(traffic, "psh_flag_cnt", 0.0)
        p["urg_cnt"] = num(traffic, "urg_flag_cnt", 0.0)
        p["cwe_cnt"] = num(traffic, "cwe_flag_count", 0.0)
        p["ece_cnt"] = num(traffic, "ece_flag_cnt", 0.0)
        p["fwd_psh_cnt"] = num(traffic, "fwd_psh_flags", 0.0)
        p["fwd_urg_cnt"] = num(traffic, "fwd_urg_flags", 0.0)

        # ---------------- TCP profile ----------------
        p["init_fwd_win"] = num(traffic, "init_fwd_win_byts", 0.0)
        p["init_bwd_win"] = num(traffic, "init_bwd_win_byts", 0.0)
        p["fwd_seg_min"] = num(traffic, "fwd_seg_size_min", 0.0)

        # ---------------- Activity / idle (seconds -> us) --------------
        p["active_mean_us"] = num(
            traffic, ("active_mean_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND
        p["idle_mean_us"] = num(
            traffic, ("idle_mean_sec",), 0.0
        ) * MICROSECONDS_PER_SECOND

        # ---------------- Network balance ----------------
        p["down_up_ratio"] = num(traffic, "down_up_ratio", 0.0)

        return p

    # ================================================================
    # Explicit legacy slot overrides
    # ================================================================

    # Field groups whose legacy snake_case keys directly set every
    # corresponding 138-feature slot (mean / max / min) — preserves the
    # previous transformer contract for scripts and tests.
    LEGACY_OVERRIDE_GROUPS = {
        "Flow IAT Mean": "flow_iat_mean",
        "Flow IAT Std": "flow_iat_std",
        "Flow IAT Max": "flow_iat_max",
        "Fwd IAT Tot": "fwd_iat_tot",
        "Fwd IAT Mean": "fwd_iat_mean",
        "Fwd IAT Std": "fwd_iat_std",
        "Fwd IAT Max": "fwd_iat_max",
        "Bwd IAT Tot": "bwd_iat_tot",
        "Bwd IAT Mean": "bwd_iat_mean",
        "Bwd IAT Std": "bwd_iat_std",
        "Bwd IAT Max": "bwd_iat_max",
        "Bwd IAT Min": "bwd_iat_min",
        "Fwd Pkt Len Max": "fwd_pkt_len_max",
        "Fwd Pkt Len Min": "fwd_pkt_len_min",
        "Fwd Pkt Len Mean": "fwd_pkt_len_mean",
        "Fwd Pkt Len Std": "fwd_pkt_len_std",
        "Bwd Pkt Len Max": "bwd_pkt_len_max",
        "Bwd Pkt Len Min": "bwd_pkt_len_min",
        "Bwd Pkt Len Mean": "bwd_pkt_len_mean",
        "Bwd Pkt Len Std": "bwd_pkt_len_std",
        "Pkt Len Min": "pkt_len_min",
        "Pkt Len Max": "pkt_len_max",
        "Pkt Len Mean": "pkt_len_mean",
        "Pkt Len Std": "pkt_len_std",
        "Pkt Len Var": "pkt_len_var",
        "Pkt Size Avg": "pkt_size_avg",
        "Active Mean": "active_mean",
        "Active Std": "active_std",
        "Active Max": "active_max",
        "Active Min": "active_min",
        "Idle Mean": "idle_mean",
        "Idle Std": "idle_std",
        "Idle Max": "idle_max",
        "Idle Min": "idle_min",
    }

    def _apply_legacy_overrides(
        self,
        traffic: Mapping[str, Any],
        data: Dict[str, float],
    ) -> None:
        """Apply direct feature-slot overrides from legacy input keys."""

        for field, key in self.LEGACY_OVERRIDE_GROUPS.items():
            if key not in traffic or traffic[key] in (None, ""):
                continue

            value = self._number(traffic, key)

            for suffix in ("mean", "max"):
                slot = f"{field}_{suffix}"
                if slot in self.feature_names:
                    data[slot] = value

            min_slot = f"{field}_min"
            if min_slot in self.feature_names:
                data[min_slot] = value

        # Header length overrides (legacy keys)
        if "fwd_header_len" in traffic and traffic["fwd_header_len"] not in (None, ""):
            value = self._number(traffic, "fwd_header_len")
            data["Fwd Header Len_mean"] = value
            data["Fwd Header Len_max"] = value

        if "bwd_header_len" in traffic and traffic["bwd_header_len"] not in (None, ""):
            value = self._number(traffic, "bwd_header_len")
            data["Bwd Header Len_mean"] = value
            data["Bwd Header Len_max"] = value

        # Flag group overrides (legacy keys)
        legacy_flags = {
            "Fwd PSH Flags": "fwd_psh_flags",
            "Fwd URG Flags": "fwd_urg_flags",
            "FIN Flag Cnt": "fin_flag_cnt",
            "SYN Flag Cnt": "syn_flag_cnt",
            "RST Flag Cnt": "rst_flag_cnt",
            "PSH Flag Cnt": "psh_flag_cnt",
            "ACK Flag Cnt": "ack_flag_cnt",
            "URG Flag Cnt": "urg_flag_cnt",
            "CWE Flag Count": "cwe_flag_count",
            "ECE Flag Cnt": "ece_flag_cnt",
        }
        for field, key in legacy_flags.items():
            if key not in traffic or traffic[key] in (None, ""):
                continue

            value = self._number(traffic, key)

            sum_slot = f"{field}_sum"
            if sum_slot in self.feature_names:
                data[sum_slot] = value

            max_slot = f"{field}_max"
            if max_slot in self.feature_names:
                data[max_slot] = FLAG_MAX_PRESENT if value > 0 else FLAG_MAX_ABSENT

    # ================================================================
    # Derivation engine
    # ================================================================

    def _build_features(self, p: Dict[str, float]) -> Dict[str, float]:
        """Construct all 138 feature slots from the parsed profile."""

        data: Dict[str, float] = {}

        # ------------------------------------------------------------
        # 1. Observation window
        # ------------------------------------------------------------
        data["flow_count"] = p["flow_count"]
        data["total_flow_count"] = p["flow_count"]
        data["unique_dst_ports"] = p["unique_dst_ports"]
        data["unique_protocols"] = p["unique_protocols"]

        flow_count = p["flow_count"]

        # ------------------------------------------------------------
        # 2. Volume: sums direct, means = sum / flow_count (exact),
        #    max = largest flow (direct input).
        # ------------------------------------------------------------
        volume = [
            ("Tot Fwd Pkts", p["fwd_pkts_sum"], p["max_fwd_pkts_flow"]),
            ("Tot Bwd Pkts", p["bwd_pkts_sum"], p["max_bwd_pkts_flow"]),
            ("TotLen Fwd Pkts", p["fwd_bytes_sum"], p["max_fwd_bytes_flow"]),
            ("TotLen Bwd Pkts", p["bwd_bytes_sum"], p["max_bwd_bytes_flow"]),
        ]

        for field, total, peak_flow in volume:
            data[f"{field}_sum"] = total
            data[f"{field}_mean"] = self._safe_div(total, flow_count)
            data[f"{field}_max"] = peak_flow

        # ------------------------------------------------------------
        # 3. Flow duration (seconds -> us already applied)
        # ------------------------------------------------------------
        dur_mean = p["dur_mean_us"]
        dur_max = p["dur_max_us"] if p["dur_max_us"] > 0 else dur_mean
        dur_min = p["dur_min_us"]

        data["Flow Duration_mean"] = dur_mean
        data["Flow Duration_min"] = dur_min
        data["Flow Duration_max"] = dur_max

        # ------------------------------------------------------------
        # 4. Inter-arrival time statistics
        # ------------------------------------------------------------
        iat_mean = p["iat_mean_us"]
        iat_std = p["iat_std_us"]
        iat_max = p["iat_max_us"] if p["iat_max_us"] > 0 else dur_max
        iat_bwd = p["iat_bwd_mean_us"]

        fwd_pkts_per_flow = self._safe_div(p["fwd_pkts_sum"], flow_count)
        bwd_pkts_per_flow = self._safe_div(p["bwd_pkts_sum"], flow_count)

        fwd_iat_tot = iat_mean * max(fwd_pkts_per_flow - 1.0, 0.0)
        bwd_iat_tot = iat_bwd * max(bwd_pkts_per_flow - 1.0, 0.0)
        bwd_iat_min = iat_bwd * BWD_IAT_MIN_RATIO

        # Max-across-flows IAT statistics (capped at the flow timeout).
        iat_cap = IAT_CAP_US

        data["Flow IAT Mean_mean"] = iat_mean
        data["Flow IAT Mean_min"] = 0.0
        data["Flow IAT Mean_max"] = min(dur_max * IAT_MEAN_MAX_RATIO, iat_cap)

        data["Flow IAT Std_mean"] = iat_std
        data["Flow IAT Std_min"] = 0.0
        data["Flow IAT Std_max"] = min(dur_max * IAT_STD_MAX_RATIO, iat_cap)

        data["Flow IAT Max_mean"] = iat_max
        data["Flow IAT Max_min"] = 0.0
        data["Flow IAT Max_max"] = min(dur_max * IAT_MAX_MAX_RATIO, iat_cap)

        data["Fwd IAT Tot_mean"] = fwd_iat_tot
        data["Fwd IAT Tot_min"] = 0.0
        data["Fwd IAT Tot_max"] = min(dur_max, iat_cap)

        data["Fwd IAT Mean_mean"] = iat_mean
        data["Fwd IAT Mean_min"] = 0.0
        data["Fwd IAT Mean_max"] = min(dur_max * FWD_IAT_MEAN_MAX_RATIO, iat_cap)

        data["Fwd IAT Std_mean"] = iat_std
        data["Fwd IAT Std_min"] = 0.0
        data["Fwd IAT Std_max"] = min(dur_max * FWD_IAT_STD_MAX_RATIO, iat_cap)

        data["Fwd IAT Max_mean"] = iat_max
        data["Fwd IAT Max_min"] = 0.0
        data["Fwd IAT Max_max"] = min(dur_max * FWD_IAT_MAX_MAX_RATIO, iat_cap)

        data["Bwd IAT Tot_mean"] = bwd_iat_tot
        data["Bwd IAT Tot_max"] = min(dur_max, iat_cap)

        data["Bwd IAT Mean_mean"] = iat_bwd
        data["Bwd IAT Mean_max"] = min(dur_max * BWD_IAT_MEAN_MAX_RATIO, iat_cap)

        data["Bwd IAT Std_mean"] = iat_std
        data["Bwd IAT Std_max"] = min(dur_max * BWD_IAT_STD_MAX_RATIO, iat_cap)

        data["Bwd IAT Max_mean"] = iat_max
        data["Bwd IAT Max_max"] = min(dur_max * BWD_IAT_MAX_MAX_RATIO, iat_cap)

        data["Bwd IAT Min_mean"] = bwd_iat_min
        data["Bwd IAT Min_max"] = min(dur_max * BWD_IAT_MEAN_MAX_RATIO, iat_cap)

        # ------------------------------------------------------------
        # 5. Packet-length statistics
        # ------------------------------------------------------------
        avg_fwd_pkt = p["avg_fwd_pkt"]
        avg_bwd_pkt = p["avg_bwd_pkt"]
        max_fwd_pkt = p["max_fwd_pkt"]
        max_bwd_pkt = p["max_bwd_pkt"]
        min_fwd_pkt = p["min_fwd_pkt"]
        min_bwd_pkt = p["min_bwd_pkt"]
        pkt_std = p["pkt_std"]

        pkt_len_max_mean = max(max_fwd_pkt, max_bwd_pkt)
        pkt_len_min_mean = min(min_fwd_pkt, min_bwd_pkt)

        total_pkts = p["fwd_pkts_sum"] + p["bwd_pkts_sum"]
        has_fwd_pkts = p["fwd_pkts_sum"] > 0
        has_bwd_pkts = p["bwd_pkts_sum"] > 0

        # Physical caps apply only when the corresponding traffic exists.
        pkt_len_min_max = (
            max(min_fwd_pkt, min_bwd_pkt, TCP_MIN_PACKET_BYTES)
            if total_pkts > 0
            else 0.0
        )

        # Per-flow packet-length variance is maximised by a flow that
        # mixes packets at both extremes (small ACK .. MTU). Verified
        # against genuine rows: median relative error 2.4%.
        pkt_len_span_half = max(
            (MTU_BYTES - pkt_len_min_mean) / 2.0, 0.0
        ) if total_pkts > 0 else 0.0
        pkt_len_std_max = pkt_len_span_half
        pkt_len_var_max = pkt_len_span_half ** 2

        if total_pkts > 0 and (avg_fwd_pkt > 0 or avg_bwd_pkt > 0):
            pkt_len_mean = (
                avg_fwd_pkt * p["fwd_pkts_sum"]
                + avg_bwd_pkt * p["bwd_pkts_sum"]
            ) / total_pkts
        else:
            pkt_len_mean = (
                (avg_fwd_pkt + avg_bwd_pkt) / 2.0
                if (avg_fwd_pkt + avg_bwd_pkt) > 0
                else 0.0
            )

        # Largest per-flow mean packet length (max across flows) scales
        # with the window mean packet size, capped at the MTU.
        fwd_pkt_mean_max = (
            min(avg_fwd_pkt * FWD_PKT_MEAN_MAX_RATIO, MTU_BYTES)
            if has_fwd_pkts
            else 0.0
        )
        bwd_pkt_mean_max = (
            min(avg_bwd_pkt * BWD_PKT_MEAN_MAX_RATIO, MTU_BYTES)
            if has_bwd_pkts
            else 0.0
        )
        pkt_len_mean_max = max(fwd_pkt_mean_max, bwd_pkt_mean_max)

        # Forward packet lengths
        data["Fwd Pkt Len Max_mean"] = max_fwd_pkt
        data["Fwd Pkt Len Max_max"] = MTU_BYTES if has_fwd_pkts else 0.0
        data["Fwd Pkt Len Min_mean"] = min_fwd_pkt
        data["Fwd Pkt Len Min_max"] = (
            max(min_fwd_pkt, TCP_MIN_PACKET_BYTES) if has_fwd_pkts else 0.0
        )
        data["Fwd Pkt Len Mean_mean"] = avg_fwd_pkt
        data["Fwd Pkt Len Mean_max"] = fwd_pkt_mean_max
        data["Fwd Pkt Len Std_mean"] = pkt_std
        data["Fwd Pkt Len Std_max"] = pkt_len_std_max

        # Backward packet lengths
        data["Bwd Pkt Len Max_mean"] = max_bwd_pkt
        data["Bwd Pkt Len Max_max"] = MTU_BYTES if has_bwd_pkts else 0.0
        data["Bwd Pkt Len Min_mean"] = min_bwd_pkt
        data["Bwd Pkt Len Min_max"] = (
            max(min_bwd_pkt, TCP_MIN_PACKET_BYTES) if has_bwd_pkts else 0.0
        )
        data["Bwd Pkt Len Mean_mean"] = avg_bwd_pkt
        data["Bwd Pkt Len Mean_max"] = bwd_pkt_mean_max
        data["Bwd Pkt Len Std_mean"] = pkt_std
        data["Bwd Pkt Len Std_max"] = pkt_len_std_max

        # Overall packet lengths
        data["Pkt Len Min_mean"] = pkt_len_min_mean
        data["Pkt Len Min_max"] = pkt_len_min_max
        data["Pkt Len Max_mean"] = pkt_len_max_mean
        data["Pkt Len Max_max"] = MTU_BYTES if total_pkts > 0 else 0.0
        data["Pkt Len Mean_mean"] = pkt_len_mean
        data["Pkt Len Mean_max"] = pkt_len_mean_max
        data["Pkt Len Std_mean"] = pkt_std
        data["Pkt Len Std_max"] = pkt_len_std_max
        data["Pkt Len Var_mean"] = pkt_std ** 2
        data["Pkt Len Var_max"] = pkt_len_var_max
        data["Pkt Size Avg_mean"] = pkt_len_mean
        data["Pkt Size Avg_max"] = pkt_len_mean_max

        # ------------------------------------------------------------
        # 6. Traffic rates (per-flow means; max approximated by mean)
        # ------------------------------------------------------------
        data["Flow Byts/s_mean"] = p["rate_bytes_ps"]
        data["Flow Byts/s_max"] = p["rate_bytes_ps"]
        data["Flow Pkts/s_mean"] = p["rate_pkts_ps"]
        data["Flow Pkts/s_max"] = p["rate_pkts_ps"]
        data["Bwd Pkts/s_mean"] = p["rate_bwd_ps"]
        data["Bwd Pkts/s_max"] = p["rate_bwd_ps"]

        # ------------------------------------------------------------
        # 7. TCP flags (sum direct; max constant per TCP semantics)
        # ------------------------------------------------------------
        flags = [
            ("Fwd PSH Flags", p["fwd_psh_cnt"]),
            ("Fwd URG Flags", p["fwd_urg_cnt"]),
            ("FIN Flag Cnt", p["fin_cnt"]),
            ("SYN Flag Cnt", p["syn_cnt"]),
            ("RST Flag Cnt", p["rst_cnt"]),
            ("PSH Flag Cnt", p["psh_cnt"]),
            ("ACK Flag Cnt", p["ack_cnt"]),
            ("URG Flag Cnt", p["urg_cnt"]),
            ("CWE Flag Count", p["cwe_cnt"]),
            ("ECE Flag Cnt", p["ece_cnt"]),
        ]

        for field, count in flags:
            data[f"{field}_sum"] = count
            data[f"{field}_max"] = (
                FLAG_MAX_PRESENT if count > 0 else FLAG_MAX_ABSENT
            )

        # ------------------------------------------------------------
        # 8. Down/Up ratio
        # ------------------------------------------------------------
        data["Down/Up Ratio_mean"] = p["down_up_ratio"]
        data["Down/Up Ratio_max"] = p["down_up_ratio"]

        # ------------------------------------------------------------
        # 9. Header lengths ~= 20 bytes per packet (verified)
        # ------------------------------------------------------------
        fwd_pkts_mean = self._safe_div(p["fwd_pkts_sum"], flow_count)
        bwd_pkts_mean = self._safe_div(p["bwd_pkts_sum"], flow_count)

        data["Fwd Header Len_mean"] = HEADER_BYTES_PER_PACKET * fwd_pkts_mean
        data["Fwd Header Len_max"] = HEADER_BYTES_PER_PACKET * p["max_fwd_pkts_flow"]
        data["Bwd Header Len_mean"] = HEADER_BYTES_PER_PACKET * bwd_pkts_mean
        data["Bwd Header Len_max"] = HEADER_BYTES_PER_PACKET * p["max_bwd_pkts_flow"]

        # ------------------------------------------------------------
        # 10. Initial TCP windows (mean direct; min 0 / max 65535).
        #     The 65535 cap applies only when window data is present.
        # ------------------------------------------------------------
        data["Init Fwd Win Byts_mean"] = p["init_fwd_win"]
        data["Init Fwd Win Byts_min"] = 0.0
        data["Init Fwd Win Byts_max"] = (
            TCP_WINDOW_MAX if p["init_fwd_win"] > 0 else 0.0
        )

        data["Init Bwd Win Byts_mean"] = p["init_bwd_win"]
        data["Init Bwd Win Byts_min"] = 0.0
        data["Init Bwd Win Byts_max"] = (
            TCP_WINDOW_MAX if p["init_bwd_win"] > 0 else 0.0
        )

        # ------------------------------------------------------------
        # 11. Forward segment size
        # ------------------------------------------------------------
        data["Fwd Seg Size Min_mean"] = p["fwd_seg_min"]
        data["Fwd Seg Size Min_max"] = p["fwd_seg_min"]

        # ------------------------------------------------------------
        # 12. Active / idle behaviour (profile ratios)
        # ------------------------------------------------------------
        active_mean = p["active_mean_us"]
        idle_mean = p["idle_mean_us"]

        # Per-flow (mean-across-flows) statistics.
        data["Active Mean_mean"] = active_mean
        data["Active Std_mean"] = active_mean * ACTIVE_STD_RATIO
        data["Active Max_mean"] = active_mean * ACTIVE_MAX_RATIO
        data["Active Min_mean"] = active_mean * ACTIVE_MIN_RATIO

        # Max-across-flows statistics (scaled, capped at the flow timeout).
        active_across = min(active_mean * ACTIVE_MAX_ACROSS_RATIO, IAT_CAP_US)
        active_std_across = min(
            active_mean * ACTIVE_STD_ACROSS_RATIO, IAT_CAP_US
        )
        idle_across = min(idle_mean * IDLE_MAX_ACROSS_RATIO, IAT_CAP_US)
        idle_std_across = min(idle_mean * IDLE_STD_ACROSS_RATIO, IAT_CAP_US)

        data["Active Mean_max"] = active_across
        data["Active Std_max"] = active_std_across
        data["Active Max_max"] = active_across
        data["Active Min_max"] = active_across

        data["Idle Mean_mean"] = idle_mean
        data["Idle Mean_min"] = idle_mean
        data["Idle Mean_max"] = idle_across
        data["Idle Std_mean"] = idle_mean * IDLE_STD_RATIO
        data["Idle Std_min"] = idle_mean * IDLE_STD_RATIO
        data["Idle Std_max"] = idle_std_across
        data["Idle Max_mean"] = idle_mean * IDLE_MAX_RATIO
        data["Idle Max_min"] = idle_mean * IDLE_MAX_RATIO
        data["Idle Max_max"] = idle_across
        data["Idle Min_mean"] = idle_mean
        data["Idle Min_min"] = 0.0
        data["Idle Min_max"] = idle_across

        return data

    # ================================================================
    # Public transform
    # ================================================================

    def transform(
        self,
        traffic: Mapping[str, Any],
    ) -> pd.DataFrame:
        """
        Convert a practical 5-minute traffic-window profile into a 1-row,
        138-feature DataFrame.
        """

        profile = self._parse_profile(traffic)

        data = self._build_features(profile)

        # Legacy direct slot overrides take precedence over derivations.
        self._apply_legacy_overrides(traffic, data)

        # ------------------------------------------------------------
        # Final schema enforcement
        # ------------------------------------------------------------
        output = pd.DataFrame(
            [[data.get(name, 0.0) for name in self.feature_names]],
            columns=self.feature_names,
        )

        output = output.apply(
            pd.to_numeric,
            errors="coerce",
        )

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