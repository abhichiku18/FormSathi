const canvas = document.getElementById("signatureCanvas");
const ctx = canvas.getContext("2d");
const clearButton = document.getElementById("clearSignature");
const saveButton = document.getElementById("saveSignature");
const message = document.getElementById("signatureMessage");

if (!localStorage.getItem("formsathiFormData")) {
  window.location.href = "form_editor.html";
}

ctx.lineWidth = 2.2;
ctx.lineCap = "round";
ctx.lineJoin = "round";
ctx.strokeStyle = "#111827";

let drawing = false;
let hasStroke = false;

function getPosition(event) {
  const rect = canvas.getBoundingClientRect();
  const point = event.touches?.[0] || event;
  return {
    x: (point.clientX - rect.left) * (canvas.width / rect.width),
    y: (point.clientY - rect.top) * (canvas.height / rect.height),
  };
}

function startDrawing(event) {
  drawing = true;
  const { x, y } = getPosition(event);
  ctx.beginPath();
  ctx.moveTo(x, y);
}

function draw(event) {
  if (!drawing) {
    return;
  }

  event.preventDefault();
  const { x, y } = getPosition(event);
  ctx.lineTo(x, y);
  ctx.stroke();
  hasStroke = true;
}

function stopDrawing() {
  drawing = false;
  ctx.closePath();
}

function clearCanvas() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  hasStroke = false;
  message.textContent = "Signature cleared.";
}

function saveSignature() {
  if (!hasStroke) {
    message.textContent = "Please add a signature before continuing.";
    return;
  }

  localStorage.setItem("formsathiSignature", canvas.toDataURL("image/png"));
  message.textContent = "Signature saved. Opening preview...";
  window.location.href = "preview.html";
}

canvas.addEventListener("mousedown", startDrawing);
canvas.addEventListener("mousemove", draw);
canvas.addEventListener("mouseup", stopDrawing);
canvas.addEventListener("mouseleave", stopDrawing);
canvas.addEventListener("touchstart", startDrawing, { passive: false });
canvas.addEventListener("touchmove", draw, { passive: false });
canvas.addEventListener("touchend", stopDrawing);
clearButton.addEventListener("click", clearCanvas);
saveButton.addEventListener("click", saveSignature);
