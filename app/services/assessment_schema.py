from typing import Literal

from pydantic import BaseModel, Field


class CropAssessment(BaseModel):
    success: bool = True

    crop: str = Field(
        description="The identified crop, or Unknown if it cannot be identified."
    )

    plant_health: Literal[
        "Healthy-looking",
        "Possible disease detected",
        "Possible pest damage",
        "Possible environmental stress",
        "Uncertain",
    ]

    possible_disease: str = Field(
        description=(
            "The suspected disease, or Unknown if the image "
            "does not support a reasonable identification."
        )
    )

    observed_symptoms: list[str] = Field(
        description="Visible symptoms observed in the submitted image."
    )

    confidence: Literal[
        "Low",
        "Moderate",
        "High",
        "Unable to assess",
    ]

    recommendations: list[str] = Field(
        description="Practical, cautious next steps for the user."
    )

    limitations: list[str] = Field(
        description="Uncertainties or limitations of this assessment."
    )