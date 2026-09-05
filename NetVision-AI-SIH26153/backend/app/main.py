"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="NetVision AI")


@app.get("/")
def read_root():
    return {"message": "NetVision AI backend is running."}
