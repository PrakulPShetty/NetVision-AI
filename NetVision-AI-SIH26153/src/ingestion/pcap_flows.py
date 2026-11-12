"""Approximate CICFlowMeter-style flow reconstruction from PCAP/PCAPNG.

This module intentionally produces the *same canonical flow columns* as a
CICFlowMeter export, so the Phase 4 window aggregator is shared between
CSV and packet-capture ingestion.

Documented approximations (also repeated in docs/api/file_ingestion_api.md):

* Bidirectional 5-tuple flow key; the first packet seen defines the
  forward direction.
* Idle timeout: 120 s. A flow is finalised after 120 s without packets.
* Active/idle statistics use a 5 s activity threshold (CICFlowMeter's
  activity timeout).
* Packet length = IP total length, excluding link-layer headers, capped at
  1460 bytes to stay inside the training distribution's MTU.
* Per-flow standard deviations are population standard deviations.
* No TCP stream reassembly: retransmissions / out-of-order packets are
  counted as observed.
* Flow start timestamps (not packet end times) assign a flow to a 5-minute
  window, matching CICFlowMeter's ``Timestamp`` semantics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.ingestion.errors import (
    EmptyFileError,
    IngestionLimitError,
    MalformedFileError,
)

# CICFlowMeter defaults.
IDLE_TIMEOUT_SECONDS = 120.0
ACTIVE_TIMEOUT_SECONDS = 5.0
PACKET_LENGTH_CAP = 1460.0
SWEEP_INTERVAL_SECONDS = 30.0

PCAP_MAGIC = {
    b"\xd4\xc3\xb2\xa1",
    b"\xa1\xb2\xc3\xd4",
    b"\x4d\x3c\xb2\xa1",
    b"\xa1\xb2\x3c\x4d",
}
PCAPNG_MAGIC = b"\x0a\x0d\x0d\x0a"

# TCP flag bits.
FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20


def looks_like_pcap(prefix: bytes) -> bool:
    return prefix[:4] in PCAP_MAGIC or prefix[:4] == PCAPNG_MAGIC


def _stddev(count: int, total: float, total_sq: float) -> float:
    if count <= 0:
        return 0.0
    mean = total / count
    variance = max(total_sq / count - mean * mean, 0.0)
    return math.sqrt(variance)


@dataclass
class _Flow:
    first_ts: float
    last_ts: float
    initiator_ip: str
    initiator_port: int
    responder_ip: str
    responder_port: int
    dst_port: int
    protocol: int

    fwd_pkts: int = 0
    bwd_pkts: int = 0
    fwd_bytes: float = 0.0
    bwd_bytes: float = 0.0

    fwd_len_sum: float = 0.0
    fwd_len_sq: float = 0.0
    bwd_len_sum: float = 0.0
    bwd_len_sq: float = 0.0
    all_len_sum: float = 0.0
    all_len_sq: float = 0.0

    fwd_len_min: Optional[float] = None
    fwd_len_max: float = 0.0
    bwd_len_min: Optional[float] = None
    bwd_len_max: float = 0.0

    last_fwd_ts: Optional[float] = None
    last_bwd_ts: Optional[float] = None

    fwd_iat_sum: float = 0.0
    fwd_iat_sq: float = 0.0
    fwd_iat_count: int = 0
    fwd_iat_max: float = 0.0

    bwd_iat_sum: float = 0.0
    bwd_iat_sq: float = 0.0
    bwd_iat_count: int = 0
    bwd_iat_max: float = 0.0

    iat_sum: float = 0.0
    iat_sq: float = 0.0
    iat_count: int = 0
    iat_max: float = 0.0

    flags: int = 0
    init_fwd_win: Optional[int] = None
    init_bwd_win: Optional[int] = None
    fwd_seg_min: Optional[int] = None

    active_start: Optional[float] = None
    active_sum: float = 0.0
    active_count: int = 0
    idle_sum: float = 0.0
    idle_count: int = 0

    def add(
        self,
        *,
        ts: float,
        forward: bool,
        length: float,
        tcp_flags: int,
        tcp_window: Optional[int],
        payload_length: int,
        is_tcp: bool,
    ) -> None:
        # Inter-arrival timing (seconds; converted to microseconds on export).
        # The first packet of a flow has no predecessor.
        if (
            self.last_ts is not None
            and (self.fwd_pkts + self.bwd_pkts) > 0
        ):
            gap = max(ts - self.last_ts, 0.0)
            self.iat_sum += gap
            self.iat_sq += gap * gap
            self.iat_count += 1
            self.iat_max = max(self.iat_max, gap)

        # Active / idle bursts, using the 5 s activity threshold.
        if self.active_start is None:
            self.active_start = ts
        elif self.last_ts is not None and ts - self.last_ts > ACTIVE_TIMEOUT_SECONDS:
            self.active_sum += max(self.last_ts - self.active_start, 0.0)
            self.active_count += 1
            self.idle_sum += ts - self.last_ts
            self.idle_count += 1
            self.active_start = ts

        if forward:
            if self.last_fwd_ts is not None:
                gap = max(ts - self.last_fwd_ts, 0.0)
                self.fwd_iat_sum += gap
                self.fwd_iat_sq += gap * gap
                self.fwd_iat_count += 1
                self.fwd_iat_max = max(self.fwd_iat_max, gap)
            self.last_fwd_ts = ts
            self.fwd_pkts += 1
            self.fwd_bytes += length
            self.fwd_len_sum += length
            self.fwd_len_sq += length * length
            self.fwd_len_min = (
                length if self.fwd_len_min is None else min(self.fwd_len_min, length)
            )
            self.fwd_len_max = max(self.fwd_len_max, length)
            if is_tcp:
                if self.init_fwd_win is None and tcp_window is not None:
                    self.init_fwd_win = int(tcp_window)
                if payload_length > 0:
                    self.fwd_seg_min = (
                        payload_length
                        if self.fwd_seg_min is None
                        else min(self.fwd_seg_min, payload_length)
                    )
        else:
            if self.last_bwd_ts is not None:
                gap = max(ts - self.last_bwd_ts, 0.0)
                self.bwd_iat_sum += gap
                self.bwd_iat_sq += gap * gap
                self.bwd_iat_count += 1
                self.bwd_iat_max = max(self.bwd_iat_max, gap)
            self.last_bwd_ts = ts
            self.bwd_pkts += 1
            self.bwd_bytes += length
            self.bwd_len_sum += length
            self.bwd_len_sq += length * length
            self.bwd_len_min = (
                length if self.bwd_len_min is None else min(self.bwd_len_min, length)
            )
            self.bwd_len_max = max(self.bwd_len_max, length)
            if is_tcp and self.init_bwd_win is None and tcp_window is not None:
                self.init_bwd_win = int(tcp_window)

        self.all_len_sum += length
        self.all_len_sq += length * length
        self.flags |= tcp_flags
        self.last_ts = ts

    def finalise(self) -> None:
        if self.active_start is not None:
            self.active_sum += max(self.last_ts - self.active_start, 0.0)
            self.active_count += 1

    def to_record(self) -> Dict[str, Any]:
        self.finalise()

        duration_us = max(self.last_ts - self.first_ts, 0.0) * 1_000_000.0
        duration_s = duration_us / 1_000_000.0
        total_pkts = self.fwd_pkts + self.bwd_pkts
        total_bytes = self.fwd_bytes + self.bwd_bytes

        def per_second(value: float) -> float:
            return value / duration_s if duration_s > 0 else 0.0

        fwd_mean = self.fwd_bytes / self.fwd_pkts if self.fwd_pkts else 0.0
        bwd_mean = self.bwd_bytes / self.bwd_pkts if self.bwd_pkts else 0.0

        iat_mean = (
            (self.iat_sum / self.iat_count) * 1_000_000.0
            if self.iat_count
            else 0.0
        )
        iat_std = _stddev(self.iat_count, self.iat_sum, self.iat_sq) * 1_000_000.0
        iat_max = self.iat_max * 1_000_000.0

        bwd_iat_mean = (
            (self.bwd_iat_sum / self.bwd_iat_count) * 1_000_000.0
            if self.bwd_iat_count
            else 0.0
        )

        active_mean = (
            (self.active_sum / self.active_count) * 1_000_000.0
            if self.active_count
            else 0.0
        )
        idle_mean = (
            (self.idle_sum / self.idle_count) * 1_000_000.0
            if self.idle_count
            else 0.0
        )

        return {
            "Timestamp": pd.Timestamp(self.first_ts, unit="s", tz="UTC").tz_convert(
                None
            ),
            "Dst Port": int(self.dst_port),
            "Protocol": int(self.protocol),
            "Tot Fwd Pkts": float(self.fwd_pkts),
            "Tot Bwd Pkts": float(self.bwd_pkts),
            "TotLen Fwd Pkts": float(self.fwd_bytes),
            "TotLen Bwd Pkts": float(self.bwd_bytes),
            "Flow Duration": float(duration_us),
            "Fwd Pkt Len Max": float(self.fwd_len_max),
            "Fwd Pkt Len Min": float(self.fwd_len_min or 0.0),
            "Fwd Pkt Len Mean": float(fwd_mean),
            "Fwd Pkt Len Std": float(
                _stddev(self.fwd_pkts, self.fwd_len_sum, self.fwd_len_sq)
            ),
            "Bwd Pkt Len Max": float(self.bwd_len_max),
            "Bwd Pkt Len Min": float(self.bwd_len_min or 0.0),
            "Bwd Pkt Len Mean": float(bwd_mean),
            "Bwd Pkt Len Std": float(
                _stddev(self.bwd_pkts, self.bwd_len_sum, self.bwd_len_sq)
            ),
            "Pkt Len Std": float(
                _stddev(total_pkts, self.all_len_sum, self.all_len_sq)
            ),
            "Flow Byts/s": float(per_second(total_bytes)),
            "Flow Pkts/s": float(per_second(total_pkts)),
            "Bwd Pkts/s": float(per_second(self.bwd_pkts)),
            "Flow IAT Mean": float(iat_mean),
            "Flow IAT Std": float(iat_std),
            "Flow IAT Max": float(iat_max),
            "Bwd IAT Mean": float(bwd_iat_mean),
            "SYN Flag Cnt": float(1 if self.flags & SYN else 0),
            "ACK Flag Cnt": float(1 if self.flags & ACK else 0),
            "RST Flag Cnt": float(1 if self.flags & RST else 0),
            "FIN Flag Cnt": float(1 if self.flags & FIN else 0),
            "PSH Flag Cnt": float(1 if self.flags & PSH else 0),
            "URG Flag Cnt": float(1 if self.flags & URG else 0),
            "Init Fwd Win Byts": float(self.init_fwd_win or 0),
            "Init Bwd Win Byts": float(self.init_bwd_win or 0),
            "Fwd Seg Size Min": float(self.fwd_seg_min or 0),
            "Active Mean": float(active_mean),
            "Idle Mean": float(idle_mean),
            "Down/Up Ratio": float(
                self.bwd_bytes / self.fwd_bytes if self.fwd_bytes > 0 else 0.0
            ),
        }


def _open_reader(fileobj):
    try:
        from scapy.utils import PcapNgReader, PcapReader
    except ImportError as exc:  # pragma: no cover - dependency is in requirements
        raise RuntimeError(
            "PCAP ingestion requires the 'scapy' package. Install it with "
            "'pip install scapy'."
        ) from exc

    fileobj.seek(0)
    magic = fileobj.read(4)
    fileobj.seek(0)

    if magic == PCAPNG_MAGIC:
        return PcapNgReader(fileobj)

    if magic in PCAP_MAGIC:
        return PcapReader(fileobj)

    raise MalformedFileError(
        "The file does not start with a PCAP or PCAPNG magic header."
    )


def extract_flow_frame(
    fileobj,
    *,
    max_packets: int,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Reconstruct approximate flow records from a PCAP/PCAPNG upload."""

    try:
        from scapy.all import IP, IPv6, TCP, UDP
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "PCAP ingestion requires the 'scapy' package. Install it with "
            "'pip install scapy'."
        ) from exc

    reader = _open_reader(fileobj)
    flows: Dict[Tuple[Any, ...], _Flow] = {}
    records: List[Dict[str, Any]] = []

    packet_count = 0
    ip_packet_count = 0
    skipped_non_ip = 0
    last_sweep = 0.0
    first_timestamp: Optional[float] = None
    last_timestamp: Optional[float] = None

    def finalise(key: Tuple[Any, ...]) -> None:
        flow = flows.pop(key, None)
        if flow is not None:
            records.append(flow.to_record())

    try:
        for packet in reader:
            packet_count += 1
            if packet_count > max_packets:
                raise IngestionLimitError(
                    f"The capture contains more than {max_packets:,} packets. "
                    "Split the capture into smaller time ranges before uploading."
                )

            if IP in packet:
                ip_layer = packet[IP]
                src_ip = str(ip_layer.src)
                dst_ip = str(ip_layer.dst)
                fallback_protocol = int(ip_layer.proto)
            elif IPv6 in packet:
                ip_layer = packet[IPv6]
                src_ip = str(ip_layer.src)
                dst_ip = str(ip_layer.dst)
                fallback_protocol = int(ip_layer.nh)
            else:
                skipped_non_ip += 1
                continue

            ts = float(packet.time)
            if first_timestamp is None:
                first_timestamp = ts
            last_timestamp = ts
            ip_packet_count += 1

            is_tcp = TCP in packet
            is_udp = UDP in packet

            if is_tcp:
                tcp = packet[TCP]
                protocol = 6
                src_port = int(tcp.sport)
                dst_port = int(tcp.dport)
                tcp_flags = int(tcp.flags)
                tcp_window: Optional[int] = int(tcp.window)
                payload_length = len(bytes(tcp.payload))
            elif is_udp:
                udp = packet[UDP]
                protocol = 17
                src_port = int(udp.sport)
                dst_port = int(udp.dport)
                tcp_flags = 0
                tcp_window = None
                payload_length = len(bytes(udp.payload))
            else:
                protocol = fallback_protocol
                src_port = 0
                dst_port = 0
                tcp_flags = 0
                tcp_window = None
                payload_length = 0

            length = min(max(float(len(ip_layer)), 0.0), PACKET_LENGTH_CAP)

            left = (src_ip, src_port)
            right = (dst_ip, dst_port)
            key = (
                protocol,
                left,
                right,
            ) if left <= right else (
                protocol,
                right,
                left,
            )

            flow = flows.get(key)
            if flow is not None and ts - flow.last_ts > IDLE_TIMEOUT_SECONDS:
                finalise(key)
                flow = None

            if flow is None:
                flow = _Flow(
                    first_ts=ts,
                    last_ts=ts,
                    initiator_ip=src_ip,
                    initiator_port=src_port,
                    responder_ip=dst_ip,
                    responder_port=dst_port,
                    dst_port=dst_port,
                    protocol=protocol,
                )
                flows[key] = flow

            forward = (
                src_ip == flow.initiator_ip and src_port == flow.initiator_port
            )

            flow.add(
                ts=ts,
                forward=forward,
                length=length,
                tcp_flags=tcp_flags,
                tcp_window=tcp_window,
                payload_length=payload_length,
                is_tcp=is_tcp,
            )

            if ts - last_sweep >= SWEEP_INTERVAL_SECONDS:
                expired = [
                    expired_key
                    for expired_key, candidate in flows.items()
                    if ts - candidate.last_ts > IDLE_TIMEOUT_SECONDS
                ]
                for expired_key in expired:
                    finalise(expired_key)
                last_sweep = ts
    finally:
        close = getattr(reader, "close", None)
        if close is not None:
            close()

    for key in list(flows):
        finalise(key)

    if not records:
        raise EmptyFileError(
            "No IP flows could be reconstructed from the capture. Supported "
            "packets are IPv4/IPv6 TCP, UDP and other IP protocols."
        )

    frame = pd.DataFrame.from_records(records)
    stats = {
        "packet_count": int(packet_count),
        "ip_packet_count": int(ip_packet_count),
        "skipped_non_ip": int(skipped_non_ip),
        "flow_count": int(len(records)),
        "first_timestamp": (
            pd.Timestamp(first_timestamp, unit="s", tz="UTC")
            .tz_convert(None)
            .isoformat(timespec="seconds")
            if first_timestamp is not None
            else None
        ),
        "last_timestamp": (
            pd.Timestamp(last_timestamp, unit="s", tz="UTC")
            .tz_convert(None)
            .isoformat(timespec="seconds")
            if last_timestamp is not None
            else None
        ),
    }

    return frame, stats
