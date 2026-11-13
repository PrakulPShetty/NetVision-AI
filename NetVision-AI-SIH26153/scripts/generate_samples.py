import os
import sys
from pathlib import Path
from scapy.all import Ether, IP, TCP, Raw, wrpcap

# Ensure project root is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import app

def main():
    target_dirs = [
        PROJECT_ROOT / "data" / "samples",
        PROJECT_ROOT.parent / "data" / "samples",
    ]
    for d in target_dirs:
        d.mkdir(parents=True, exist_ok=True)

    # 1. CICFlowMeter Flow Header
    flow_header = (
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

    # 2. Benign Flow Record (1 record)
    benign_csv_row = (
        "22/02/2018 08:00:00,80,6,10,20,1000,2000,1000000,"
        "100,40,100,10,200,40,100,20,15,3000,30,20,"
        "100000,50000,200000,80000,1,1,0,0,1,0,1000,2000,17,"
        "100000,500000,2.0,Benign"
    )
    benign_csv_content = f"{flow_header}\n{benign_csv_row}\n"

    # 3. Attack Flow Record (1 record)
    attack_csv_row = (
        "22/02/2018 08:05:00,80,6,150,0,15000,0,5000000,"
        "100,100,100,0,0,0,0,0,0,3000,30,0,"
        "33333,5000,40000,0,1,0,0,0,0,0,29200,-1,32,"
        "0,0,0,DDoS attacks-LOIC-HTTP"
    )
    attack_csv_content = f"{flow_header}\n{attack_csv_row}\n"

    # 4. Benign PCAP Packet (1 record)
    pkt_benign = (
        Ether()
        / IP(src="192.168.1.10", dst="192.168.1.1")
        / TCP(sport=12345, dport=80, flags="S")
    )

    # 5. Attack PCAP Packet (1 record)
    pkt_attack = (
        Ether()
        / IP(src="10.0.0.99", dst="10.0.0.1")
        / TCP(sport=43210, dport=80, flags="A", window=64240)
        / Raw(b"GET / HTTP/1.1\r\n\r\n")
    )

    # Write files
    for d in target_dirs:
        (d / "benign_sample.csv").write_text(benign_csv_content, encoding="utf-8")
        (d / "attack_sample.csv").write_text(attack_csv_content, encoding="utf-8")
        wrpcap(str(d / "benign_sample.pcap"), [pkt_benign])
        wrpcap(str(d / "attack_sample.pcap"), [pkt_attack])

    print("Successfully generated all 4 files.")

    # Validate with FastAPI client
    client = TestClient(app)
    files_to_test = [
        ("benign_sample.csv", "BENIGN"),
        ("attack_sample.csv", "ATTACK"),
        ("benign_sample.pcap", "BENIGN"),
        ("attack_sample.pcap", "ATTACK"),
    ]

    primary_dir = target_dirs[0]
    all_passed = True

    print("\n--- Validation Results ---")
    for filename, expected_state in files_to_test:
        filepath = primary_dir / filename
        content = filepath.read_bytes()

        # 1. Preprocess
        res_prep = client.post(
            "/preprocess/file",
            files={"file": (filename, content, "application/octet-stream")},
        )
        assert res_prep.status_code == 200, f"Preprocessing failed: {res_prep.text}"
        prep_data = res_prep.json()
        rec_count = prep_data.get("row_count") or prep_data.get("packet_count")

        # 2. Forecast
        res_fc = client.post(
            "/forecast/file",
            files={"file": (filename, content, "application/octet-stream")},
            data={"window_index": 0},
        )
        assert res_fc.status_code == 200, f"Forecasting failed: {res_fc.text}"
        fc_data = res_fc.json()
        pred_state = fc_data["forecast"]["ml"]["current_state_label"]
        prob = fc_data["forecast"]["ml"]["ensemble_attack_probability"]

        is_match = (pred_state == expected_state)
        status_str = "PASS" if is_match else "FAIL"
        if not is_match:
            all_passed = False

        print(
            f"File: {filename:<18} | Records: {rec_count} | Expected: {expected_state:<6} "
            f"| Predicted: {pred_state:<6} | P(Attack): {prob:.4f} | Status: {status_str}"
        )

    assert all_passed, "One or more sample validations failed!"
    print("\nALL 4 SAMPLE FILES VERIFIED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
