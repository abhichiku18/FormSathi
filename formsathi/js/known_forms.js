const API_BASE_URL = "http://127.0.0.1:8000";

const knownFormsGrid = document.getElementById("knownFormsGrid");
const knownFormsLanguage = document.getElementById("knownFormsLanguage");
const knownFormsStatus = document.getElementById("knownFormsStatus");
const knownFormsError = document.getElementById("knownFormsError");
const CUSTOM_TEMPLATE_STORAGE_KEY = "formsathiCustomKnownTemplates";

const savedLanguage = localStorage.getItem("formsathiLanguage") || "English";
knownFormsLanguage.value = savedLanguage;

function resetStoredSession() {
  [
    "formsathiUploadResponse",
    "formsathiFields",
    "formsathiOriginalFields",
    "formsathiLanguage",
    "formsathiFormData",
    "formsathiSignature",
    "formsathiGeneratedPdf",
  ].forEach((key) => localStorage.removeItem(key));
}

function setError(message = "") {
  knownFormsError.textContent = message;
  knownFormsError.classList.toggle("hidden", !message);
}

async function openTemplate(item) {
  setError("");
  knownFormsStatus.textContent = `Preparing ${item.name}...`;

  try {
    const isCustom = item.kind === "custom";
    const url = isCustom ? `${API_BASE_URL}/known-forms/custom/start` : `${API_BASE_URL}/known-forms/${item.id}/start`;
    const body = isCustom
      ? {
          form_title: item.name,
          blocks: item.blocks,
          language: knownFormsLanguage.value,
        }
      : {
          language: knownFormsLanguage.value,
        };

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Could not open the known form template.");
    }

    const payload = await response.json();
    localStorage.setItem("formsathiUploadResponse", JSON.stringify(payload));
    localStorage.setItem("formsathiOriginalFields", JSON.stringify(payload.detected_fields || []));
    localStorage.setItem("formsathiFields", JSON.stringify(payload.detected_fields || []));
    localStorage.setItem("formsathiLanguage", knownFormsLanguage.value);
    localStorage.setItem("formsathiFormData", JSON.stringify({}));
    window.location.href = "form_editor.html";
  } catch (error) {
    setError(error.message || "Could not open the known form template.");
    knownFormsStatus.textContent = "Choose a known form for exact placement.";
  }
}

function renderKnownForms(items, customTemplates) {
  knownFormsGrid.innerHTML = "";

  const addCard = document.createElement("article");
  addCard.className = "known-form-card add-template-card";
  addCard.innerHTML = `
    <div class="plus-badge">+</div>
    <h3>Add Custom Template</h3>
    <p class="muted">Create your own reusable form template and save it for exact placement later.</p>
    <button class="primary-button" type="button">Create Template</button>
  `;
  addCard.querySelector("button").addEventListener("click", () => {
    window.location.href = "create_form.html";
  });
  knownFormsGrid.appendChild(addCard);

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "known-form-card";
    card.innerHTML = `
      <p class="eyebrow">Exact Placement Template</p>
      <h3>${item.name}</h3>
      <p class="muted">${item.purpose}</p>
      <p class="muted">${item.description}</p>
      <button class="primary-button" type="button">Use Template</button>
    `;

    card.querySelector("button").addEventListener("click", () => openTemplate(item));

    knownFormsGrid.appendChild(card);
  });

  customTemplates.forEach((item) => {
    const card = document.createElement("article");
    card.className = "known-form-card custom-template-card";
    card.innerHTML = `
      <p class="eyebrow">Your Saved Template</p>
      <h3>${item.name}</h3>
      <p class="muted">${item.purpose}</p>
      <p class="muted">${item.description}</p>
      <button class="primary-button" type="button">Use Template</button>
    `;
    card.querySelector("button").addEventListener("click", () => openTemplate({ ...item, kind: "custom" }));
    knownFormsGrid.appendChild(card);
  });
}

async function loadKnownForms() {
  knownFormsStatus.textContent = "Loading template forms...";
  setError("");

  try {
    const response = await fetch(`${API_BASE_URL}/known-forms`);
    if (!response.ok) {
      throw new Error("Unable to load known forms.");
    }
    const payload = await response.json();
    const customTemplates = JSON.parse(localStorage.getItem(CUSTOM_TEMPLATE_STORAGE_KEY) || "[]");
    renderKnownForms(payload.items || [], customTemplates);
    knownFormsStatus.textContent = "Choose a template to start filling with exact placement.";
  } catch (error) {
    setError(error.message || "Unable to load known forms.");
    knownFormsStatus.textContent = "Could not load template forms.";
  }
}

knownFormsLanguage.addEventListener("change", () => {
  localStorage.setItem("formsathiLanguage", knownFormsLanguage.value);
});

resetStoredSession();
loadKnownForms();
