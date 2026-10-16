import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import ValidationError

from app.services.assessment_schema import CropAssessment


# Load environment variables from the project's .env file.
load_dotenv()


# Gemini configuration.
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash",
)


class GenConfigurationError(Exception):
    """Raised when the Gemini configuration is missing."""


class GenServiceError(Exception):
    """Raised when Gemini cannot complete an assessment."""


ASSESSMENT_INSTRUCTIONS = """
You are an assistant supporting preliminary crop health assessment.

Carefully examine the submitted plant image.

Your responsibilities:

1. Identify the crop only when the image provides enough evidence.
2. Describe symptoms that are actually visible in the image.
3. Suggest a possible disease only when visual evidence supports it.
4. Distinguish visible observations from possible explanations.
5. Provide practical and cautious recommendations.
6. Explain uncertainty and limitations.
7. If the image is unclear, unrelated to crops, or insufficient,
   do not invent a diagnosis.
8. Do not claim that a suspected disease is confirmed.
9. Do not recommend a specific pesticide or dosage without
   sufficient evidence and appropriate context.
10. If the plant is not a tomato, identify the actual crop when
    possible. Do not automatically classify every image as tomato.

Return ONLY one valid JSON object with these fields:

{
    "success": true,
    "crop": "Tomato or Unknown",
    "plant_health": "Uncertain",
    "possible_disease": "Unknown",
    "observed_symptoms": [],
    "confidence": "Unable to assess",
    "recommendations": [],
    "limitations": []
}

Required rules:

- success must be a boolean.
- crop must be a string.
- plant_health must be exactly one of:
  "Healthy-looking",
  "Possible disease detected",
  "Possible pest damage",
  "Possible environmental stress",
  "Uncertain".
- possible_disease must be a string.
- observed_symptoms must be a list of strings.
- confidence must be exactly one of:
  "Low",
  "Moderate",
  "High",
  "Unable to assess".
- recommendations must be a list of strings.
- limitations must be a list of strings.
- Include every required field.
- Do not wrap the JSON in Markdown code fences.
- Do not add explanations outside the JSON object.
- Do not invent symptoms that are not visible in the image.
- Explain when the image quality prevents reliable assessment.
"""


def _get_image_mime_type(image_format: str) -> str:
    """Convert the validated image format into a MIME type."""

    mime_types = {
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    normalized_format = image_format.upper()

    if normalized_format not in mime_types:
        raise GenServiceError(
            "Unsupported image format for Gemini analysis."
        )

    return mime_types[normalized_format]


def _clean_json_response(content: str) -> str:
    """Remove Markdown code fences if the model includes them."""

    content = content.strip()

    if not content.startswith("```"):
        return content

    lines = content.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


async def analyze_crop_image(
    image_bytes: bytes,
    image_format: str,
) -> CropAssessment:
    """
    Send a plant image to Gemini and return a validated assessment.

    This function does not return simulated demo assessments.
    Every successful assessment must come from a Gemini response.
    """

    # Require a real API key.
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key or api_key.lower().startswith("your_"):
        raise GenConfigurationError(
            "GEMINI_API_KEY is missing or has not been configured. "
            "Add a valid Gemini API key to your .env file."
        )

    # Validate the image format.
    mime_type = _get_image_mime_type(image_format)

    # Convert the uploaded image into a Gemini-compatible part.
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type=mime_type,
    )

    client = genai.Client(api_key=api_key)

    try:
        # Make the actual Gemini image-analysis request.
        response = await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                ASSESSMENT_INSTRUCTIONS,
                (
                    "Examine the attached plant image and return "
                    "the required JSON assessment."
                ),
                image_part,
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=2048,
                response_mime_type="application/json",
            ),
        )

    except APIError as error:
        # Log diagnostic details without exposing the API key.
        print(
            f"Gemini API error: "
            f"{type(error).__name__}: {str(error)[:500]}"
        )

        status_code = getattr(error, "code", None)

        if status_code == 401 or status_code == 403:
            message = (
                "Gemini authentication failed. Check whether "
                "your API key is valid and authorized."
            )
        elif status_code == 429:
            message = (
                "Gemini rejected the request because of a quota "
                "or rate limit. Check your available API usage."
            )
        elif status_code == 404:
            message = (
                f"The Gemini model '{GEMINI_MODEL}' was not found "
                "or is unavailable to this API. Check the model name."
            )
        else:
            message = (
                "Gemini could not complete the request. "
                "Check the server logs for diagnostic details."
            )

        raise GenServiceError(message) from error

    except Exception as error:
        print(
            f"Gemini request error: "
            f"{type(error).__name__}: {str(error)[:500]}"
        )

        raise GenServiceError(
            "An unexpected error occurred while contacting Gemini. "
            "Check the server logs for diagnostic details."
        ) from error

    finally:
        # Release the asynchronous client's resources.
        await client.aio.aclose()

    # Ensure Gemini returned content.
    content = response.text

    if not content:
        raise GenServiceError(
            "Gemini returned no assessment content. "
            "Try another image or check the model response."
        )

    # Parse and validate the returned JSON.
    try:
        assessment_data = json.loads(
            _clean_json_response(content)
        )

        assessment = CropAssessment.model_validate(
            assessment_data
        )

    except json.JSONDecodeError as error:
        print(
            "Gemini returned invalid JSON: "
            f"{str(error)[:300]}"
        )

        raise GenServiceError(
            "Gemini returned an invalid JSON assessment."
        ) from error

    except ValidationError as error:
        print(
            "Gemini assessment failed schema validation: "
            f"{str(error)[:500]}"
        )

        raise GenServiceError(
            "Gemini returned an assessment that does not match "
            "the required CropAssessment schema."
        ) from error

    return assessment