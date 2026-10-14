// ============================================
// 1. GET THE HTML ELEMENTS
// ============================================

const uploadForm = document.querySelector("#upload-form");

const cropImageInput = document.querySelector("#crop-image");

const previewContainer = document.querySelector("#preview-container");

const imagePreview = document.querySelector("#image-preview");

const uploadMessage = document.querySelector("#upload-message");

const analyzeButton = document.querySelector("#analyze-button");

const resultSection = document.querySelector("#result-section");

const resultContent = document.querySelector("#result-content");


// ============================================
// 2. DEFINE THE ALLOWED IMAGE TYPES
// ============================================

const allowedImageTypes = [
    "image/jpeg",
    "image/png",
    "image/webp"
];


// ============================================
// 3. SET THE MAXIMUM FILE SIZE
// ============================================

// Maximum file size: 5 MB

const maximumFileSize = 5 * 1024 * 1024;


// ============================================
// 4. HANDLE IMAGE SELECTION
// ============================================

cropImageInput.addEventListener("change", function () {

    // Get the selected file.

    const selectedFile = cropImageInput.files[0];


    // Reset the previous preview and messages.

    previewContainer.hidden = true;

    imagePreview.removeAttribute("src");

    analyzeButton.disabled = true;

    uploadMessage.textContent = "";

    resultSection.hidden = true;

    resultContent.textContent = "";


    // Check whether the user selected a file.

    if (!selectedFile) {

        uploadMessage.textContent = "Please select a crop image.";

        return;
    }


    // Check the file type.

    if (!allowedImageTypes.includes(selectedFile.type)) {

        uploadMessage.textContent =
            "Invalid file type. Please select a JPEG, PNG, or WebP image.";

        cropImageInput.value = "";

        return;
    }


    // Check the file size.

    if (selectedFile.size > maximumFileSize) {

        uploadMessage.textContent =
            "The image is too large. Please select an image smaller than 5 MB.";

        cropImageInput.value = "";

        return;
    }


    // Create a temporary URL for the selected image.

    const imageURL = URL.createObjectURL(selectedFile);


    // Display the selected image.

    imagePreview.src = imageURL;

    previewContainer.hidden = false;


    // Tell the user that the image was selected successfully.

    uploadMessage.textContent = "Image selected successfully.";


    // Enable the Analyze Image button.

    analyzeButton.disabled = false;

});


// ============================================
// 5. HANDLE FORM SUBMISSION
// ============================================

uploadForm.addEventListener("submit", function (event) {

    // Prevent the browser from submitting the form normally.

    event.preventDefault();


    // Get the selected file.

    const selectedFile = cropImageInput.files[0];


    // Make sure a file is available.

    if (!selectedFile) {

        uploadMessage.textContent = "Please select an image first.";

        return;
    }


    // Show a temporary message.

    uploadMessage.textContent =
        "Image selected. Backend analysis will be connected next.";


    console.log("Selected image:", selectedFile.name);

    console.log("Image type:", selectedFile.type);

    console.log("Image size:", selectedFile.size, "bytes");

});