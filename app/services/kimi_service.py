import base64
import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.services.assessment_schema import CropAssessment


# Load settings from the project's .env file.
load_dotenv()


# OpenCode configuration.
OPENCODE_BASE_URL = os.getenv(
    "OPENCODE_BASE_URL",
    "https://opencode.ai/zen/v1",
)

KIMI_MODEL = os.getenv(
    "KIMI_MODEL",
    "kimi-k2.6",
)


# Development mode avoids real AI requests while we build the app.
# Set CDR_DEMO_MODE=false when you're ready to use the real AI service.
CDR_DEMO_MODE = (
    os.getenv("CDR_DEMO_MODE", "true").strip().lower()
    in {"1", "true", "yes", "on"}
)


class KimiConfigurationError(Exception):
    """Raised when the OpenCode/Kimi configuration is missing."""


class KimiServiceError(Exception):
    """Raised when the AI assessment fails."""


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
"""


def _image_to_data_url(
    image_bytes: bytes,
    image_format: str,
) -> str:
    """Convert validated image bytes into a Base64 data URL."""

    mime_types = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp",
    }

    normalized_format = image_format.upper()

    if normalized_format not in mime_types:
        raise KimiServiceError(
            "Unsupported image format for AI analysis."
        )

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    mime_type = mime_types[normalized_format]

    return f"data:{mime_type};base64,{encoded_image}"


def _create_demo_assessment() -> CropAssessment:
    """
    Return a clearly labelled placeholder assessment.

    No crop image is examined by an AI model in demo mode.
    """

    return CropAssessment(
        success=True,
        crop="Unknown",
        plant_health="Uncertain",
        possible_disease="Not assessed in demo mode",
        observed_symptoms=[],
        confidence="Unable to assess",
        recommendations=[
            "The image upload and backend connection are working.",
            (
                "No disease diagnosis was performed. "
                "Configure the real AI service to assess the image."
            ),
        ],
        limitations=[
            (
                "SIMULATED DEMO RESULT: no AI model examined "
                "this image. These are not diagnostic findings."
            ),
            (
                "The actual crop, symptoms, and possible disease "
                "have not been assessed."
            ),
        ],
    )


async def analyze_crop_image(
    image_bytes: bytes,
    image_format: str,
) -> CropAssessment:
    """
    Return a demo response or request a real AI assessment.

    The calling route must validate the uploaded image first.
    """

    # Development mode never makes a real AI request.
    if CDR_DEMO_MODE:
        return _create_demo_assessment()

    # Real AI mode requires a configured API key.
    api_key = os.getenv("OPENCODE_API_KEY")

    if not api_key or api_key.lower().startswith("your_"):
        raise KimiConfigurationError(
            "The OpenCode API key is not configured. "
            "Configure a valid key or enable CDR_DEMO_MODE."
        )

    image_data_url = _image_to_data_url(
        image_bytes=image_bytes,
        image_format=image_format,
    )

    try:
        async with AsyncOpenAI(
            api_key=api_key,
            base_url=OPENCODE_BASE_URL,
            timeout=60.0,
            max_retries=1,
        ) as client:

            response = await client.chat.completions.create(
                model=KIMI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": ASSESSMENT_INSTRUCTIONS,
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Assess this plant image. "
                                    "Return the required JSON object."
                                ),
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_data_url,
                                },
                            },
                        ],
                    },
                ],
                temperature=0.2,
                max_tokens=2048,
            )

    except OpenAIError as error:
        # Do not expose API credentials or raw provider details.
        raise KimiServiceError(
            "The AI service could not complete the request. "
            "Check your OpenCode account, model access, and "
            "available credits, then try again."
        ) from error

    if not response.choices:
        raise KimiServiceError(
            "The AI service returned no assessment."
        )

    content = response.choices[0].message.content

    if not content:
        raise KimiServiceError(
            "The AI service returned an empty assessment."
        )

    # Some models may wrap their JSON response in Markdown fences.
    cleaned_content = content.strip()

    if cleaned_content.startswith("```"):
        lines = cleaned_content.splitlines()

        if (
            lines
            and lines[0].startswith("```")
            and lines[-1].strip() == "```"
        ):
            cleaned_content = "\n".join(lines[1:-1]).strip()

    try:
        assessment_data = json.loads(cleaned_content)

        assessment = CropAssessment.model_validate(
            assessment_data
        )

    except (json.JSONDecodeError, ValidationError) as error:
        raise KimiServiceError(
            "The AI service returned an assessment "
            "that did not match the required format."
        ) from error

    return assessment