"""
Request and response schemas for the NetVision AI forecasting API.
"""

from typing import Any, Dict, Optional
import math
from pydantic import BaseModel, Field, model_validator


DISALLOWED_INPUT_KEYS = {
    "future_attack_state",
    "ground_truth",
    "model_prediction",
    "shap_values",
    "mitre_mapping",
}


class ForecastRequest(BaseModel):
    """
    Input schema for the network attack forecasting endpoint.

    Supports both:
    1. Practical network traffic input (individual fields or a 'traffic' dictionary).
    2. Direct 138 model-ready features dictionary (via 'features').
    """

    features: Optional[Dict[str, float]] = Field(
        default=None,
        description="138 model-ready network traffic features for direct model querying."
    )

    traffic: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Practical network traffic input fields dictionary."
    )

    # Core practical fields at top-level for convenience
    flow_count: Optional[float] = Field(default=None, ge=0)
    unique_dst_ports: Optional[float] = Field(default=None, ge=0)
    unique_protocols: Optional[float] = Field(default=None, ge=0)

    forward_packets: Optional[float] = Field(default=None, ge=0)
    backward_packets: Optional[float] = Field(default=None, ge=0)

    forward_bytes: Optional[float] = Field(default=None, ge=0)
    backward_bytes: Optional[float] = Field(default=None, ge=0)

    flow_duration: Optional[float] = Field(default=None, ge=0)

    flow_bytes_per_sec: Optional[float] = Field(default=None, ge=0)
    flow_packets_per_sec: Optional[float] = Field(default=None, ge=0)
    backward_packets_per_sec: Optional[float] = Field(default=None, ge=0)

    down_up_ratio: Optional[float] = Field(default=None, ge=0)

    syn_flag_cnt: Optional[float] = Field(default=None, ge=0)
    ack_flag_cnt: Optional[float] = Field(default=None, ge=0)
    rst_flag_cnt: Optional[float] = Field(default=None, ge=0)
    fin_flag_cnt: Optional[float] = Field(default=None, ge=0)
    psh_flag_cnt: Optional[float] = Field(default=None, ge=0)
    urg_flag_cnt: Optional[float] = Field(default=None, ge=0)

    fwd_psh_flags: Optional[float] = Field(default=None, ge=0)
    fwd_urg_flags: Optional[float] = Field(default=None, ge=0)

    cwe_flag_count: Optional[float] = Field(default=None, ge=0)
    ece_flag_cnt: Optional[float] = Field(default=None, ge=0)

    # ------------------------------------------------------------------
    # Extended 5-minute traffic-window profile fields
    # (see docs/architecture/runtime_input_design.md)
    # ------------------------------------------------------------------

    # S3 - Largest flow (peak per-flow)
    max_fwd_packets_per_flow: Optional[float] = Field(default=None, ge=0)
    max_bwd_packets_per_flow: Optional[float] = Field(default=None, ge=0)
    max_fwd_bytes_per_flow: Optional[float] = Field(default=None, ge=0)
    max_bwd_bytes_per_flow: Optional[float] = Field(default=None, ge=0)

    # S4 - Flow duration (seconds; converted to microseconds internally)
    avg_flow_duration_sec: Optional[float] = Field(default=None, ge=0)
    max_flow_duration_sec: Optional[float] = Field(default=None, ge=0)
    min_flow_duration_sec: Optional[float] = Field(default=None, ge=0)

    # S5 - Packet profile (bytes)
    avg_fwd_packet_size: Optional[float] = Field(default=None, ge=0)
    avg_bwd_packet_size: Optional[float] = Field(default=None, ge=0)
    max_fwd_packet_size: Optional[float] = Field(default=None, ge=0)
    max_bwd_packet_size: Optional[float] = Field(default=None, ge=0)
    min_fwd_packet_size: Optional[float] = Field(default=None, ge=0)
    min_bwd_packet_size: Optional[float] = Field(default=None, ge=0)
    pkt_len_std: Optional[float] = Field(default=None, ge=0)

    # S6 - Traffic rates (per-flow means)
    avg_flow_bytes_per_sec: Optional[float] = Field(default=None, ge=0)
    avg_flow_packets_per_sec: Optional[float] = Field(default=None, ge=0)
    avg_bwd_packets_per_sec: Optional[float] = Field(default=None, ge=0)

    # S7 - Inter-packet timing (seconds; converted to microseconds)
    avg_iat_sec: Optional[float] = Field(default=None, ge=0)
    iat_std_sec: Optional[float] = Field(default=None, ge=0)
    max_iat_sec: Optional[float] = Field(default=None, ge=0)
    avg_bwd_iat_sec: Optional[float] = Field(default=None, ge=0)

    # S9 - TCP profile
    init_fwd_win_byts: Optional[float] = Field(default=None, ge=0)
    init_bwd_win_byts: Optional[float] = Field(default=None, ge=0)
    fwd_seg_size_min: Optional[float] = Field(default=None, ge=0)

    # S10 - Activity / idle behaviour (seconds; converted to microseconds)
    active_mean_sec: Optional[float] = Field(default=None, ge=0)
    idle_mean_sec: Optional[float] = Field(default=None, ge=0)

    class Config:
        extra = "allow"

    @model_validator(mode="after")
    def validate_inputs(self) -> "ForecastRequest":
        # Ensure no disallowed input keys are passed
        if self.traffic:
            invalid_keys = set(self.traffic.keys()).intersection(DISALLOWED_INPUT_KEYS)
            if invalid_keys:
                raise ValueError(
                    f"Disallowed input keys in traffic dictionary: {invalid_keys}"
                )

        # Validate numeric types and finite values
        if self.features:
            for k, v in self.features.items():
                if k in DISALLOWED_INPUT_KEYS:
                    raise ValueError(f"Disallowed feature key: {k}")
                if not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
                    raise ValueError(f"Feature '{k}' must be a finite number.")

        return self