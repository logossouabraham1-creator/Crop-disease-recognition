from io import BytesIO
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.assessment_schema import CropAssessment
from app.services.Gen_service import KimiServiceError


client = TestClient(app)


def create_test_image() -> bytes:
    """Create a small, valid JPEG image for testing."""
    image = Image.new("RGB", (100, 100), color="green")

    image_bytes = BytesIO()
    image.save(image_bytes, format="JPEG")

    return image_bytes.getvalue()


def create_mock_assessment() -> CropAssessment:
    """Create a simulated assessment without calling an AI service."""
    return CropAssessment(
        success=True,
        crop="Tomato",
        plant_health="Possible disease detected",
        possible_disease="Possible early blight",
        observed_symptoms=[
            "Dark spots visible on the leaf"
        ],
        confidence="Moderate",
        recommendations=[
            "Inspect other leaves for similar symptoms",
            "Consult an agricultural extension officer"
        ],
        limitations=[
            "This is simulated test data, not a real diagnosis"
        ],
    )


def test_valid_image_returns_assessment():
    """A valid image should receive a simulated assessment."""

    mock_assessment = create_mock_assessment()

    with patch(
        "app.routes.analysis.analyze_crop_image",
        new_callable=AsyncMock,
        return_value=mock_assessment,
    ) as mock_analyze:

        response = client.post(
            "/api/analyze",
            files={
                "image": (
                    "tomato.jpg",
                    create_test_image(),
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["crop"] == "Tomato"
    assert data["possible_disease"] == "Possible early blight"

    mock_analyze.assert_awaited_once()


def test_invalid_file_is_rejected():
    """A text file must not be accepted as an image."""

    response = client.post(
        "/api/analyze",
        files={
            "image": (
                "not_an_image.txt",
                b"This is not an image",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert "valid" in response.json()["detail"].lower()


def test_oversized_upload_is_rejected():
    """An upload exceeding the size limit must be rejected."""

    from app.services.image_service import MAX_UPLOAD_BYTES

    oversized_content = b"x" * (MAX_UPLOAD_BYTES + 1)

    response = client.post(
        "/api/analyze",
        files={
            "image": (
                "large.jpg",
                oversized_content,
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 413

def test_ai_service_failure_returns_502():
    """An AI-service failure should produce a 502 response."""

    with patch(
        "app.routes.analysis.analyze_crop_image",
        new_callable=AsyncMock,
        side_effect=KimiServiceError(
            "Simulated AI service failure"
        ),
    ):
        response = client.post(
            "/api/analyze",
            files={
                "image": (
                    "tomato.jpg",
                    create_test_image(),
                    "image/jpeg",
                )
            },
        )

    assert response.status_code == 502

    data = response.json()

    assert data["detail"] == "Simulated AI service failure"