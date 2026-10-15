from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.image_service import (
    MAX_UPLOAD_BYTES,
    validate_image,
)

from app.services.kimi_service import (
    KimiConfigurationError,
    KimiServiceError,
    analyze_crop_image,
)


router = APIRouter()


@router.post("/analyze")
async def analyze_crop(image: UploadFile = File(...)):
    """
    Receive a plant image, validate it, and request
    a preliminary crop health assessment from Kimi.
    """

    try:
        # 1. Read no more than the permitted size plus one byte.
        image_bytes = await image.read(MAX_UPLOAD_BYTES + 1)

        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail="The image exceeds the 5 MiB upload limit.",
            )

        # 2. Validate the uploaded image.
        try:
            image_information = validate_image(image_bytes)

        except ValueError as error:
            raise HTTPException(
                status_code=400,
                detail=str(error),
            ) from error

        # 3. Send the validated image to Kimi.
        try:
            assessment = await analyze_crop_image(
                image_bytes=image_bytes,
                image_format=image_information["format"],
            )

        except KimiConfigurationError as error:
            raise HTTPException(
                status_code=503,
                detail=str(error),
            ) from error

        except KimiServiceError as error:
            raise HTTPException(
                status_code=502,
                detail=str(error),
            ) from error

        # 4. Return the validated assessment as JSON.
        return assessment.model_dump()

    finally:
        # 5. Close the uploaded file when processing finishes.
        await image.close()