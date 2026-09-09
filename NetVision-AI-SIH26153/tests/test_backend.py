"""
NetVision AI — Backend FastAPI Integration Test
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app


def test_backend():
    print("=" * 70)
    print("FASTAPI BACKEND INTEGRATION TEST")
    print("=" * 70)

    client = TestClient(app)

    # 1. Test GET /
    print("\nTesting GET / ...")
    res_root = client.get("/")
    assert res_root.status_code == 200
    root_json = res_root.json()
    assert root_json["project"] == "NetVision AI"
    assert root_json["status"] == "running"
    print("GET / : PASS", root_json)

    # 2. Test GET /health
    print("\nTesting GET /health ...")
    res_health = client.get("/health")
    assert res_health.status_code == 200
    health_json = res_health.json()
    assert health_json["status"] == "healthy"
    assert health_json["ml_model"] == "loaded"
    assert health_json["world_model"] == "loaded"
    assert health_json["xai"] == "loaded"
    assert health_json["mitre_attack"] == "loaded"
    print("GET /health : PASS", health_json)

    # 3. Test POST /forecast with practical traffic input
    print("\nTesting POST /forecast with practical traffic input ...")
    practical_traffic = {
        "flow_count": 500,
        "unique_dst_ports": 50,
        "unique_protocols": 2,
        "forward_packets": 2500,
        "backward_packets": 1800,
        "forward_bytes": 250000,
        "backward_bytes": 180000,
        "flow_duration": 300000,
        "syn_flag_cnt": 150,
        "ack_flag_cnt": 2000,
        "rst_flag_cnt": 5,
        "fin_flag_cnt": 20,
    }

    res_forecast = client.post("/forecast", json=practical_traffic)
    assert res_forecast.status_code == 200, f"Error: {res_forecast.text}"
    forecast_json = res_forecast.json()

    # Verify sections
    assert "ml" in forecast_json or "ml_forecast" in forecast_json
    assert "world_model" in forecast_json or "world_model_forecast" in forecast_json
    assert "xai" in forecast_json
    assert "mitre_attack" in forecast_json

    ml_sec = forecast_json.get("ml") or forecast_json.get("ml_forecast")
    print("ML Probability         :", ml_sec["ensemble_attack_probability"])
    print("Current State          :", ml_sec.get("current_state_label") or ml_sec.get("predicted_current_state"))

    world_sec = forecast_json.get("world_model")
    if world_sec and "forecasts" in world_sec:
        for item in world_sec["forecasts"]:
            print(f"World Model {item['horizon_minutes']} min forecast:", item["future_attack_probability"])

    print("POST /forecast (Practical Input) : PASS")

    # 4. Test POST /forecast with 138-feature zero vector
    print("\nTesting POST /forecast with 138 zero features ...")
    feature_names = app.state.pipeline.feature_names if hasattr(app.state, "pipeline") else None
    if not feature_names:
        from src.forecasting.attack_forecast import AttackForecastPipeline
        # get feature names from loaded pipeline
        from backend.app.main import pipeline as main_pipeline
        feature_names = main_pipeline.feature_names

    zero_features = {f: 0.0 for f in feature_names}
    res_zero = client.post("/forecast", json={"features": zero_features})
    assert res_zero.status_code == 200, f"Error: {res_zero.text}"
    zero_json = res_zero.json()

    ml_zero = zero_json.get("ml") or zero_json.get("ml_forecast")
    assert abs(ml_zero["xgb_attack_probability"] - 0.126096) < 1e-4
    assert abs(ml_zero["rf_attack_probability"] - 0.373333) < 1e-4
    assert abs(ml_zero["ensemble_attack_probability"] - 0.249715) < 1e-4
    print("POST /forecast (138 Zero Features) : PASS")

    # 5. Test input validation (reject invalid input keys like future_attack_state)
    print("\nTesting POST /forecast input validation (rejecting disallowed keys) ...")
    invalid_payload = {"traffic": {"future_attack_state": 1}}
    res_invalid = client.post("/forecast", json=invalid_payload)
    assert res_invalid.status_code == 422, f"Expected 422, got {res_invalid.status_code}"
    print("Input Validation : PASS (422 rejected invalid key)")

    print("\n" + "=" * 70)
    print("ALL FASTAPI BACKEND TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_backend()
