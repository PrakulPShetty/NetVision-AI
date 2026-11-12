"""Route-level tests for the multipart ingestion endpoints.

A stub pipeline keeps these tests independent of the trained artifacts.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routes.ingestion import create_ingestion_router

CSV = (
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


class StubPipeline:
    def __init__(self):
        self.calls = []

    def forecast(self, features):
        self.calls.append(("features", features))
        return {"stub": "features", "count": len(features)}

    def forecast_from_traffic(self, profile):
        self.calls.append(("profile", profile))
        return {"stub": "profile", "flow_count": profile["flow_count"]}


def _client():
    pipeline = StubPipeline()
    app = FastAPI()
    app.include_router(create_ingestion_router(pipeline))
    return TestClient(app), pipeline


def test_preprocess_endpoint():
    client, _ = _client()
    response = client.post(
        "/preprocess/file",
        files={"file": ("flows.csv", CSV, "text/csv")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "cicflowmeter_csv"
    assert body["window_count"] == 1
    assert body["windows"][0]["profile"]["flow_count"] == 1


def test_forecast_file_endpoint_profile_window():
    client, pipeline = _client()
    response = client.post(
        "/forecast/file",
        files={"file": ("flows.csv", CSV, "text/csv")},
        data={"window_index": "0"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "profile"
    assert body["forecast"]["stub"] == "profile"
    assert pipeline.calls[0][0] == "profile"


def test_forecast_file_endpoint_out_of_range():
    client, _ = _client()
    response = client.post(
        "/forecast/file",
        files={"file": ("flows.csv", CSV, "text/csv")},
        data={"window_index": "99"},
    )

    assert response.status_code == 422
    assert "window_index" in response.json()["detail"]


def test_preprocess_endpoint_rejects_unknown_file():
    client, _ = _client()
    response = client.post(
        "/preprocess/file",
        files={"file": ("unknown.bin", b"\x00\x01\x02", "application/octet-stream")},
    )

    assert response.status_code == 415
