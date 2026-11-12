"""
Shared constants for the NetVision AI file ingestion layer.

The ingestion layer is deliberately frozen against the existing model
contract:

    raw flows / packets  ->  5-minute windows  ->  40-field practical profile
                                                     |
                                                     v
                                          RuntimeFeatureTransformer (untouched)
                                                     |
                                                     v
                                                138 model features

Nothing in this module changes the trained models, the ensemble, the
transformer, XAI or MITRE mapping.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, Tuple

# ------------------------------------------------------------------
# Model / window contract (must match the Phase 4 / Phase 5 design)
# ------------------------------------------------------------------

WINDOW_MINUTES = 5
WINDOW_SECONDS = WINDOW_MINUTES * 60

PROFILE_FIELD_COUNT = 40
MODEL_FEATURE_COUNT = 138

#: The 40 practical profile fields accepted by the frontend form and by
#: ``RuntimeFeatureTransformer``. Order mirrors the form groups.
PROFILE_FIELDS: Tuple[str, ...] = (
    # S1 - observation window
    "flow_count",
    "unique_dst_ports",
    "unique_protocols",
    # S2 - traffic volume (window totals)
    "forward_packets",
    "backward_packets",
    "forward_bytes",
    "backward_bytes",
    # S3 - largest flow (peak per-flow)
    "max_fwd_packets_per_flow",
    "max_bwd_packets_per_flow",
    "max_fwd_bytes_per_flow",
    "max_bwd_bytes_per_flow",
    # S4 - flow duration (seconds)
    "avg_flow_duration_sec",
    "max_flow_duration_sec",
    "min_flow_duration_sec",
    # S5 - packet profile (bytes)
    "avg_fwd_packet_size",
    "avg_bwd_packet_size",
    "max_fwd_packet_size",
    "max_bwd_packet_size",
    "min_fwd_packet_size",
    "min_bwd_packet_size",
    "pkt_len_std",
    # S6 - traffic rates (per-flow means)
    "avg_flow_bytes_per_sec",
    "avg_flow_packets_per_sec",
    "avg_bwd_packets_per_sec",
    # S7 - inter-packet timing (seconds)
    "avg_iat_sec",
    "iat_std_sec",
    "max_iat_sec",
    "avg_bwd_iat_sec",
    # S8 - TCP flags
    "syn_flag_cnt",
    "ack_flag_cnt",
    "rst_flag_cnt",
    "fin_flag_cnt",
    "psh_flag_cnt",
    "urg_flag_cnt",
    # S9 - TCP profile
    "init_fwd_win_byts",
    "init_bwd_win_byts",
    "fwd_seg_size_min",
    # S10 - activity / idle (seconds)
    "active_mean_sec",
    "idle_mean_sec",
    # S11 - network balance
    "down_up_ratio",
)

PROFILE_FIELD_SET = frozenset(PROFILE_FIELDS)

# ------------------------------------------------------------------
# Canonical CICFlowMeter flow columns used by the aggregator
# ------------------------------------------------------------------

#: Columns the aggregator reads from a flow table. A raw CICFlowMeter CSV
#: is normalised onto these names before aggregation, and the PCAP
#: reconstructor emits them directly.
FLOW_COLUMNS: Tuple[str, ...] = (
    "Timestamp",
    "Dst Port",
    "Protocol",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Flow Duration",
    "Fwd Pkt Len Max",
    "Fwd Pkt Len Min",
    "Fwd Pkt Len Mean",
    "Fwd Pkt Len Std",
    "Bwd Pkt Len Max",
    "Bwd Pkt Len Min",
    "Bwd Pkt Len Mean",
    "Bwd Pkt Len Std",
    "Pkt Len Std",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Bwd Pkts/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Bwd IAT Mean",
    "SYN Flag Cnt",
    "ACK Flag Cnt",
    "RST Flag Cnt",
    "FIN Flag Cnt",
    "PSH Flag Cnt",
    "URG Flag Cnt",
    "Init Fwd Win Byts",
    "Init Bwd Win Byts",
    "Fwd Seg Size Min",
    "Active Mean",
    "Idle Mean",
    "Down/Up Ratio",
    "Label",
)

#: Raw CICFlowMeter headers vary between tool versions. Each canonical
#: name lists the spelling variants observed in CIC-IDS2018 and the
#: common CICFlowMeter Python/Java exports.
FLOW_COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "Timestamp": (
        "Timestamp",
        "Flow Start Time",
        "Start Time",
        "Time",
    ),
    "Dst Port": (
        "Dst Port",
        "Destination Port",
        "DstPort",
        "DestinationPort",
    ),
    "Protocol": (
        "Protocol",
        "Protocol Type",
        "IP Protocol",
    ),
    "Tot Fwd Pkts": (
        "Tot Fwd Pkts",
        "Total Fwd Packets",
        "Total Forward Packets",
    ),
    "Tot Bwd Pkts": (
        "Tot Bwd Pkts",
        "Total Bwd Packets",
        "Total Backward Packets",
    ),
    "TotLen Fwd Pkts": (
        "TotLen Fwd Pkts",
        "Total Length of Fwd Packets",
        "Total Length Fwd Packets",
        "Total Length of Forward Packets",
    ),
    "TotLen Bwd Pkts": (
        "TotLen Bwd Pkts",
        "Total Length of Bwd Packets",
        "Total Length Bwd Packets",
        "Total Length of Backward Packets",
    ),
    "Flow Duration": ("Flow Duration",),
    "Fwd Pkt Len Max": (
        "Fwd Pkt Len Max",
        "Fwd Packet Length Max",
        "Fwd Paket Len Max",
    ),
    "Fwd Pkt Len Min": (
        "Fwd Pkt Len Min",
        "Fwd Packet Length Min",
        "Fwd Paket Len Min",
    ),
    "Fwd Pkt Len Mean": (
        "Fwd Pkt Len Mean",
        "Fwd Packet Length Mean",
        "Fwd Paket Len Mean",
    ),
    "Fwd Pkt Len Std": (
        "Fwd Pkt Len Std",
        "Fwd Packet Length Std",
        "Fwd Paket Len Std",
    ),
    "Bwd Pkt Len Max": (
        "Bwd Pkt Len Max",
        "Bwd Packet Length Max",
        "Bwd Paket Len Max",
    ),
    "Bwd Pkt Len Min": (
        "Bwd Pkt Len Min",
        "Bwd Packet Length Min",
        "Bwd Paket Len Min",
    ),
    "Bwd Pkt Len Mean": (
        "Bwd Pkt Len Mean",
        "Bwd Packet Length Mean",
        "Bwd Paket Len Mean",
    ),
    "Bwd Pkt Len Std": (
        "Bwd Pkt Len Std",
        "Bwd Packet Length Std",
        "Bwd Paket Len Std",
    ),
    "Pkt Len Std": (
        "Pkt Len Std",
        "Packet Length Std",
    ),
    "Flow Byts/s": (
        "Flow Byts/s",
        "Flow Bytes/s",
        "Flow Bytes per Second",
    ),
    "Flow Pkts/s": (
        "Flow Pkts/s",
        "Flow Packets/s",
        "Flow Packets per Second",
    ),
    "Bwd Pkts/s": (
        "Bwd Pkts/s",
        "Bwd Packets/s",
        "Bwd Packets per Second",
    ),
    "Flow IAT Mean": ("Flow IAT Mean",),
    "Flow IAT Std": ("Flow IAT Std",),
    "Flow IAT Max": ("Flow IAT Max",),
    "Bwd IAT Mean": ("Bwd IAT Mean",),
    "SYN Flag Cnt": (
        "SYN Flag Cnt",
        "SYN Flag Count",
        "SYN Flags",
    ),
    "ACK Flag Cnt": (
        "ACK Flag Cnt",
        "ACK Flag Count",
        "ACK Flags",
    ),
    "RST Flag Cnt": (
        "RST Flag Cnt",
        "RST Flag Count",
        "RST Flags",
    ),
    "FIN Flag Cnt": (
        "FIN Flag Cnt",
        "FIN Flag Count",
        "FIN Flags",
    ),
    "PSH Flag Cnt": (
        "PSH Flag Cnt",
        "PSH Flag Count",
        "PSH Flags",
    ),
    "URG Flag Cnt": (
        "URG Flag Cnt",
        "URG Flag Count",
        "URG Flags",
    ),
    "Init Fwd Win Byts": (
        "Init Fwd Win Byts",
        "Init Fwd Win Bytes",
        "Init Win Bytes Forward",
        "Init_Win_bytes_forward",
        "Init Win Bytes Fwd",
    ),
    "Init Bwd Win Byts": (
        "Init Bwd Win Byts",
        "Init Bwd Win Bytes",
        "Init Win Bytes Backward",
        "Init_Win_bytes_backward",
        "Init Win Bytes Bwd",
    ),
    "Fwd Seg Size Min": (
        "Fwd Seg Size Min",
        "Fwd Segment Size Min",
        "min_seg_size_forward",
    ),
    "Active Mean": ("Active Mean", "Active Mean Time"),
    "Idle Mean": ("Idle Mean", "Idle Mean Time"),
    "Down/Up Ratio": ("Down/Up Ratio", "Down Up Ratio"),
    "Label": ("Label", "Class", "Attack Label"),
}

#: Columns that are essential for producing a complete 40-field profile.
#: Five low-importance columns are optional and default to zero with a
#: warning when a CSV variant omits them.
REQUIRED_FLOW_COLUMNS: Tuple[str, ...] = (
    "Dst Port",
    "Protocol",
    "Tot Fwd Pkts",
    "Tot Bwd Pkts",
    "TotLen Fwd Pkts",
    "TotLen Bwd Pkts",
    "Flow Duration",
    "Fwd Pkt Len Max",
    "Fwd Pkt Len Min",
    "Fwd Pkt Len Mean",
    "Bwd Pkt Len Max",
    "Bwd Pkt Len Min",
    "Bwd Pkt Len Mean",
    "Pkt Len Std",
    "Flow Byts/s",
    "Flow Pkts/s",
    "Bwd Pkts/s",
    "Flow IAT Mean",
    "Flow IAT Std",
    "Flow IAT Max",
    "Bwd IAT Mean",
    "SYN Flag Cnt",
    "ACK Flag Cnt",
    "RST Flag Cnt",
    "FIN Flag Cnt",
    "PSH Flag Cnt",
    "URG Flag Cnt",
    "Init Fwd Win Byts",
    "Init Bwd Win Byts",
)

OPTIONAL_FLOW_COLUMNS: Tuple[str, ...] = (
    "Fwd Seg Size Min",
    "Active Mean",
    "Idle Mean",
    "Down/Up Ratio",
)

NUMERIC_FLOW_COLUMNS: Tuple[str, ...] = tuple(
    column
    for column in FLOW_COLUMNS
    if column not in ("Timestamp", "Label")
)

# ------------------------------------------------------------------
# Feature-CSV detection (bonus 138-feature path)
# ------------------------------------------------------------------

FEATURE_SUFFIXES: Tuple[str, ...] = ("_mean", "_max", "_min", "_sum")

#: Four of the 138 model features do not carry an aggregation suffix.
WINDOW_FEATURE_NAMES: Tuple[str, ...] = (
    "flow_count",
    "total_flow_count",
    "unique_dst_ports",
    "unique_protocols",
)

#: Columns that may accompany a Phase 4 feature export but are not model
#: inputs. They are excluded from the 138-feature selection.
FEATURE_METADATA_COLUMNS: frozenset = frozenset(
    {
        "window_start",
        "window_end",
        "dataset_day",
        "timestamp",
        "label",
        "current_attack_state",
        "attack_flow_count",
        "current_attack_ratio",
        "future_attack_state",
    }
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_NON_ALNUM = re.compile(r"[^0-9a-zA-Z]+")
_WHITESPACE = re.compile(r"\s+")


def normalize_column(name: object) -> str:
    """Normalise a column/header name for tolerant matching.

    ``"Tot Fwd Pkts"``, ``"tot_fwd_pkts"`` and ``"TOT  FWD  PKTS"`` all
    become ``"tot fwd pkts"``. A UTF-8 BOM and surrounding whitespace are
    removed.
    """

    text = str(name).replace("\ufeff", "").strip()
    text = _NON_ALNUM.sub(" ", text)
    return _WHITESPACE.sub(" ", text).strip().lower()


def _build_lookup(aliases: Dict[str, Iterable[str]]) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    for canonical, variants in aliases.items():
        lookup[normalize_column(canonical)] = canonical
        for variant in variants:
            lookup[normalize_column(variant)] = canonical
    return lookup


FLOW_ALIAS_LOOKUP: Dict[str, str] = _build_lookup(FLOW_COLUMN_ALIASES)

PROFILE_ALIAS_LOOKUP: Dict[str, str] = {
    normalize_column(field): field for field in PROFILE_FIELDS
}

# Common friendly spellings for an already-aggregated profile CSV.
_PROFILE_EXTRA_ALIASES = {
    "total flow count": "flow_count",
    "total flows": "flow_count",
    "flows": "flow_count",
    "unique destination ports": "unique_dst_ports",
    "destination ports": "unique_dst_ports",
    "protocols": "unique_protocols",
    "total forward packets": "forward_packets",
    "total backward packets": "backward_packets",
    "total forward bytes": "forward_bytes",
    "total backward bytes": "backward_bytes",
    "average flow duration seconds": "avg_flow_duration_sec",
    "longest flow duration seconds": "max_flow_duration_sec",
    "shortest flow duration seconds": "min_flow_duration_sec",
    "average forward packet size": "avg_fwd_packet_size",
    "average backward packet size": "avg_bwd_packet_size",
    "average flow bytes per sec": "avg_flow_bytes_per_sec",
    "average flow packets per sec": "avg_flow_packets_per_sec",
    "average backward packets per sec": "avg_bwd_packets_per_sec",
    "average iat seconds": "avg_iat_sec",
    "iat std seconds": "iat_std_sec",
    "max iat seconds": "max_iat_sec",
    "average backward iat seconds": "avg_bwd_iat_sec",
    "syn count": "syn_flag_cnt",
    "ack count": "ack_flag_cnt",
    "rst count": "rst_flag_cnt",
    "fin count": "fin_flag_cnt",
    "psh count": "psh_flag_cnt",
    "urg count": "urg_flag_cnt",
    "initial forward window": "init_fwd_win_byts",
    "initial backward window": "init_bwd_win_byts",
    "minimum forward segment size": "fwd_seg_size_min",
    "average active time": "active_mean_sec",
    "average idle time": "idle_mean_sec",
    "down up ratio": "down_up_ratio",
}
PROFILE_ALIAS_LOOKUP.update(_PROFILE_EXTRA_ALIASES)


def resolve_flow_column(name: object) -> str:
    """Return the canonical flow column for a raw header, or ``""``."""
    return FLOW_ALIAS_LOOKUP.get(normalize_column(name), "")


def resolve_profile_field(name: object) -> str:
    """Return the canonical profile field for a CSV header, or ``""``."""
    return PROFILE_ALIAS_LOOKUP.get(normalize_column(name), "")


# Normalised lookups used by CSV shape detection. They are defined last
# because they depend on ``normalize_column``.
WINDOW_FEATURE_NORMALIZED: frozenset = frozenset(
    normalize_column(name) for name in WINDOW_FEATURE_NAMES
)

FEATURE_METADATA_NORMALIZED: frozenset = frozenset(
    normalize_column(name) for name in FEATURE_METADATA_COLUMNS
)
