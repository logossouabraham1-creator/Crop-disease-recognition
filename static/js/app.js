// ============================================
// 1. GET THE HTML ELEMENTS
// ============================================
console.log("CDR app.js has started running");
const uploadForm = document.querySelector("#upload-form");
const cropImageInput = document.querySelector("#crop-image");
const previewContainer = document.querySelector("#preview-container");
const imagePreview = document.querySelector("#image-preview");
const uploadMessage = document.querySelector("#upload-message");
const analyzeButton = document.querySelector("#analyze-button");
const resultSection = document.querySelector("#result-section");
const resultContent = document.querySelector("#result-content");


// ============================================
// 2. CONFIGURATION
// ============================================

const allowedImageTypes = [
    "image/jpeg",
    "image/png",
    "image/webp"
];

const maximumFileSize = 5 * 1024 * 1024;

let currentPreviewUrl = null;


// ============================================
// 3. HELPER: SHOW A MESSAGE
// ============================================

function showUploadMessage(message) {
    uploadMessage.textContent = message;
}


// ============================================
// 4. HELPER: CLEAR PREVIOUS RESULTS
// ============================================

function clearResults() {
    resultSection.hidden = true;
    resultContent.replaceChildren();
}


// ============================================
// 5. HELPER: CREATE A HEADING
// ============================================

function createHeading(text, level = 3) {
    const heading = document.createElement(`h${level}`);

    heading.textContent = text;

    return heading;
}


// ============================================
// 6. HELPER: CREATE A PARAGRAPH
// ============================================

function createParagraph(text) {
    const paragraph = document.createElement("p");

    paragraph.textContent = text || "Not provided.";

    return paragraph;
}


// ============================================
// 7. HELPER: DISPLAY A LIST
// ============================================

function createTextList(items) {
    const list = document.createElement("ul");

    if (!Array.isArray(items) || items.length === 0) {
        const item = document.createElement("li");

        item.textContent = "None reported.";

        list.appendChild(item);

        return list;
    }

    items.forEach(function (text) {
        const item = document.createElement("li");

        item.textContent = String(text);

        list.appendChild(item);
    });

    return list;
}


// ============================================
// 8. HELPER: DISPLAY THE ASSESSMENT
// ============================================

function displayAssessment(assessment) {
    resultContent.replaceChildren();

    // Show the main assessment fields.

    resultContent.appendChild(
        createHeading("Assessment Overview")
    );

    resultContent.appendChild(
        createParagraph(`Crop: ${assessment.crop}`)
    );

    resultContent.appendChild(
        createParagraph(
            `Plant health: ${assessment.plant_health}`
        )
    );

    resultContent.appendChild(
        createParagraph(
            `Possible disease: ${assessment.possible_disease}`
        )
    );

    resultContent.appendChild(
        createParagraph(
            `Confidence: ${assessment.confidence}`
        )
    );


    // Show observed symptoms.

    resultContent.appendChild(
        createHeading("Observed Symptoms")
    );

    resultContent.appendChild(
        createTextList(assessment.observed_symptoms)
    );


    // Show recommendations.

    resultContent.appendChild(
        createHeading("Recommendations")
    );

    resultContent.appendChild(
        createTextList(assessment.recommendations)
    );


    // Show limitations and uncertainty.

    resultContent.appendChild(
        createHeading("Limitations and Important Notes")
    );

    resultContent.appendChild(
        createTextList(assessment.limitations)
    );


    // Make the result visible.

    resultSection.hidden = false;

    resultSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}


// ============================================
// 9. HANDLE IMAGE SELECTION
// ============================================

cropImageInput.addEventListener("change", function () {
    const selectedFile = cropImageInput.files[0];


    // Remove any previous temporary preview URL.

    if (currentPreviewUrl !== null) {
        URL.revokeObjectURL(currentPreviewUrl);

        currentPreviewUrl = null;
    }


    // Reset the previous preview and result.

    previewContainer.hidden = true;

    imagePreview.removeAttribute("src");

    analyzeButton.disabled = true;

    showUploadMessage("");

    clearResults();


    // Check whether a file was selected.

    if (!selectedFile) {
        showUploadMessage(
            "Please select a crop image."
        );

        return;
    }


    // Validate the file type in the browser.

    if (!allowedImageTypes.includes(selectedFile.type)) {
        showUploadMessage(
            "Invalid file type. Select a JPEG, PNG, or WebP image."
        );

        cropImageInput.value = "";

        return;
    }


    // Validate the file size in the browser.

    if (selectedFile.size > maximumFileSize) {
        showUploadMessage(
            "The image exceeds the 5 MiB upload limit."
        );

        cropImageInput.value = "";

        return;
    }


    // Create a temporary URL for the image preview.

    currentPreviewUrl = URL.createObjectURL(selectedFile);

    imagePreview.src = currentPreviewUrl;

    previewContainer.hidden = false;


    // Confirm that the image is ready.

    showUploadMessage(
        "Image selected successfully. Ready for analysis."
    );


    // Allow the user to submit the image.

    analyzeButton.disabled = false;
});


// ============================================
// 10. SUBMIT THE IMAGE TO FASTAPI
// ============================================

uploadForm.addEventListener("submit", async function (event) {
    // Prevent the browser's normal form submission.
    event.preventDefault();


    const selectedFile = cropImageInput.files[0];


    // Make sure an image has been selected.

    if (!selectedFile) {
        showUploadMessage(
            "Please select an image before starting the analysis."
        );

        return;
    }


    // Prepare the image for a multipart/form-data request.

    const formData = new FormData();

    formData.append("image", selectedFile);


    // Inform the user that processing has started.

    analyzeButton.disabled = true;

    analyzeButton.textContent = "Analyzing...";

    showUploadMessage(
        "Uploading your image and waiting for the assessment..."
    );

    clearResults();


    try {
        // Send the image to the FastAPI endpoint.

        const response = await fetch("/api/analyze", {
            method: "POST",
            body: formData
        });


        // Read the JSON response.

        const data = await response.json();


        // Handle HTTP errors returned by the backend.

        if (!response.ok) {
            const errorMessage =
                typeof data.detail === "string"
                    ? data.detail
                    : "The server could not process your image.";

            throw new Error(errorMessage);
        }


        // Make sure the response contains an assessment.

        if (
            !data ||
            typeof data !== "object" ||
            typeof data.crop !== "string" ||
            !Array.isArray(data.recommendations) ||
            !Array.isArray(data.limitations)
        ) {
            throw new Error(
                "The server returned an unexpected assessment format."
            );
        }


        // Display the returned assessment.

        displayAssessment(data);

        showUploadMessage(
            "Assessment received. Review the limitations before acting on it."
        );

    } catch (error) {
        console.error("Crop assessment request failed:", error);


        // Display a useful error without exposing technical details.

        const message =
            error instanceof Error
                ? error.message
                : "An unexpected error occurred.";

        showUploadMessage(
            `Unable to complete the assessment: ${message}`
        );

    } finally {
        // Restore the button after the request finishes.

        analyzeButton.disabled = !cropImageInput.files[0];

        analyzeButton.textContent = "Analyze Image";
    }
});