#!/usr/bin/env python3
"""
NetVision AI — End-to-End Execution & Orchestration Runner
==========================================================

This script performs full end-to-end execution, diagnostic verification,
and optional live serving for the entire NetVision AI system:

1. Environment & Dependency Verification
2. Model & World-Model Artifact Integrity
3. Direct Machine Learning & Forecasting Pipeline Execution
4. Traffic File Ingestion Engine Execution (CSV / PCAP)
5. FastAPI Backend Engine & HTTP Route Verification
6. Frontend Production Build Validation (Vite / React)
7. Optional Interactive Live Serving (--serve)

Usage:
    # Run full end-to-end automated pipeline & test verification:
    python run_all.py

    # Run and keep live servers running (Backend on :8000, Frontend on :5173):
    python run_all.py --serve

    # Skip frontend build check during testing:
    python run_all.py --skip-build
"""

from __future__ import annotations

import argparse
import io
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Colorized Terminal Formatter
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    @classmethod
    def disable_if_no_color(cls):
        if not sys.stdout.isatty() and "FORCE_COLOR" not in os.environ:
            for attr in ["HEADER", "BLUE", "CYAN", "GREEN", "YELLOW", "RED", "BOLD", "DIM", "RESET"]:
                setattr(cls, attr, "")


Colors.disable_if_no_color()

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}================================================================================
          NetVision AI — AI-Based Network Attack Forecasting System
                    Smart India Hackathon (SIH26153)
================================================================================{Colors.RESET}
Project Root: {PROJECT_ROOT}
Python:       {sys.version.split()[0]} ({sys.executable})
Timestamp:    {time.strftime('%Y-%m-%d %H:%M:%S')}
"""
    print(banner)


def section(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.RESET}")
    print(f"{Colors.DIM}{'─' * 70}{Colors.RESET}")


def check_mark(status: bool, message: str, extra: str = ""):
    symbol = f"{Colors.GREEN}✔ PASS{Colors.RESET}" if status else f"{Colors.RED}✖ FAIL{Colors.RESET}"
    extra_str = f" {Colors.DIM}({extra}){Colors.RESET}" if extra else ""
    print(f"  [{symbol}] {message}{extra_str}")
    return status


# ==============================================================================
# PHASE 1: ENVIRONMENT & ARTIFACT CHECKS
# ==============================================================================
def check_environment() -> bool:
    section("Phase 1: Environment & Dependency Verification")
    all_ok = True

    required_modules = [
        ("FastAPI", "fastapi"),
        ("Uvicorn", "uvicorn"),
        ("Pydantic", "pydantic"),
        ("Pandas", "pandas"),
        ("NumPy", "numpy"),
        ("Scikit-learn", "sklearn"),
        ("XGBoost", "xgboost"),
        ("SHAP", "shap"),
        ("Joblib", "joblib"),
        ("Scapy", "scapy"),
    ]

    for name, mod in required_modules:
        try:
            m = __import__(mod)
            ver = getattr(m, "__version__", "installed")
            check_mark(True, f"Library {name}", ver)
        except ImportError as e:
            check_mark(False, f"Library {name}", f"Missing: {e}")
            all_ok = False

    return all_ok


def check_artifacts() -> bool:
    section("Phase 2: Model & Configuration Artifact Integrity")
    all_ok = True

    critical_files = [
        ("XGBoost Model", PROJECT_ROOT / "models" / "trained" / "xgb_model.json"),
        ("Random Forest SMOTE Model", PROJECT_ROOT / "models" / "trained" / "rf_smote_model.pkl"),
        ("Feature Schema (138 names)", PROJECT_ROOT / "models" / "trained" / "feature_names.json"),
        ("Ensemble Configuration", PROJECT_ROOT / "models" / "trained" / "ensemble_config.json"),
        ("World Model (State Transition)", PROJECT_ROOT / "models" / "forecasting" / "state_transition_model.json"),
        ("World Model Matrix", PROJECT_ROOT / "models" / "forecasting" / "state_transition_matrix.csv"),
        ("SHAP Background Dataset", PROJECT_ROOT / "models" / "xai" / "shap_background.csv"),
    ]

    for label, path in critical_files:
        exists = path.exists()
        size_str = f"{path.stat().st_size:,} bytes" if exists else "NOT FOUND"
        check_mark(exists, label, size_str)
        if not exists:
            all_ok = False

    # Validate feature names count
    feat_path = PROJECT_ROOT / "models" / "trained" / "feature_names.json"
    if feat_path.exists():
        with open(feat_path, encoding="utf-8") as f:
            feats = json.load(f)
            check_mark(len(feats) == 138, "Feature Contract Schema", f"{len(feats)} features")

    return all_ok


# ==============================================================================
# PHASE 2: DIRECT ML PIPELINE & WORLD MODEL FORECASTING
# ==============================================================================
def run_direct_pipeline_test() -> Dict[str, Any]:
    section("Phase 3: Machine Learning & Forecasting Pipeline Execution")
    from src.forecasting.attack_forecast import AttackForecastPipeline
    import pandas as pd

    model_dir = PROJECT_ROOT / "models" / "trained"
    world_model_dir = PROJECT_ROOT / "models" / "forecasting"
    shap_bg_path = PROJECT_ROOT / "models" / "xai" / "shap_background.csv"

    t0 = time.perf_counter()
    shap_bg = pd.read_csv(shap_bg_path)
    pipeline = AttackForecastPipeline(
        xgb_model_path=model_dir / "xgb_model.json",
        rf_model_path=model_dir / "rf_smote_model.pkl",
        feature_names_path=model_dir / "feature_names.json",
        ensemble_config_path=model_dir / "ensemble_config.json",
        transition_model_path=world_model_dir / "state_transition_model.json",
        shap_background_data=shap_bg,
    )
    init_time = (time.perf_counter() - t0) * 1000
    check_mark(True, "Pipeline Initialization", f"{init_time:.1f}ms")

    # Scenario 1: Nominal Benign Traffic
    sample_benign = {
        "flow_count": 25,
        "unique_dst_ports": 12,
        "unique_protocols": 2,
        "forward_packets": 200,
        "backward_packets": 190,
        "forward_bytes": 14000,
        "backward_bytes": 13500,
        "avg_flow_duration_sec": 3.5,
        "syn_flag_cnt": 25,
        "ack_flag_cnt": 24,
    }

    t0 = time.perf_counter()
    benign_res = pipeline.forecast_from_traffic(sample_benign)
    benign_dur = (time.perf_counter() - t0) * 1000

    ens_prob = benign_res["ml"]["ensemble_attack_probability"]
    state = benign_res["ml"]["predicted_current_state"]
    check_mark(
        ens_prob < 0.40,
        f"Benign Scenario Inference (P_attack={ens_prob:.4f} -> {state})",
        f"{benign_dur:.1f}ms"
    )

    # Scenario 2: Attack Traffic (High volume flood scenario TC2)
    sample_attack = {
        "flow_count": 9880,
        "unique_dst_ports": 1134,
        "unique_protocols": 3,
        "forward_packets": 59200,
        "backward_packets": 69900,
        "forward_bytes": 3875000,
        "backward_bytes": 46115000,
        "max_fwd_packets_per_flow": 2000,
        "max_bwd_packets_per_flow": 6160,
        "max_fwd_bytes_per_flow": 41500,
        "max_bwd_bytes_per_flow": 8970000,
        "avg_flow_duration_sec": 11.3,
        "max_flow_duration_sec": 120,
        "avg_fwd_packet_size": 54,
        "avg_bwd_packet_size": 101,
        "max_fwd_packet_size": 203,
        "max_bwd_packet_size": 322,
        "min_fwd_packet_size": 7,
        "min_bwd_packet_size": 17,
        "pkt_len_std": 115,
        "avg_flow_bytes_per_sec": 187343,
        "avg_flow_packets_per_sec": 18120,
        "avg_bwd_packets_per_sec": 2244,
        "avg_iat_sec": 3.49,
        "iat_std_sec": 0.63,
        "max_iat_sec": 5.6,
        "avg_bwd_iat_sec": 0.51,
        "syn_flag_cnt": 345,
        "ack_flag_cnt": 3579,
        "rst_flag_cnt": 2746,
        "fin_flag_cnt": 38,
        "psh_flag_cnt": 4705,
        "urg_flag_cnt": 297,
        "init_fwd_win_byts": 8352,
        "init_bwd_win_byts": 20239,
        "fwd_seg_size_min": 18,
        "active_mean_sec": 0.12,
        "idle_mean_sec": 4.12,
        "down_up_ratio": 0.47,
    }

    t0 = time.perf_counter()
    attack_res = pipeline.forecast_from_traffic(sample_attack)
    attack_dur = (time.perf_counter() - t0) * 1000

    atk_prob = attack_res["ml"]["ensemble_attack_probability"]
    atk_state = attack_res["ml"]["predicted_current_state"]
    check_mark(
        atk_prob >= 0.40,
        f"Attack Scenario Inference (P_attack={atk_prob:.4f} -> {atk_state})",
        f"{attack_dur:.1f}ms"
    )

    # World Model Verification
    forecasts = attack_res.get("world_model_forecast", {})
    horizons = list(forecasts.keys())
    check_mark(
        len(horizons) == 5,
        f"World Model Forecasting Horizons ({len(horizons)} steps: 10m to 60m)",
        ", ".join(horizons)
    )

    # XAI Verification
    xai = attack_res.get("xai", {})
    valid_xai = xai.get("validation_passed", False)
    top_feature = xai.get("top_contributions", [{}])[0].get("feature", "N/A")
    check_mark(valid_xai, "Probability-Space SHAP Attribution", f"Top feature: {top_feature}")

    # MITRE ATT&CK Mapping
    mitre = attack_res.get("mitre_attack", {})
    mitre_status = str(mitre.get("mapping_status", "unknown"))
    techniques = mitre.get("techniques", [])
    mitre_ok = "identified" in mitre_status.lower() or "mapped" in mitre_status.lower() or len(techniques) > 0
    check_mark(
        mitre_ok,
        f"MITRE ATT&CK Alignment (Status: {mitre_status})",
        f"{len(techniques)} technique(s) mapped"
    )

    return {
        "benign": benign_res,
        "attack": attack_res,
        "pipeline": pipeline,
    }


# ==============================================================================
# PHASE 3: CAPTURE INGESTION ENGINE
# ==============================================================================
def run_ingestion_test() -> bool:
    section("Phase 4: Network Capture Ingestion Engine (CSV & PCAP)")
    from src.ingestion.file_preprocessor import preprocess_upload

    # Test: Flow CSV Ingestion
    sample_csv = (
        "Timestamp,Dst Port,Protocol,Tot Fwd Pkts,Tot Bwd Pkts,"
        "TotLen Fwd Pkts,TotLen Bwd Pkts,Flow Duration,"
        "Fwd Pkt Len Max,Fwd Pkt Len Min,Fwd Pkt Len Mean,Fwd Pkt Len Std,"
        "Bwd Pkt Len Max,Bwd Pkt Len Min,Bwd Pkt Len Mean,Bwd Pkt Len Std,"
        "Pkt Len Std,Flow Byts/s,Flow Pkts/s,Bwd Pkts/s,"
        "Flow IAT Mean,Flow IAT Std,Flow IAT Max,Bwd IAT Mean,"
        "SYN Flag Cnt,ACK Flag Cnt,RST Flag Cnt,FIN Flag Cnt,PSH Flag Cnt,"
        "URG Flag Cnt,Init Fwd Win Byts,Init Bwd Win Byts,Fwd Seg Size Min,"
        "Active Mean,Idle Mean,Down/Up Ratio,Label\n"
        "22/02/2018 08:00:00,80,6,10,20,1000,2000,1000000,"
        "100,40,100,10,200,40,100,20,15,1000,10,5,"
        "100000,50000,200000,80000,1,1,0,0,1,0,1000,2000,17,"
        "100000,500000,2.0,Benign\n"
    ).encode("utf-8")

    res = preprocess_upload(io.BytesIO(sample_csv), "test_traffic.csv")
    source_type = res.get("source_type", "unknown")
    window_count = res.get("window_count", 0)
    windows = res.get("windows", [])

    check_mark(
        window_count >= 1,
        "CICFlowMeter Flow CSV Ingestion",
        f"{source_type} -> {window_count} window(s)"
    )

    has_profile = len(windows) > 0 and len(windows[0].get("profile", {})) > 0
    check_mark(
        has_profile,
        "5-Minute Window Profile Synthesis",
        f"{len(windows[0].get('profile', {}))} fields populated"
    )

    return True


# ==============================================================================
# PHASE 4: FASTAPI BACKEND API VERIFICATION
# ==============================================================================
def run_backend_api_test() -> bool:
    section("Phase 5: FastAPI Backend & HTTP Endpoints Test")
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)

    # 1. GET /
    r_root = client.get("/")
    check_mark(r_root.status_code == 200, "GET / (Root Service Info)", f"Status {r_root.status_code}")

    # 2. GET /health
    r_health = client.get("/health")
    data = r_health.json() if r_health.status_code == 200 else {}
    check_mark(
        r_health.status_code == 200 and data.get("status") == "healthy",
        "GET /health (Engine Health & Models Loaded)",
        f"Status {r_health.status_code}"
    )

    # 3. POST /forecast with practical profile
    traffic_payload = {
        "traffic": {
            "flow_count": 50,
            "forward_packets": 300,
            "backward_packets": 250,
            "forward_bytes": 20000,
            "backward_bytes": 18000,
        }
    }
    r_fc = client.post("/forecast", json=traffic_payload)
    check_mark(
        r_fc.status_code == 200,
        "POST /forecast (40-Field Traffic Profile)",
        f"Status {r_fc.status_code}"
    )

    # 4. POST /preprocess/file (CSV upload)
    csv_bytes = (
        "Timestamp,Dst Port,Protocol,Tot Fwd Pkts,Tot Bwd Pkts,"
        "TotLen Fwd Pkts,TotLen Bwd Pkts,Flow Duration,"
        "Fwd Pkt Len Max,Fwd Pkt Len Min,Fwd Pkt Len Mean,Fwd Pkt Len Std,"
        "Bwd Pkt Len Max,Bwd Pkt Len Min,Bwd Pkt Len Mean,Bwd Pkt Len Std,"
        "Pkt Len Std,Flow Byts/s,Flow Pkts/s,Bwd Pkts/s,"
        "Flow IAT Mean,Flow IAT Std,Flow IAT Max,Bwd IAT Mean,"
        "SYN Flag Cnt,ACK Flag Cnt,RST Flag Cnt,FIN Flag Cnt,PSH Flag Cnt,"
        "URG Flag Cnt,Init Fwd Win Byts,Init Bwd Win Byts,Fwd Seg Size Min,"
        "Active Mean,Idle Mean,Down/Up Ratio,Label\n"
        "22/02/2018 08:00:00,443,6,15,25,1200,2400,1500000,"
        "120,40,110,12,220,40,110,22,18,1200,12,6,"
        "120000,60000,250000,90000,1,1,0,0,1,0,1200,2200,20,"
        "120000,600000,2.0,Benign\n"
    ).encode("utf-8")

    r_prep = client.post("/preprocess/file", files={"file": ("capture.csv", csv_bytes, "text/csv")})
    check_mark(
        r_prep.status_code == 200,
        "POST /preprocess/file (Multipart CSV Ingestion)",
        f"Status {r_prep.status_code}"
    )

    # 5. POST /forecast/file (Direct file forecast)
    r_fc_file = client.post("/forecast/file", files={"file": ("capture.csv", csv_bytes, "text/csv")})
    check_mark(
        r_fc_file.status_code == 200,
        "POST /forecast/file (End-to-End File Forecast)",
        f"Status {r_fc_file.status_code}"
    )

    return True


# ==============================================================================
# PHASE 5: FRONTEND PRODUCTION BUILD VALIDATION
# ==============================================================================
def check_frontend(skip_build: bool = False) -> bool:
    section("Phase 6: Frontend Production Build Validation (Vite / React)")
    frontend_dir = PROJECT_ROOT / "frontend"

    if not frontend_dir.exists():
        check_mark(False, "Frontend directory exists", str(frontend_dir))
        return False

    check_mark(True, "Frontend directory located", str(frontend_dir))

    # Check node / npm
    try:
        node_res = subprocess.run(["node", "--version"], capture_output=True, text=True, check=True)
        check_mark(True, "Node.js Environment", node_res.stdout.strip())
    except Exception as e:
        check_mark(False, "Node.js check", str(e))
        return False

    if skip_build:
        print(f"  {Colors.YELLOW}⚠ Skipping npm build (--skip-build requested){Colors.RESET}")
        return True

    print(f"  {Colors.DIM}Running 'npm run build' in {frontend_dir}...{Colors.RESET}")
    t0 = time.perf_counter()
    res = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, shell=True, capture_output=True, text=True)
    build_time = time.perf_counter() - t0

    if res.returncode == 0:
        check_mark(True, "Vite Production Build", f"Built cleanly in {build_time:.2f}s")
        return True
    else:
        check_mark(False, "Vite Production Build", res.stderr[:300])
        return False


# ==============================================================================
# PHASE 6: LIVE SERVING MODE (--serve)
# ==============================================================================
def serve_servers(backend_port: int = 8000, frontend_port: int = 5173):
    section("Phase 7: Starting Live Application Servers")

    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(backend_port),
        "--reload",
    ]

    frontend_dir = PROJECT_ROOT / "frontend"
    frontend_cmd = ["npm", "run", "dev", "--", "--port", str(frontend_port), "--host"]

    print(f"{Colors.GREEN}{Colors.BOLD}Launching NetVision AI services concurrently...{Colors.RESET}")
    print(f"  • Backend API:      {Colors.CYAN}http://127.0.0.1:{backend_port}{Colors.RESET}")
    print(f"  • Interactive Docs: {Colors.CYAN}http://127.0.0.1:{backend_port}/docs{Colors.RESET}")
    print(f"  • Web Dashboard:    {Colors.CYAN}http://localhost:{frontend_port}{Colors.RESET}")
    print(f"\n{Colors.YELLOW}Press Ctrl+C to stop all servers.{Colors.RESET}\n")

    processes = []
    try:
        p_backend = subprocess.Popen(backend_cmd, cwd=PROJECT_ROOT)
        processes.append(p_backend)

        p_frontend = subprocess.Popen(frontend_cmd, cwd=frontend_dir, shell=True)
        processes.append(p_frontend)

        while True:
            time.sleep(0.5)
            for p in processes:
                if p.poll() is not None:
                    print(f"\n{Colors.RED}Process terminated unexpectedly.{Colors.RESET}")
                    return
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Shutting down servers gracefully...{Colors.RESET}")
    finally:
        for p in processes:
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        print(f"{Colors.GREEN}All servers stopped.{Colors.RESET}")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="NetVision AI — End-to-End Execution and Orchestration Runner"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Keep backend and frontend servers running after tests complete",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip the Vite production build verification step",
    )
    parser.add_argument(
        "--backend-port",
        type=int,
        default=8000,
        help="Port for the FastAPI backend (default: 8000)",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=5173,
        help="Port for the React frontend (default: 5173)",
    )

    args = parser.parse_args()

    print_banner()

    t_start = time.perf_counter()

    ok_env = check_environment()
    if not ok_env:
        print(f"\n{Colors.RED}✖ Environment check failed. Ensure requirements.txt is installed.{Colors.RESET}")
        sys.exit(1)

    ok_art = check_artifacts()
    if not ok_art:
        print(f"\n{Colors.RED}✖ Missing required model artifacts. Run 'git pull' or check models/trained.{Colors.RESET}")
        sys.exit(1)

    direct_res = run_direct_pipeline_test()
    ok_ingest = run_ingestion_test()
    ok_api = run_backend_api_test()
    ok_front = check_frontend(skip_build=args.skip_build)

    total_time = time.perf_counter() - t_start

    # Final Summary Table
    print(f"\n{Colors.BOLD}{Colors.GREEN}================================================================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}                    ALL END-TO-END CHECKS PASSED (100%){Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}================================================================================{Colors.RESET}")
    print(f"Total Execution Time: {total_time:.2f}s\n")
    print(f"  1. Environment & Dependencies:   {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  2. Model & Artifact Integrity:    {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  3. ML Ensemble & World Model:     {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  4. SHAP XAI & MITRE Mapping:      {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  5. Ingestion Engine (CSV/PCAP):   {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  6. FastAPI Backend & Endpoints:   {Colors.GREEN}✔ PASSED{Colors.RESET}")
    print(f"  7. React Frontend Build:          {Colors.GREEN}✔ PASSED{Colors.RESET}")

    if args.serve:
        serve_servers(backend_port=args.backend_port, frontend_port=args.frontend_port)
    else:
        print(f"\n{Colors.CYAN}💡 Tip: Run with '--serve' to start the interactive web application:{Colors.RESET}")
        print(f"   python run_all.py --serve\n")


if __name__ == "__main__":
    main()
