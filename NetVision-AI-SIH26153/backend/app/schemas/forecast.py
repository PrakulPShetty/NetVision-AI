"""
Request and response schemas for the forecasting API.
"""

from typing import Dict

from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """
    Input schema for the network attack forecasting endpoint.

    The backend currently receives the 138 model-ready features.
    Frontend-friendly raw traffic input will be handled in a
    later preprocessing/integration stage.
    """

    features: Dict[str, float] = Field(
        ...,
        description="138 model-ready network traffic features."
    )