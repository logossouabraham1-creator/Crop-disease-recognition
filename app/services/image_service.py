from io import BytesIO

from PIL import Image, UnidentifiedImageError


# Maximum permitted upload size: 5 MiB.
MAX_UPLOAD_BYTES = 5 * 1024 * 1024

# Maximum permitted number of pixels.
MAX_IMAGE_PIXELS = 25_000_000

# Image formats supported by our application.
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


def validate_image(image_bytes: bytes) -> dict:
    """
    Validate an uploaded image before AI analysis.

    Returns information about a valid image.

    Raises:
        ValueError: If the image is empty, too large,
                    unsupported, or unreadable.
    """

    # 1. Reject empty uploads.
    if not image_bytes:
        raise ValueError("The uploaded file is empty.")

    # 2. Check the file size.
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError(
            "The image exceeds the 5 MiB upload limit."
        )

    # 3. Open and inspect the image.
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_format = image.format
            width, height = image.size

            # 4. Allow only supported formats.
            if image_format not in ALLOWED_FORMATS:
                raise ValueError(
                    "Unsupported image format. "
                    "Please upload a JPEG, PNG, or WebP image."
                )

            # 5. Reject invalid dimensions.
            if width <= 0 or height <= 0:
                raise ValueError(
                    "The image has invalid dimensions."
                )

            # 6. Prevent excessively large images.
            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError(
                    "The image dimensions are too large to process."
                )

            # 7. Check the image data for corruption.
            image.verify()

    except ValueError:
        raise

    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
    ) as error:
        raise ValueError(
            "The file is not a valid, readable image."
        ) from error

    # 8. Return information for the analysis route.
    return {
        "format": image_format,
        "width": width,
        "height": height,
        "size_bytes": len(image_bytes),
    }