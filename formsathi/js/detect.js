const detectStatus = document.getElementById("detectStatus");
const uploadResponse = JSON.parse(localStorage.getItem("formsathiUploadResponse") || "null");

if (!uploadResponse) {
  window.location.href = "upload.html";
}

const phases = [
  "OCR extraction is complete. Preparing field suggestions now.",
  "Groq is analyzing the extracted text for fillable fields.",
  "Detected field structure is ready. Redirecting to the editor.",
];

let phaseIndex = 0;

const timer = setInterval(() => {
  phaseIndex += 1;
  if (phaseIndex >= phases.length) {
    clearInterval(timer);
    window.location.href = "form_editor.html";
    return;
  }

  detectStatus.textContent = phases[phaseIndex];
}, 1400);
