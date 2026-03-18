const API_BASE_URL = "http://127.0.0.1:8000";

const state = {
  file: null,
  previewUrl: "",
  uploadId: "",
  mode: "text",
  annotations: [],
  signatureData: "",
  pageViews: [],
  pageSizes: [],
  highlightDraft: null,
  draggedAnnotationId: null,
  dragOffset: null,
};

const editorFileInput = document.getElementById("editorFileInput");
const openEditorPdfButton = document.getElementById("openEditorPdfButton");
const refreshRenderedPreviewButton = document.getElementById("refreshRenderedPreviewButton");
const exportEditorButton = document.getElementById("exportEditorButton");
const editorStatus = document.getElementById("editorStatus");
const editorError = document.getElementById("editorError");
const editorFileName = document.getElementById("editorFileName");
const pdfEditorPages = document.getElementById("pdfEditorPages");
const toolButtons = Array.from(document.querySelectorAll(".tool-button"));
const fontSizeInput = document.getElementById("fontSizeInput");
const undoAnnotationButton = document.getElementById("undoAnnotationButton");
const clearAnnotationsButton = document.getElementById("clearAnnotationsButton");
const signatureCanvas = document.getElementById("editorSignatureCanvas");
const clearEditorSignature = document.getElementById("clearEditorSignature");
const saveEditorSignature = document.getElementById("saveEditorSignature");
const editorSignatureStatus = document.getElementById("editorSignatureStatus");
const editorTranslationLanguage = document.getElementById("editorTranslationLanguage");
const translatePdfButton = document.getElementById("translatePdfButton");
const clearTranslationButton = document.getElementById("clearTranslationButton");
const translationStatus = document.getElementById("translationStatus");
const translationResult = document.getElementById("translationResult");
const renderedEditorPreviewCard = document.getElementById("renderedEditorPreviewCard");
const renderedEditorPreviewFrame = document.getElementById("renderedEditorPreviewFrame");
const renderedEditorPreviewStatus = document.getElementById("renderedEditorPreviewStatus");
const downloadEditedPdfLink = document.getElementById("downloadEditedPdfLink");
const floatingRenderedEditorPreviewCard = document.getElementById("floatingRenderedEditorPreviewCard");
const floatingRenderedEditorPreviewFrame = document.getElementById("floatingRenderedEditorPreviewFrame");
const floatingRenderedEditorPreviewStatus = document.getElementById("floatingRenderedEditorPreviewStatus");

const signatureContext = signatureCanvas.getContext("2d");
const textMeasureCanvas = document.createElement("canvas");
const textMeasureContext = textMeasureCanvas.getContext("2d");
let isSigning = false;
let renderedPreviewTimer = null;

function setEditorError(message = "") {
  editorError.textContent = message;
  editorError.classList.toggle("hidden", !message);
}

function updateStatus(message) {
  editorStatus.textContent = message;
}

function setRenderedPreviewState(message, pdfUrl = "") {
  renderedEditorPreviewStatus.textContent =
    message || "This preview uses the same backend renderer as the downloaded PDF.";
  renderedEditorPreviewCard.classList.toggle("hidden", !message && !pdfUrl);
  renderedEditorPreviewFrame.src = pdfUrl || "";
  downloadEditedPdfLink.href = pdfUrl || "#";
  downloadEditedPdfLink.classList.toggle("disabled-link", !pdfUrl);
  floatingRenderedEditorPreviewStatus.textContent =
    message || "This corner preview uses the backend PDF renderer.";
  floatingRenderedEditorPreviewCard.classList.toggle("hidden", !message && !pdfUrl);
  floatingRenderedEditorPreviewFrame.src = pdfUrl || "";
}

function setTranslationState(message = "", translatedText = "") {
  translationStatus.textContent =
    message || "Optional reading view only. Your original PDF and editor layout stay unchanged.";
  translationStatus.classList.toggle("hidden", !message && !translatedText);
  translationResult.textContent = translatedText;
  translationResult.classList.toggle("hidden", !translatedText);
}

function setTool(tool) {
  state.mode = tool;
  toolButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.tool === tool);
  });
}

function clearPreviewUrl() {
  if (state.previewUrl) {
    URL.revokeObjectURL(state.previewUrl);
    state.previewUrl = "";
  }
}

function getPointWithinElement(event, element) {
  const rect = element.getBoundingClientRect();
  return {
    x: event.clientX - rect.left,
    y: event.clientY - rect.top,
    width: rect.width,
    height: rect.height,
  };
}

function renderAnnotations() {
  state.pageViews.forEach(({ layer, pageNumber, overlay }) => {
    layer.innerHTML = "";
    const pageAnnotations = state.annotations.filter((item) => item.page === pageNumber - 1);

    pageAnnotations.forEach((annotation) => {
      const node = document.createElement("div");
      node.className = `editor-annotation ${annotation.type}`;
      node.dataset.annotationId = annotation.id;
      node.style.left = `${annotation.xRatio * overlay.clientWidth}px`;
      node.style.top = `${annotation.yRatio * overlay.clientHeight}px`;
      node.style.width = `${annotation.widthRatio * overlay.clientWidth}px`;
      node.style.height = `${annotation.heightRatio * overlay.clientHeight}px`;

      if (annotation.type === "text") {
        node.classList.add("draggable");
        node.textContent = annotation.content;
        node.style.fontSize = `${annotation.fontSize}px`;
        node.style.lineHeight = "1.2";
      } else if (annotation.type === "signature") {
        node.classList.add("draggable");
        const image = document.createElement("img");
        image.src = annotation.signatureData;
        image.alt = "Signature preview";
        node.appendChild(image);
      }

      layer.appendChild(node);
    });
  });
}

function measureTextBlock(content, fontSize) {
  const lines = String(content || "").split(/\r?\n/);
  textMeasureContext.font = `${fontSize}px Arial`;
  const widestLine = lines.reduce((widest, line) => {
    return Math.max(widest, textMeasureContext.measureText(line || " ").width);
  }, 0);

  return {
    width: widestLine + 16,
    height: Math.max(lines.length, 1) * (fontSize * 1.2) + 12,
  };
}

function addTextAnnotation(pageIndex, point) {
  const content = window.prompt("Enter the text you want to place on the PDF:");
  if (!content) {
    return;
  }

  const fontSize = Math.max(10, Math.min(32, Number(fontSizeInput.value) || 16));
  const measured = measureTextBlock(content, fontSize);
  const width = Math.min(point.width * 0.42, Math.max(120, measured.width));
  const height = Math.max(fontSize * 1.4, measured.height);

  state.annotations.push({
    id: crypto.randomUUID(),
    type: "text",
    page: pageIndex,
    content,
    fontSize,
    xRatio: point.x / point.width,
    yRatio: point.y / point.height,
    widthRatio: width / point.width,
    heightRatio: height / point.height,
  });

  renderAnnotations();
  scheduleRenderedPreview();
}

function placeSignature(pageIndex, point) {
  if (!state.signatureData) {
    setEditorError("Draw and save a signature first.");
    return;
  }

  setEditorError("");
  state.annotations.push({
    id: crypto.randomUUID(),
    type: "signature",
    page: pageIndex,
    signatureData: state.signatureData,
    xRatio: point.x / point.width,
    yRatio: point.y / point.height,
    widthRatio: Math.min(180 / point.width, 0.32),
    heightRatio: Math.min(72 / point.height, 0.12),
  });

  renderAnnotations();
  scheduleRenderedPreview();
}

function updateAnnotationPosition(annotationId, pageIndex, point, offset) {
  const annotation = state.annotations.find((item) => item.id === annotationId && item.page === pageIndex);
  if (!annotation) {
    return;
  }

  const widthPx = annotation.widthRatio * point.width;
  const heightPx = annotation.heightRatio * point.height;
  const nextX = Math.min(Math.max(point.x - offset.x, 0), Math.max(point.width - widthPx, 0));
  const nextY = Math.min(Math.max(point.y - offset.y, 0), Math.max(point.height - heightPx, 0));

  annotation.xRatio = nextX / point.width;
  annotation.yRatio = nextY / point.height;
}

function bindPageInteractions(layer, pageIndex) {
  layer.addEventListener("click", (event) => {
    if (event.target.closest(".editor-annotation.draggable")) {
      return;
    }

    if (state.mode === "highlight" && state.highlightDraft) {
      return;
    }

    const point = getPointWithinElement(event, layer);
    if (state.mode === "text") {
      addTextAnnotation(pageIndex, point);
    } else if (state.mode === "signature") {
      placeSignature(pageIndex, point);
    }
  });

  layer.addEventListener("pointerdown", (event) => {
    const draggableAnnotation = event.target.closest(".editor-annotation.draggable");
    if (draggableAnnotation) {
      const point = getPointWithinElement(event, layer);
      state.draggedAnnotationId = draggableAnnotation.dataset.annotationId;
      state.dragOffset = {
        x: point.x - draggableAnnotation.offsetLeft,
        y: point.y - draggableAnnotation.offsetTop,
      };
      layer.setPointerCapture(event.pointerId);
      return;
    }

    if (state.mode !== "highlight") {
      return;
    }

    const start = getPointWithinElement(event, layer);
    const draft = document.createElement("div");
    draft.className = "editor-annotation highlight draft";
    draft.style.left = `${start.x}px`;
    draft.style.top = `${start.y}px`;
    draft.style.width = "0px";
    draft.style.height = "0px";
    layer.appendChild(draft);
    state.highlightDraft = { pageIndex, start, layer, draft };
    layer.setPointerCapture(event.pointerId);
  });

  layer.addEventListener("pointermove", (event) => {
    if (state.draggedAnnotationId) {
      const point = getPointWithinElement(event, layer);
      updateAnnotationPosition(state.draggedAnnotationId, pageIndex, point, state.dragOffset);
      renderAnnotations();
      return;
    }

    if (!state.highlightDraft || state.highlightDraft.pageIndex !== pageIndex) {
      return;
    }

    const current = getPointWithinElement(event, layer);
    const left = Math.min(state.highlightDraft.start.x, current.x);
    const top = Math.min(state.highlightDraft.start.y, current.y);
    const width = Math.abs(current.x - state.highlightDraft.start.x);
    const height = Math.abs(current.y - state.highlightDraft.start.y);

    state.highlightDraft.draft.style.left = `${left}px`;
    state.highlightDraft.draft.style.top = `${top}px`;
    state.highlightDraft.draft.style.width = `${width}px`;
    state.highlightDraft.draft.style.height = `${height}px`;
  });

  layer.addEventListener("pointerup", (event) => {
    if (state.draggedAnnotationId) {
      const point = getPointWithinElement(event, layer);
      updateAnnotationPosition(state.draggedAnnotationId, pageIndex, point, state.dragOffset);
      state.draggedAnnotationId = null;
      state.dragOffset = null;
      renderAnnotations();
      scheduleRenderedPreview();
      layer.releasePointerCapture(event.pointerId);
      return;
    }

    if (!state.highlightDraft || state.highlightDraft.pageIndex !== pageIndex) {
      return;
    }

    const current = getPointWithinElement(event, layer);
    const left = Math.min(state.highlightDraft.start.x, current.x);
    const top = Math.min(state.highlightDraft.start.y, current.y);
    const width = Math.abs(current.x - state.highlightDraft.start.x);
    const height = Math.abs(current.y - state.highlightDraft.start.y);

    state.highlightDraft.draft.remove();
    state.highlightDraft = null;

    if (width < 10 || height < 10) {
      return;
    }

    state.annotations.push({
      id: crypto.randomUUID(),
      type: "highlight",
      page: pageIndex,
      xRatio: left / layer.clientWidth,
      yRatio: top / layer.clientHeight,
      widthRatio: width / layer.clientWidth,
      heightRatio: height / layer.clientHeight,
    });

    renderAnnotations();
    scheduleRenderedPreview();
    layer.releasePointerCapture(event.pointerId);
  });
}

function buildPageFrame(pageNumber, pageSize) {
  const shell = document.createElement("article");
  shell.className = "pdf-editor-page";

  const label = document.createElement("div");
  label.className = "pdf-page-label";
  label.textContent = `Page ${pageNumber}`;

  const ratio = pageSize.height / pageSize.width;
  const width = Math.min(760, pdfEditorPages.clientWidth - 40 || 760);
  const height = Math.max(width * ratio, 420);

  const stage = document.createElement("div");
  stage.className = "pdf-page-stage";
  stage.style.width = `${width}px`;
  stage.style.height = `${height}px`;

  const frame = document.createElement("iframe");
  frame.className = "pdf-page-frame";
  frame.src = `${state.previewUrl}#page=${pageNumber}&toolbar=0&navpanes=0&scrollbar=0&view=FitH`;
  frame.title = `PDF page ${pageNumber}`;

  const overlay = document.createElement("div");
  overlay.className = "pdf-overlay-surface";

  const layer = document.createElement("div");
  layer.className = "pdf-annotation-layer";

  overlay.appendChild(layer);
  stage.appendChild(frame);
  stage.appendChild(overlay);
  shell.appendChild(label);
  shell.appendChild(stage);
  pdfEditorPages.appendChild(shell);

  bindPageInteractions(layer, pageNumber - 1);
  state.pageViews.push({ pageNumber, overlay, layer });
}

function buildImageFrame(pageNumber, pageSize) {
  const shell = document.createElement("article");
  shell.className = "pdf-editor-page";

  const label = document.createElement("div");
  label.className = "pdf-page-label";
  label.textContent = `Image ${pageNumber}`;

  const ratio = pageSize.height / pageSize.width;
  const width = Math.min(760, pdfEditorPages.clientWidth - 40 || 760);
  const height = Math.max(width * ratio, 420);

  const stage = document.createElement("div");
  stage.className = "pdf-page-stage";
  stage.style.width = `${width}px`;
  stage.style.height = `${height}px`;

  const image = document.createElement("img");
  image.className = "pdf-page-image";
  image.src = state.previewUrl;
  image.alt = `Uploaded image ${pageNumber}`;

  const overlay = document.createElement("div");
  overlay.className = "pdf-overlay-surface";

  const layer = document.createElement("div");
  layer.className = "pdf-annotation-layer";

  overlay.appendChild(layer);
  stage.appendChild(image);
  stage.appendChild(overlay);
  shell.appendChild(label);
  shell.appendChild(stage);
  pdfEditorPages.appendChild(shell);

  bindPageInteractions(layer, pageNumber - 1);
  state.pageViews.push({ pageNumber, overlay, layer });
}

function renderPdfPages(pageSizes) {
  state.pageViews = [];
  pdfEditorPages.innerHTML = "";
  pageSizes.forEach((pageSize, index) => {
    if ((state.file?.type || "").startsWith("image/")) {
      buildImageFrame(index + 1, pageSize);
    } else {
      buildPageFrame(index + 1, pageSize);
    }
  });
  renderAnnotations();
}

async function uploadPdfForEditor(file) {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE_URL}/editor/upload-pdf`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || "Could not prepare the form editor file.");
  }

  return response.json();
}

async function handleEditorFile(file) {
  const lowerName = file?.name?.toLowerCase() || "";
  if (!file || ![".pdf", ".jpg", ".jpeg", ".png"].some((ext) => lowerName.endsWith(ext))) {
    setEditorError("Please choose a PDF, JPG, JPEG, or PNG file.");
    return;
  }

  clearPreviewUrl();
  setEditorError("");
  setTranslationState();
  state.file = file;
  state.annotations = [];
  state.uploadId = "";
  state.pageSizes = [];
  state.previewUrl = URL.createObjectURL(file);
  editorFileName.textContent = file.name;
  exportEditorButton.disabled = true;
  refreshRenderedPreviewButton.disabled = true;
  translatePdfButton.disabled = true;
  setRenderedPreviewState("");
  updateStatus("Uploading file for editor...");

  try {
    const uploadPayload = await uploadPdfForEditor(file);
    state.uploadId = uploadPayload.upload_id;
    state.pageSizes = uploadPayload.page_sizes || [];
    renderPdfPages(state.pageSizes);
    exportEditorButton.disabled = false;
    refreshRenderedPreviewButton.disabled = false;
    translatePdfButton.disabled = false;
    updateStatus("File is ready. Choose a tool and work directly on the page overlays.");
    scheduleRenderedPreview();
  } catch (error) {
    setEditorError(error.message || "Unable to open the form editor.");
    setRenderedPreviewState("");
    updateStatus("Could not load the form editor.");
  }
}

function buildEditorExportPayload() {
  return {
    upload_id: state.uploadId,
    original_filename: state.file.name,
    annotations: state.annotations.map((annotation) => ({
      page: annotation.page,
      type: annotation.type,
      content: annotation.content || "",
      font_size: annotation.fontSize || 16,
      signature_data: annotation.signatureData || "",
      x_ratio: annotation.xRatio,
      y_ratio: annotation.yRatio,
      width_ratio: annotation.widthRatio,
      height_ratio: annotation.heightRatio,
    })),
  };
}

async function renderEditedPdfPreview(openInNewTab = false) {
  if (!state.uploadId || !state.file) {
    setEditorError("Open a file before exporting.");
    return;
  }

  setEditorError("");
  updateStatus(openInNewTab ? "Exporting your edited PDF..." : "Rendering backend preview...");
  if (openInNewTab) {
    exportEditorButton.disabled = true;
  } else {
    refreshRenderedPreviewButton.disabled = true;
  }
  setRenderedPreviewState("Rendering backend preview...");

  try {
    const response = await fetch(`${API_BASE_URL}/editor/export-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(buildEditorExportPayload()),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Could not export the edited PDF.");
    }

    const payload = await response.json();
    const pdfUrl = `${API_BASE_URL}${payload.pdf_url}`;
    setRenderedPreviewState(
      "Rendered preview updated using the same backend PDF engine as export.",
      pdfUrl,
    );
    updateStatus(openInNewTab ? "Edited PDF is ready." : "Rendered preview is up to date.");
    if (openInNewTab) {
      window.open(pdfUrl, "_blank", "noopener");
    }
  } catch (error) {
    setEditorError(error.message || "Could not export the edited PDF.");
    updateStatus(openInNewTab ? "Export failed." : "Rendered preview failed.");
  } finally {
    exportEditorButton.disabled = false;
    refreshRenderedPreviewButton.disabled = false;
  }
}

function scheduleRenderedPreview() {
  if (!state.uploadId) {
    return;
  }

  if (renderedPreviewTimer) {
    window.clearTimeout(renderedPreviewTimer);
  }

  renderedPreviewTimer = window.setTimeout(() => {
    renderEditedPdfPreview(false);
  }, 500);
}

async function translatePdfForReading() {
  if (!state.uploadId) {
    setEditorError("Upload a PDF first before using translation.");
    return;
  }

  setEditorError("");
  setTranslationState("Translating PDF text for reading...");
  translatePdfButton.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/editor/translate-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        upload_id: state.uploadId,
        language: editorTranslationLanguage.value,
      }),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Could not translate the PDF text.");
    }

    const payload = await response.json();
    setTranslationState(`Showing ${payload.language} reading translation.`, payload.translated_text || "");
  } catch (error) {
    setTranslationState(error.message || "Could not translate the PDF text.");
  } finally {
    translatePdfButton.disabled = false;
  }
}

function getCanvasPoint(event) {
  const rect = signatureCanvas.getBoundingClientRect();
  const scaleX = signatureCanvas.width / rect.width;
  const scaleY = signatureCanvas.height / rect.height;
  return {
    x: (event.clientX - rect.left) * scaleX,
    y: (event.clientY - rect.top) * scaleY,
  };
}

function startSignature(event) {
  isSigning = true;
  const point = getCanvasPoint(event);
  signatureContext.beginPath();
  signatureContext.moveTo(point.x, point.y);
}

function moveSignature(event) {
  if (!isSigning) {
    return;
  }
  const point = getCanvasPoint(event);
  signatureContext.lineTo(point.x, point.y);
  signatureContext.strokeStyle = "#111827";
  signatureContext.lineWidth = 2.4;
  signatureContext.lineCap = "round";
  signatureContext.stroke();
}

function stopSignature() {
  isSigning = false;
  signatureContext.closePath();
}

editorFileInput.addEventListener("change", (event) => {
  const file = event.target.files?.[0];
  if (file) {
    handleEditorFile(file);
  }
});

openEditorPdfButton.addEventListener("click", () => {
  editorFileInput.click();
});

toolButtons.forEach((button) => {
  button.addEventListener("click", () => setTool(button.dataset.tool));
});

undoAnnotationButton.addEventListener("click", () => {
  state.annotations.pop();
  renderAnnotations();
  scheduleRenderedPreview();
});

clearAnnotationsButton.addEventListener("click", () => {
  state.annotations = [];
  renderAnnotations();
  scheduleRenderedPreview();
});

exportEditorButton.addEventListener("click", () => renderEditedPdfPreview(true));
refreshRenderedPreviewButton.addEventListener("click", () => renderEditedPdfPreview(false));
translatePdfButton.addEventListener("click", translatePdfForReading);
clearTranslationButton.addEventListener("click", () => setTranslationState());

signatureCanvas.addEventListener("pointerdown", startSignature);
signatureCanvas.addEventListener("pointermove", moveSignature);
signatureCanvas.addEventListener("pointerup", stopSignature);
signatureCanvas.addEventListener("pointerleave", stopSignature);

clearEditorSignature.addEventListener("click", () => {
  signatureContext.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
  state.signatureData = "";
  editorSignatureStatus.textContent = "Draw a signature, save it, then click on the PDF where you want it.";
});

saveEditorSignature.addEventListener("click", () => {
  state.signatureData = signatureCanvas.toDataURL("image/png");
  editorSignatureStatus.textContent = "Signature saved. Switch to the signature tool and click on the PDF to place it.";
  setTool("signature");
});

window.addEventListener("beforeunload", clearPreviewUrl);
setTranslationState();
setTool("text");
