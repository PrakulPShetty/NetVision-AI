"""Tests for raw CICFlowMeter CSV, PCAP/PCAPNG and profile ingestion.

These tests exercise the ingestion layer only. They do not require the
trained model artifacts, so they can run in isolation from the forecasting
pipeline.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest

from src.ingestion import (
    IngestionSettings,
    preprocess_upload,
    select_window,
    window_forecast_payload,
)
from src.ingestion.constants import MODEL_FEATURE_COUNT, PROFILE_FIELDS
from src.ingestion.errors import (
    EmptyFileError,
    FileTooLargeError,
    IngestionLimitError,
    MalformedFileError,
    UnsupportedFileTypeError,
)

FLOW_HEADER = (
    "Timestamp,Dst Port,Protocol,Tot Fwd Pkts,Tot Bwd Pkts,"
    "TotLen Fwd Pkts,TotLen Bwd Pkts,Flow Duration,"
    "Fwd Pkt Len Max,Fwd Pkt Len Min,Fwd Pkt Len Mean,Fwd Pkt Len Std,"
    "Bwd Pkt Len Max,Bwd Pkt Len Min,Bwd Pkt Len Mean,Bwd Pkt Len Std,"
    "Pkt Len Std,Flow Byts/s,Flow Pkts/s,Bwd Pkts/s,"
    "Flow IAT Mean,Flow IAT Std,Flow IAT Max,Bwd IAT Mean,"
    "SYN Flag Cnt,ACK Flag Cnt,RST Flag Cnt,FIN Flag Cnt,PSH Flag Cnt,"
    "URG Flag Cnt,Init Fwd Win Byts,Init Bwd Win Byts,Fwd Seg Size Min,"
    "Active Mean,Idle Mean,Down/Up Ratio,Label"
)

FLOW_ROWS = [
    # Window 08:00-08:05, flow 1
    "22/02/2018 08:00:00,80,6,10,20,1000,2000,1000000,"
    "100,40,100,10,200,40,100,20,15,1000,10,5,"
    "100000,50000,200000,80000,1,1,0,0,1,0,1000,2000,17,"
    "100000,500000,2.0,Benign",
    # Window 08:00-08:05, flow 2
    "22/02/2018 08:03:00,443,6,5,5,500,500,2000000,"
    "80,40,80,5,90,40,90,10,8,500,5,2,"
    "200000,20000,300000,100000,0,1,0,0,0,0,500,1000,10,"
    "200000,1000000,1.0,Benign",
    # Window 08:05-08:10
    "22/02/2018 08:06:00,22,6,4,4,400,400,3000000,"
    "70,40,70,0,80,40,80,0,0,400,4,2,"
    "300000,0,300000,150000,1,0,0,0,0,0,300,600,8,"
    "300000,1500000,1.0,Attack",
]


def _csv(rows=FLOW_ROWS, header=FLOW_HEADER) -> bytes:
    return (header + "\n" + "\n".join(rows) + "\n").encode("utf-8")


def test_cicflowmeter_csv_uses_phase4_aggregation():
    result = preprocess_upload(io.BytesIO(_csv()), "flows.csv")

    assert result["source_type"] == "cicflowmeter_csv"
    assert result["window_count"] == 2
    assert result["row_count"] == 3
    assert result["label_summary"] == {"Benign": 2, "Attack": 1}

    first = result["windows"][0]
    profile = first["profile"]

    assert first["window_start"] == "2018-02-22T08:00:00"
    assert first["window_end"] == "2018-02-22T08:05:00"
    assert first["flow_count"] == 2
    assert first["label_counts"] == {"Benign": 2}
    assert first["attack_flow_count"] == 0
    assert first["benign_flow_count"] == 2

    assert set(profile) == set(PROFILE_FIELDS)
    assert profile["flow_count"] == 2
    assert profile["unique_dst_ports"] == 2
    assert profile["unique_protocols"] == 1
    assert profile["forward_packets"] == 15
    assert profile["backward_packets"] == 25
    assert profile["forward_bytes"] == 1500
    assert profile["backward_bytes"] == 2500
    assert profile["max_fwd_packets_per_flow"] == 10
    assert profile["max_bwd_bytes_per_flow"] == 2000

    assert profile["avg_flow_duration_sec"] == pytest.approx(1.5)
    assert profile["max_flow_duration_sec"] == pytest.approx(2.0)
    assert profile["min_flow_duration_sec"] == pytest.approx(1.0)

    assert profile["avg_fwd_packet_size"] == pytest.approx(90.0)
    assert profile["avg_bwd_packet_size"] == pytest.approx(95.0)
    assert profile["max_fwd_packet_size"] == pytest.approx(90.0)
    assert profile["max_bwd_packet_size"] == pytest.approx(145.0)

    assert profile["avg_iat_sec"] == pytest.approx(0.15)
    assert profile["iat_std_sec"] == pytest.approx(0.035)
    assert profile["max_iat_sec"] == pytest.approx(0.25)
    assert profile["avg_bwd_iat_sec"] == pytest.approx(0.09)

    assert profile["syn_flag_cnt"] == 1
    assert profile["ack_flag_cnt"] == 2
    assert profile["psh_flag_cnt"] == 1

    assert profile["init_fwd_win_byts"] == pytest.approx(750.0)
    assert profile["init_bwd_win_byts"] == pytest.approx(1500.0)
    assert profile["fwd_seg_size_min"] == pytest.approx(13.5)

    assert profile["active_mean_sec"] == pytest.approx(0.15)
    assert profile["idle_mean_sec"] == pytest.approx(0.75)
    assert profile["down_up_ratio"] == pytest.approx(1.5)

    second = result["windows"][1]
    assert second["window_start"] == "2018-02-22T08:05:00"
    assert second["flow_count"] == 1
    assert second["attack_flow_count"] == 1
    assert second["benign_flow_count"] == 0


def test_header_aliases_and_month_first_timestamps():
    header = (
        FLOW_HEADER.replace("Dst Port", "Destination Port")
        .replace("Tot Fwd Pkts", "Total Fwd Packets")
        .replace("Tot Bwd Pkts", "Total Backward Packets")
        .replace("TotLen Fwd Pkts", "Total Length of Fwd Packets")
        .replace("TotLen Bwd Pkts", "Total Length of Bwd Packets")
        .replace("Fwd Pkt Len Max", "Fwd Packet Length Max")
        .replace("Bwd Pkt Len Max", "Bwd Packet Length Max")
        .replace("Pkt Len Std", "Packet Length Std")
        .replace("Flow Byts/s", "Flow Bytes/s")
        .replace("Flow Pkts/s", "Flow Packets/s")
        .replace("Bwd Pkts/s", "Bwd Packets/s")
        .replace("Init Fwd Win Byts", "Init_Win_bytes_forward")
        .replace("Init Bwd Win Byts", "Init_Win_bytes_backward")
        .replace("Fwd Seg Size Min", "min_seg_size_forward")
        .replace("SYN Flag Cnt", "SYN Flag Count")
        .replace("Label", "Class")
    )
    row = (
        "02/22/2018 08:00:00,80,6,10,20,1000,2000,1000000,"
        "100,40,100,10,200,40,100,20,15,1000,10,5,"
        "100000,50000,200000,80000,1,1,0,0,1,0,1000,2000,17,"
        "100000,500000,2.0,Benign"
    )

    result = preprocess_upload(io.BytesIO(_csv([row], header)), "aliases.csv")

    assert result["windows"][0]["window_start"] == "2018-02-22T08:00:00"
    assert result["windows"][0]["label_counts"] == {"Benign": 1}
    assert result["windows"][0]["profile"]["init_fwd_win_byts"] == 1000


def test_profile_csv_ingestion():
    header = ",".join(PROFILE_FIELDS)
    values = []
    for field in PROFILE_FIELDS:
        if field == "flow_count":
            values.append("250")
        elif field == "unique_dst_ports":
            values.append("40")
        elif field == "unique_protocols":
            values.append("3")
        else:
            values.append("1.5")

    csv = (header + "\n" + ",".join(values) + "\n").encode("utf-8")
    result = preprocess_upload(io.BytesIO(csv), "profile.csv")

    assert result["source_type"] == "profile_csv"
    assert result["window_count"] == 1
    assert result["has_profiles"] is True
    assert result["has_features"] is False
    assert result["windows"][0]["flow_count"] == 250
    assert result["windows"][0]["profile"]["down_up_ratio"] == 1.5


def test_feature_csv_ingestion():
    feature_names = [
        "flow_count",
        "total_flow_count",
        "unique_dst_ports",
        "unique_protocols",
    ] + [f"Feature {index}_mean" for index in range(134)]
    assert len(feature_names) == MODEL_FEATURE_COUNT

    row = ["120", "120", "12", "2"] + ["0.25"] * 134
    csv = (
        "window_start,"
        + ",".join(feature_names)
        + "\n2018-02-22T08:00:00,"
        + ",".join(row)
        + "\n"
    ).encode("utf-8")

    result = preprocess_upload(io.BytesIO(csv), "features.csv")

    assert result["source_type"] == "feature_csv"
    assert result["has_features"] is True
    assert result["has_profiles"] is False
    assert len(result["windows"][0]["features"]) == MODEL_FEATURE_COUNT
    assert result["windows"][0]["features"]["flow_count"] == 120


def test_without_timestamp_single_window():
    header = FLOW_HEADER.replace("Timestamp,", "")
    rows = [row.split(",", 1)[1] for row in FLOW_ROWS]
    result = preprocess_upload(io.BytesIO(_csv(rows, header)), "no_time.csv")

    assert result["window_count"] == 1
    assert result["windows"][0]["window_start"] is None
    assert result["windows"][0]["flow_count"] == 3
    assert any("one 5-minute" in warning for warning in result["warnings"])


def test_upload_limits():
    body = b"a,b\n1,2\n"

    with pytest.raises(FileTooLargeError):
        preprocess_upload(
            io.BytesIO(body),
            "x.csv",
            settings=IngestionSettings(max_upload_bytes=3),
        )

    with pytest.raises(IngestionLimitError):
        preprocess_upload(
            io.BytesIO(_csv()),
            "flows.csv",
            settings=IngestionSettings(max_csv_rows=2),
        )

    with pytest.raises(IngestionLimitError):
        preprocess_upload(
            io.BytesIO(_csv()),
            "flows.csv",
            settings=IngestionSettings(max_windows=1),
        )


def test_invalid_uploads():
    with pytest.raises(EmptyFileError):
        preprocess_upload(io.BytesIO(b""), "empty.csv")

    with pytest.raises(UnsupportedFileTypeError):
        preprocess_upload(io.BytesIO(b"\x00\x01\x02\x03"), "binary.bin")

    with pytest.raises(UnsupportedFileTypeError):
        preprocess_upload(io.BytesIO(b"a,b\n1,2\n"), "unknown.csv")

    with pytest.raises(MalformedFileError):
        preprocess_upload(
            io.BytesIO(b"Tot Fwd Pkts,Flow Duration\n1,2\n"),
            "missing.csv",
        )


def test_window_selection_payload():
    result = preprocess_upload(io.BytesIO(_csv()), "flows.csv")

    window = select_window(result, 0)
    payload = window_forecast_payload(window)
    assert payload["mode"] == "profile"
    assert set(payload["profile"]) == set(PROFILE_FIELDS)

    with pytest.raises(Exception):
        select_window(result, 99)


# ------------------------------------------------------------------
# PCAP / PCAPNG
# ------------------------------------------------------------------


def _write_pcap(packets, tmp_path, suffix=".pcap"):
    from scapy.all import wrpcap

    path = tmp_path / f"capture{suffix}"
    wrpcap(str(path), packets)
    return path.read_bytes()


def _write_pcapng(packets, tmp_path):
    from scapy.utils import PcapNgWriter

    path = tmp_path / "capture.pcapng"
    writer = PcapNgWriter(str(path))
    for packet in packets:
        writer.write(packet)
    writer.close()
    return path.read_bytes()


def _packets():
    from scapy.all import Ether, IP, Raw, TCP

    base = datetime(2018, 2, 22, 8, 0, tzinfo=timezone.utc).timestamp()

    def tcp(src, dst, sport, dport, flags, offset, payload=b"", window=64240):
        packet = (
            Ether()
            / IP(src=src, dst=dst)
            / TCP(sport=sport, dport=dport, flags=flags, window=window)
        )
        if payload:
            packet = packet / Raw(payload)
        packet.time = base + offset
        return packet

    return [
        # 08:00 window
        tcp("10.0.0.1", "10.0.0.2", 12345, 80, "S", 0.0),
        tcp("10.0.0.2", "10.0.0.1", 80, 12345, "SA", 0.1),
        tcp("10.0.0.1", "10.0.0.2", 12345, 80, "A", 0.2),
        tcp("10.0.0.1", "10.0.0.2", 12345, 80, "PA", 1.0, b"x" * 100),
        tcp("10.0.0.2", "10.0.0.1", 80, 12345, "PA", 1.1, b"y" * 200),
        tcp("10.0.0.1", "10.0.0.2", 12345, 80, "FA", 1.2),
        # 08:06 window
        tcp("10.0.0.5", "10.0.0.6", 33333, 443, "S", 360.0),
        tcp("10.0.0.6", "10.0.0.5", 443, 33333, "SA", 360.1),
    ]


def test_pcap_flow_reconstruction(tmp_path):
    packets = _packets()
    data = _write_pcap(packets, tmp_path)

    result = preprocess_upload(io.BytesIO(data), "capture.pcap")

    assert result["source_type"] == "pcap"
    assert result["packet_count"] == len(packets)
    assert result["window_count"] == 2

    first = result["windows"][0]
    assert first["window_start"] == "2018-02-22T08:00:00"
    assert first["flow_count"] == 1

    profile = first["profile"]
    assert profile["forward_packets"] == 4  # SYN, ACK, data, FIN
    assert profile["backward_packets"] == 2  # SYN-ACK, data
    assert profile["syn_flag_cnt"] == 1
    assert profile["ack_flag_cnt"] == 1
    assert profile["init_fwd_win_byts"] == 64240
    assert profile["init_bwd_win_byts"] == 64240
    assert profile["fwd_seg_size_min"] == 100
    assert profile["down_up_ratio"] == pytest.approx(280 / 260)

    second = result["windows"][1]
    assert second["window_start"] == "2018-02-22T08:05:00"
    assert second["flow_count"] == 1


def test_pcapng_flow_reconstruction(tmp_path):
    packets = _packets()
    data = _write_pcapng(packets, tmp_path)

    result = preprocess_upload(io.BytesIO(data), "capture.pcapng")

    assert result["source_type"] == "pcapng"
    assert result["packet_count"] == len(packets)
    assert result["window_count"] == 2
    assert result["windows"][0]["window_start"] == "2018-02-22T08:00:00"


def test_pcap_packet_limit(tmp_path):
    data = _write_pcap(_packets(), tmp_path)

    with pytest.raises(IngestionLimitError):
        preprocess_upload(
            io.BytesIO(data),
            "capture.pcap",
            settings=IngestionSettings(max_pcap_packets=2),
        )


def test_pcap_skips_non_ip_packets(tmp_path):
    from scapy.all import Ether, IP, TCP

    base = datetime(2018, 2, 22, 8, 0, tzinfo=timezone.utc).timestamp()
    packets = [
        Ether() / b"\x00\x01\x02",  # non-IP frame
        Ether() / IP(src="10.0.0.1", dst="10.0.0.2") / TCP(sport=1234, dport=80, flags="S"),
    ]
    packets[0].time = base
    packets[1].time = base + 0.1

    data = _write_pcap(packets, tmp_path)
    result = preprocess_upload(io.BytesIO(data), "mixed.pcap")

    assert result["packet_count"] == 2
    assert result["skipped_non_ip_packet_count"] == 1
    assert result["window_count"] == 1
