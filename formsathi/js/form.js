const API_BASE_URL = "http://127.0.0.1:8000";
const dynamicForm = document.getElementById("dynamicForm");
const languageSelector = document.getElementById("languageSelector");
const continueButton = document.getElementById("continueButton");

const originalFields = JSON.parse(localStorage.getItem("formsathiOriginalFields") || "[]");
let displayedFields = JSON.parse(localStorage.getItem("formsathiFields") || "[]");
let savedFormData = JSON.parse(localStorage.getItem("formsathiFormData") || "{}");
const savedLanguage = localStorage.getItem("formsathiLanguage") || "English";

if (!originalFields.length) {
  window.location.href = "upload.html";
}

languageSelector.value = savedLanguage;

function buildInput(field, index) {
  const wrapper = document.createElement("div");
  wrapper.className = `field-group ${field.type === "textarea" ? "full-width" : ""}`;

  const label = document.createElement("label");
  label.textContent = field.label;
  label.htmlFor = `field-${index}`;

  const input = field.type === "textarea" ? document.createElement("textarea") : document.createElement("input");
  if (field.type !== "textarea") {
    input.type = ["text", "date", "number", "email"].includes(field.type) ? field.type : "text";
  }

  input.id = `field-${index}`;
  input.name = field.original_label || field.label;
  input.placeholder = `Enter ${field.label}`;
  input.value = savedFormData[input.name] || "";
  input.addEventListener("input", () => {
    savedFormData[input.name] = input.value;
    localStorage.setItem("formsathiFormData", JSON.stringify(savedFormData));
  });

  wrapper.append(label, input);
  return wrapper;
}

function renderForm(fields) {
  dynamicForm.innerHTML = "";
  fields.forEach((field, index) => dynamicForm.appendChild(buildInput(field, index)));
}

async function translateFields(language) {
  const response = await fetch(`${API_BASE_URL}/translate-fields`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      language,
      fields: originalFields.map((field) => ({
        ...field,
        label: field.original_label || field.label,
      })),
    }),
  });

  if (!response.ok) {
    throw new Error("Unable to translate labels.");
  }

  const translated = await response.json();
  displayedFields = translated.fields || [];
  localStorage.setItem("formsathiFields", JSON.stringify(displayedFields));
}

languageSelector.addEventListener("change", async (event) => {
  const language = event.target.value;
  localStorage.setItem("formsathiLanguage", language);

  try {
    await translateFields(language);
  } catch (error) {
    displayedFields = originalFields;
  }

  renderForm(displayedFields);
});

continueButton.addEventListener("click", () => {
  localStorage.setItem("formsathiFormData", JSON.stringify(savedFormData));
  window.location.href = "signature.html";
});

renderForm(displayedFields);
