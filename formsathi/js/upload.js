const API_BASE_URL = "http://127.0.0.1:8000";

const state = {
  file: null,
  previewUrl: null,
};

const dropZone = document.getElementById("dropZone");
const fileInput = document.getElementById("fileInput");
const browseButton = document.getElementById("browseButton");
const previewCard = document.getElementById("previewCard");
const imagePreview = document.getElementById("imagePreview");
const pdfPreview = document.getElementById("pdfPreview");
const fileNameLabel = document.getElementById("fileName");
const removeFileButton = document.getElementById("removeFile");
const uploadButton = document.getElementById("uploadButton");
const loadingSpinner = document.getElementById("loadingSpinner");
const uploadError = document.getElementById("uploadError");

function resetStoredSession() {
  [
    "formsathiUploadResponse",
    "formsathiFields",
    "formsathiOriginalFields",
    "formsathiLanguage",
    "formsathiFormData",
    "formsathiSignature",
    "formsathiGeneratedPdf",
    "formsathiPlacementMode",
  ].forEach((key) => localStorage.removeItem(key));
}

function setError(message = "") {
  uploadError.textContent = message;
  uploadError.classList.toggle("hidden", !message);
}

function clearPreview() {
  if (state.previewUrl) {
    URL.revokeObjectURL(state.previewUrl);
  }

  state.file = null;
  state.previewUrl = null;
  previewCard.classList.add("hidden");
  imagePreview.classList.add("hidden");
  pdfPreview.classList.add("hidden");
  imagePreview.src = "";
  pdfPreview.src = "";
  fileNameLabel.textContent = "No file selected";
  uploadButton.disabled = true;
}

function renderPreview(file) {
  clearPreview();
  state.file = file;
  state.previewUrl = URL.createObjectURL(file);
  fileNameLabel.textContent = file.name;
  previewCard.classList.remove("hidden");
  uploadButton.disabled = false;

  if (file.type === "application/pdf") {
    pdfPreview.src = state.previewUrl;
    pdfPreview.classList.remove("hidden");
  } else {
    imagePreview.src = state.previewUrl;
    imagePreview.classList.remove("hidden");
  }
}

function validateFile(file) {
  if (!file) {
    return "Please choose a file.";
  }

  const allowedExtensions = [".pdf", ".jpg", ".jpeg", ".png"];
  const lowerName = file.name.toLowerCase();
  const isAllowed = allowedExtensions.some((ext) => lowerName.endsWith(ext));
  return isAllowed ? "" : "Unsupported file type. Please upload PDF, JPG, JPEG, or PNG.";
}

async function uploadFile() {
  const validationError = validateFile(state.file);
  if (validationError) {
    setError(validationError);
    return;
  }

  const formData = new FormData();
  formData.append("file", state.file);
  setError("");
  uploadButton.disabled = true;
  loadingSpinner.classList.remove("hidden");

  try {
    const response = await fetch(`${API_BASE_URL}/upload-form`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Upload failed.");
    }

    const payload = await response.json();
    localStorage.setItem("formsathiUploadResponse", JSON.stringify(payload));
    localStorage.setItem("formsathiOriginalFields", JSON.stringify(payload.detected_fields || []));
    localStorage.setItem("formsathiFields", JSON.stringify(payload.detected_fields || []));
    localStorage.setItem("formsathiLanguage", "English");
    window.location.href = "detect.html";
  } catch (error) {
    uploadButton.disabled = false;
    setError(error.message || "Something went wrong during upload.");
  } finally {
    loadingSpinner.classList.add("hidden");
  }
}

browseButton.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  const validationError = validateFile(file);
  if (validationError) {
    clearPreview();
    setError(validationError);
    return;
  }

  setError("");
  renderPreview(file);
});

["dragenter", "dragover"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.add("dragover");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropZone.classList.remove("dragover");
  });
});

dropZone.addEventListener("drop", (event) => {
  const file = event.dataTransfer?.files?.[0];
  const validationError = validateFile(file);
  if (validationError) {
    clearPreview();
    setError(validationError);
    return;
  }

  setError("");
  renderPreview(file);
});

removeFileButton.addEventListener("click", () => {
  fileInput.value = "";
  clearPreview();
  setError("");
});

uploadButton.addEventListener("click", uploadFile);
resetStoredSession();
