const API_BASE_URL = "http://127.0.0.1:8000";

const placementPages = document.getElementById("adjustPlacementPages");
const placementStatus = document.getElementById("adjustPlacementStatus");
const placementError = document.getElementById("adjustPlacementError");
const resetPlacementButton = document.getElementById("resetPlacementButton");
const continueToPreviewButton = document.getElementById("continueToPreviewButton");

const uploadResponse = JSON.parse(localStorage.getItem("formsathiUploadResponse") || "null");
let fields = JSON.parse(localStorage.getItem("formsathiFields") || "[]");
const formData = JSON.parse(localStorage.getItem("formsathiFormData") || "{}");
const signature = localStorage.getItem("formsathiSignature") || "";

const initialFields = JSON.parse(JSON.stringify(fields || []));
const initialSignatureAnchor = uploadResponse?.signature_anchor
  ? JSON.parse(JSON.stringify(uploadResponse.signature_anchor))
  : null;

const state = {
  metadata: null,
  pageViews: [],
  draggedItem: null,
  dragOffset: null,
  signatureAnchor: uploadResponse?.signature_anchor
    ? JSON.parse(JSON.stringify(uploadResponse.signature_anchor))
    : null,
};

if (!uploadResponse || !fields.length || !signature) {
  window.location.href = "upload.html";
}

function setPlacementError(message = "") {
  placementError.textContent = message;
  placementError.classList.toggle("hidden", !message);
}

function getSourceUrl() {
  return `${API_BASE_URL}/upload-source/${uploadResponse.upload_id}`;
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

function getPageSize(pageIndex) {
  return state.metadata?.page_sizes?.[pageIndex] || state.metadata?.page_sizes?.[0] || { width: 595.27, height: 841.89 };
}

function createTextNode(fieldIndex, field, overlay, pageSize) {
  const originalLabel = field.original_label || field.label || "";
  const value = `${formData[originalLabel] || ""}`.trim();
  if (!value || !field.position) {
    return null;
  }

  const position = field.position;
  const widthRatio = Number(position.width || 180) / pageSize.width;
  const heightRatio = Math.max(Number(position.height || 12) * 2.1, 28) / pageSize.height;
  const left = (Number(position.x || 0) / pageSize.width) * overlay.clientWidth;
  const top = ((pageSize.height - Number(position.y || 0) - Number(position.height || 12)) / pageSize.height) * overlay.clientHeight;

  const node = document.createElement("div");
  node.className = "editor-annotation text draggable placement-annotation";
  node.dataset.annotationType = "field";
  node.dataset.fieldIndex = String(fieldIndex);
  node.style.left = `${left}px`;
  node.style.top = `${top}px`;
  node.style.width = `${widthRatio * overlay.clientWidth}px`;
  node.style.height = `${Math.max(heightRatio * overlay.clientHeight, 28)}px`;
  node.textContent = value;
  return node;
}

function createSignatureNode(overlay, pageIndex, pageSize) {
  if (!signature || !state.signatureAnchor || Number(state.signatureAnchor.page || 0) !== pageIndex) {
    return null;
  }

  const widthRatio = Number(state.signatureAnchor.width || 150) / pageSize.width;
  const heightRatio = Math.max(Number(state.signatureAnchor.height || 36) * 1.6, 46) / pageSize.height;
  const left = (Number(state.signatureAnchor.x || 0) / pageSize.width) * overlay.clientWidth;
  const top = ((pageSize.height - Number(state.signatureAnchor.y || 0) - Number(state.signatureAnchor.height || 36)) / pageSize.height) * overlay.clientHeight;

  const node = document.createElement("div");
  node.className = "editor-annotation signature draggable placement-annotation";
  node.dataset.annotationType = "signature";
  node.style.left = `${left}px`;
  node.style.top = `${top}px`;
  node.style.width = `${Math.max(widthRatio * overlay.clientWidth, 120)}px`;
  node.style.height = `${Math.max(heightRatio * overlay.clientHeight, 46)}px`;

  const image = document.createElement("img");
  image.src = signature;
  image.alt = "Placed signature";
  node.appendChild(image);
  return node;
}

function renderAnnotations() {
  state.pageViews.forEach(({ pageIndex, layer, overlay }) => {
    layer.innerHTML = "";
    const pageSize = getPageSize(pageIndex);

    fields.forEach((field, fieldIndex) => {
      const fieldPage = Number(field.position?.page || 0);
      if (fieldPage !== pageIndex) {
        return;
      }
      const node = createTextNode(fieldIndex, field, overlay, pageSize);
      if (node) {
        layer.appendChild(node);
      }
    });

    const signatureNode = createSignatureNode(overlay, pageIndex, pageSize);
    if (signatureNode) {
      layer.appendChild(signatureNode);
    }
  });
}

function updateDraggedField(fieldIndex, overlay, pageSize, point, offset) {
  const field = fields[fieldIndex];
  if (!field?.position) {
    return;
  }

  const fieldWidth = Number(field.position.width || 180);
  const fieldHeight = Number(field.position.height || 12);
  const widthPx = (fieldWidth / pageSize.width) * point.width;
  const heightPx = Math.max((fieldHeight / pageSize.height) * point.height * 2.1, 28);
  const nextLeft = Math.min(Math.max(point.x - offset.x, 0), Math.max(point.width - widthPx, 0));
  const nextTop = Math.min(Math.max(point.y - offset.y, 0), Math.max(point.height - heightPx, 0));

  field.position.x = Number(((nextLeft / point.width) * pageSize.width).toFixed(2));
  field.position.y = Number((pageSize.height - ((nextTop / point.height) * pageSize.height) - fieldHeight).toFixed(2));
}

function updateDraggedSignature(overlay, pageSize, point, offset) {
  if (!state.signatureAnchor) {
    return;
  }

  const signatureWidth = Number(state.signatureAnchor.width || 150);
  const signatureHeight = Number(state.signatureAnchor.height || 36);
  const widthPx = Math.max((signatureWidth / pageSize.width) * point.width, 120);
  const heightPx = Math.max((signatureHeight / pageSize.height) * point.height * 1.6, 46);
  const nextLeft = Math.min(Math.max(point.x - offset.x, 0), Math.max(point.width - widthPx, 0));
  const nextTop = Math.min(Math.max(point.y - offset.y, 0), Math.max(point.height - heightPx, 0));

  state.signatureAnchor.x = Number(((nextLeft / point.width) * pageSize.width).toFixed(2));
  state.signatureAnchor.y = Number((pageSize.height - ((nextTop / point.height) * pageSize.height) - signatureHeight).toFixed(2));
}

function bindPageInteractions(layer, pageIndex) {
  layer.addEventListener("pointerdown", (event) => {
    const draggableNode = event.target.closest(".editor-annotation.draggable");
    if (!draggableNode) {
      return;
    }

    const point = getPointWithinElement(event, layer);
    state.draggedItem = {
      type: draggableNode.dataset.annotationType,
      fieldIndex: draggableNode.dataset.fieldIndex ? Number(draggableNode.dataset.fieldIndex) : null,
      pageIndex,
    };
    state.dragOffset = {
      x: point.x - draggableNode.offsetLeft,
      y: point.y - draggableNode.offsetTop,
    };
    layer.setPointerCapture(event.pointerId);
  });

  layer.addEventListener("pointermove", (event) => {
    if (!state.draggedItem || state.draggedItem.pageIndex !== pageIndex) {
      return;
    }

    const point = getPointWithinElement(event, layer);
    const pageSize = getPageSize(pageIndex);
    if (state.draggedItem.type === "field" && state.draggedItem.fieldIndex !== null) {
      updateDraggedField(state.draggedItem.fieldIndex, layer, pageSize, point, state.dragOffset);
    } else if (state.draggedItem.type === "signature") {
      updateDraggedSignature(layer, pageSize, point, state.dragOffset);
    }
    renderAnnotations();
  });

  layer.addEventListener("pointerup", (event) => {
    if (!state.draggedItem || state.draggedItem.pageIndex !== pageIndex) {
      return;
    }

    const point = getPointWithinElement(event, layer);
    const pageSize = getPageSize(pageIndex);
    if (state.draggedItem.type === "field" && state.draggedItem.fieldIndex !== null) {
      updateDraggedField(state.draggedItem.fieldIndex, layer, pageSize, point, state.dragOffset);
    } else if (state.draggedItem.type === "signature") {
      updateDraggedSignature(layer, pageSize, point, state.dragOffset);
    }

    state.draggedItem = null;
    state.dragOffset = null;
    renderAnnotations();
    layer.releasePointerCapture(event.pointerId);
  });
}

function buildPdfPage(pageIndex, pageSize) {
  const shell = document.createElement("article");
  shell.className = "pdf-editor-page";

  const label = document.createElement("div");
  label.className = "pdf-page-label";
  label.textContent = `Page ${pageIndex + 1}`;

  const ratio = pageSize.height / pageSize.width;
  const width = Math.min(760, Math.max(320, placementPages.clientWidth - 40 || 760));
  const height = Math.max(width * ratio, 420);

  const stage = document.createElement("div");
  stage.className = "pdf-page-stage";
  stage.style.width = `${width}px`;
  stage.style.height = `${height}px`;

  const frame = document.createElement("iframe");
  frame.className = "pdf-page-frame";
  frame.src = `${getSourceUrl()}#page=${pageIndex + 1}&toolbar=0&navpanes=0&scrollbar=0&view=FitH`;
  frame.title = `Original PDF page ${pageIndex + 1}`;

  const overlay = document.createElement("div");
  overlay.className = "pdf-overlay-surface";

  const layer = document.createElement("div");
  layer.className = "pdf-annotation-layer";

  overlay.appendChild(layer);
  stage.appendChild(frame);
  stage.appendChild(overlay);
  shell.appendChild(label);
  shell.appendChild(stage);
  placementPages.appendChild(shell);
  bindPageInteractions(layer, pageIndex);
  state.pageViews.push({ pageIndex, overlay, layer });
}

function buildImagePage(pageSize) {
  const shell = document.createElement("article");
  shell.className = "pdf-editor-page";

  const label = document.createElement("div");
  label.className = "pdf-page-label";
  label.textContent = "Uploaded Image";

  const ratio = pageSize.height / pageSize.width;
  const width = Math.min(760, Math.max(320, placementPages.clientWidth - 40 || 760));
  const height = Math.max(width * ratio, 420);

  const stage = document.createElement("div");
  stage.className = "pdf-page-stage";
  stage.style.width = `${width}px`;
  stage.style.height = `${height}px`;

  const image = document.createElement("img");
  image.className = "pdf-page-image";
  image.src = getSourceUrl();
  image.alt = "Original uploaded form";

  const overlay = document.createElement("div");
  overlay.className = "pdf-overlay-surface";

  const layer = document.createElement("div");
  layer.className = "pdf-annotation-layer";

  overlay.appendChild(layer);
  stage.appendChild(image);
  stage.appendChild(overlay);
  shell.appendChild(label);
  shell.appendChild(stage);
  placementPages.appendChild(shell);
  bindPageInteractions(layer, 0);
  state.pageViews.push({ pageIndex: 0, overlay, layer });
}

function renderSourcePages() {
  state.pageViews = [];
  placementPages.innerHTML = "";

  if (state.metadata.source_type === "pdf") {
    state.metadata.page_sizes.forEach((pageSize, pageIndex) => buildPdfPage(pageIndex, pageSize));
  } else {
    buildImagePage(state.metadata.page_sizes[0]);
  }

  renderAnnotations();
}

function ensureSignatureAnchor() {
  if (state.signatureAnchor || !state.metadata?.page_sizes?.length) {
    return;
  }

  const lastPageIndex = state.metadata.page_sizes.length - 1;
  const lastPage = state.metadata.page_sizes[lastPageIndex];
  state.signatureAnchor = {
    page: lastPageIndex,
    x: Math.max(lastPage.width - 180, 24),
    y: 72,
    width: 150,
    height: 36,
  };
}

async function loadMetadata() {
  if (uploadResponse.page_sizes?.length && uploadResponse.source_type) {
    return {
      source_type: uploadResponse.source_type,
      page_sizes: uploadResponse.page_sizes,
      page_count: uploadResponse.page_count || uploadResponse.page_sizes.length,
    };
  }

  const response = await fetch(`${API_BASE_URL}/upload-meta/${uploadResponse.upload_id}`);
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw new Error(errorPayload.detail || "Could not inspect the uploaded form.");
  }
  return response.json();
}

function persistPlacementAndContinue() {
  localStorage.setItem("formsathiFields", JSON.stringify(fields));
  const nextUploadResponse = {
    ...uploadResponse,
    signature_anchor: state.signatureAnchor,
    source_type: state.metadata?.source_type || uploadResponse.source_type,
    page_count: state.metadata?.page_count || uploadResponse.page_count,
    page_sizes: state.metadata?.page_sizes || uploadResponse.page_sizes,
  };
  localStorage.setItem("formsathiUploadResponse", JSON.stringify(nextUploadResponse));
  window.location.href = "preview.html";
}

function resetPlacement() {
  fields = JSON.parse(JSON.stringify(initialFields));
  state.signatureAnchor = initialSignatureAnchor ? JSON.parse(JSON.stringify(initialSignatureAnchor)) : null;
  renderAnnotations();
}

async function initializePlacementEditor() {
  try {
    setPlacementError("");
    placementStatus.textContent = "Loading your original form...";
    state.metadata = await loadMetadata();
    ensureSignatureAnchor();
    renderSourcePages();
    placementStatus.textContent = "Drag any filled value or the signature to fine-tune the placement.";
  } catch (error) {
    placementStatus.textContent = "Could not load the placement step.";
    setPlacementError(error.message || "Unable to open the placement adjustment view.");
  }
}

resetPlacementButton.addEventListener("click", resetPlacement);
continueToPreviewButton.addEventListener("click", persistPlacementAndContinue);

window.addEventListener("resize", () => {
  if (state.metadata) {
    renderSourcePages();
  }
});

initializePlacementEditor();
