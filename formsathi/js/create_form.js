const API_BASE_URL = "http://127.0.0.1:8000";

const BLOCK_TEMPLATES = [
  { type: "title", title: "Title", content: "Form Title" },
  { type: "meta", title: "Purpose", content: "Write the purpose of this form." },
  { type: "meta", title: "Department", content: "Department / Organization Name" },
  { type: "paragraph", title: "Description", content: "Add a short description for this form." },
  { type: "field", title: "Name", content: "" },
  { type: "field", title: "Address", content: "" },
  { type: "field", title: "Roll Number", content: "" },
  { type: "field", title: "ERP ID", content: "" },
  { type: "field", title: "Class", content: "" },
  { type: "field", title: "School", content: "" },
  { type: "field", title: "State", content: "" },
  { type: "field", title: "Country", content: "" },
  { type: "field", title: "Pin Code", content: "" },
  { type: "field", title: "Aadhaar Card", content: "" },
  { type: "signature", title: "Signature", content: "" },
  { type: "paragraph", title: "Instructions", content: "Add important instructions or notes here." },
  {
    type: "documents",
    title: "Required Documents",
    items: ["Aadhaar Card", "Address Proof"],
    content: "",
  },
];

const state = {
  blocks: [],
  selectedId: "",
};

const blockLibrary = document.getElementById("builderBlockLibrary");
const previewPage = document.getElementById("builderPreviewPage");
const editorEmpty = document.getElementById("builderEditorEmpty");
const editorPanel = document.getElementById("builderEditorPanel");
const blockTitleInput = document.getElementById("builderBlockTitle");
const blockContentInput = document.getElementById("builderBlockContent");
const documentsGroup = document.getElementById("builderDocumentsGroup");
const documentsInput = document.getElementById("builderDocumentsInput");
const moveBlockUpButton = document.getElementById("moveBlockUp");
const moveBlockDownButton = document.getElementById("moveBlockDown");
const removeBlockButton = document.getElementById("removeBlock");
const downloadButton = document.getElementById("downloadCreatedForm");
const saveTemplateButton = document.getElementById("saveCreatedTemplate");
const resetButton = document.getElementById("resetCreatedForm");
const statusNode = document.getElementById("createFormStatus");
const errorNode = document.getElementById("createFormError");
const templateNameInput = document.getElementById("templateNameInput");
const TEMPLATE_STORAGE_KEY = "formsathiCustomKnownTemplates";

function setError(message = "") {
  errorNode.textContent = message;
  errorNode.classList.toggle("hidden", !message);
}

function updateStatus(message) {
  statusNode.textContent = message;
}

function getTemplateName() {
  return templateNameInput.value.trim() || state.blocks.find((block) => block.type === "title")?.content || "Custom Form Template";
}

function createBlockFromTemplate(template) {
  return {
    id: crypto.randomUUID(),
    type: template.type,
    title: template.title,
    content: template.content || "",
    items: template.items ? [...template.items] : [],
  };
}

function getSelectedBlock() {
  return state.blocks.find((block) => block.id === state.selectedId) || null;
}

function renderBlockLibrary() {
  blockLibrary.innerHTML = "";
  BLOCK_TEMPLATES.forEach((template) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "builder-library-item";
    button.textContent = template.title;
    button.addEventListener("click", () => {
      state.blocks.push(createBlockFromTemplate(template));
      state.selectedId = state.blocks[state.blocks.length - 1].id;
      renderBuilder();
    });
    blockLibrary.appendChild(button);
  });
}

function renderPreview() {
  previewPage.innerHTML = "";

  if (!state.blocks.length) {
    const empty = document.createElement("div");
    empty.className = "builder-empty-state";
    empty.textContent = "Add blocks from the left to build your form.";
    previewPage.appendChild(empty);
    return;
  }

  state.blocks.forEach((block) => {
    const article = document.createElement("article");
    article.className = `builder-block ${block.type}`;
    article.dataset.blockId = block.id;
    article.classList.toggle("selected", block.id === state.selectedId);
    article.addEventListener("click", () => {
      state.selectedId = block.id;
      renderBuilder();
    });

    if (block.type === "title") {
      article.innerHTML = `<h1>${block.content || "Form Title"}</h1>`;
    } else if (block.type === "meta") {
      article.innerHTML = `<div class="builder-meta-row"><strong>${block.title}:</strong><span>${block.content || "Add content here"}</span></div>`;
    } else if (block.type === "paragraph") {
      article.innerHTML = `<h3>${block.title}</h3><p>${block.content || "Add content here"}</p>`;
    } else if (block.type === "documents") {
      const heading = document.createElement("h3");
      heading.textContent = block.title || "Required Documents";
      article.appendChild(heading);
      const list = document.createElement("ul");
      (block.items || []).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = item;
        list.appendChild(li);
      });
      article.appendChild(list);
    } else if (block.type === "signature") {
      article.innerHTML = `<div class="builder-field-row signature"><span>${block.title}</span><div class="builder-signature-line"></div></div>`;
    } else {
      article.innerHTML = `<div class="builder-field-row"><span>${block.title}</span><div class="builder-field-line"></div></div>`;
    }

    previewPage.appendChild(article);
  });
}

function renderEditorPanel() {
  const block = getSelectedBlock();
  editorEmpty.classList.toggle("hidden", !!block);
  editorPanel.classList.toggle("hidden", !block);

  if (!block) {
    return;
  }

  blockTitleInput.value = block.title || "";
  blockContentInput.value = block.content || "";
  documentsGroup.classList.toggle("hidden", block.type !== "documents");
  documentsInput.value = (block.items || []).join("\n");
}

function renderBuilder() {
  renderPreview();
  renderEditorPanel();
}

function updateSelectedBlock(updater) {
  const block = getSelectedBlock();
  if (!block) {
    return;
  }
  updater(block);
  renderBuilder();
}

blockTitleInput.addEventListener("input", () => {
  updateSelectedBlock((block) => {
    block.title = blockTitleInput.value;
  });
});

blockContentInput.addEventListener("input", () => {
  updateSelectedBlock((block) => {
    block.content = blockContentInput.value;
  });
});

documentsInput.addEventListener("input", () => {
  updateSelectedBlock((block) => {
    block.items = documentsInput.value
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean);
  });
});

moveBlockUpButton.addEventListener("click", () => {
  const index = state.blocks.findIndex((block) => block.id === state.selectedId);
  if (index > 0) {
    [state.blocks[index - 1], state.blocks[index]] = [state.blocks[index], state.blocks[index - 1]];
    renderBuilder();
  }
});

moveBlockDownButton.addEventListener("click", () => {
  const index = state.blocks.findIndex((block) => block.id === state.selectedId);
  if (index >= 0 && index < state.blocks.length - 1) {
    [state.blocks[index + 1], state.blocks[index]] = [state.blocks[index], state.blocks[index + 1]];
    renderBuilder();
  }
});

removeBlockButton.addEventListener("click", () => {
  state.blocks = state.blocks.filter((block) => block.id !== state.selectedId);
  state.selectedId = state.blocks[0]?.id || "";
  renderBuilder();
});

downloadButton.addEventListener("click", async () => {
  if (!state.blocks.length) {
    setError("Add at least one block before downloading the form.");
    return;
  }

  setError("");
  updateStatus("Generating your created form PDF...");

  try {
    const response = await fetch(`${API_BASE_URL}/create-form-pdf`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        form_title: state.blocks.find((block) => block.type === "title")?.content || "Created Form",
        blocks: state.blocks,
      }),
    });

    if (!response.ok) {
      const errorPayload = await response.json().catch(() => ({}));
      throw new Error(errorPayload.detail || "Could not generate the created form PDF.");
    }

    const payload = await response.json();
    window.open(`${API_BASE_URL}${payload.pdf_url}`, "_blank", "noopener");
    updateStatus("Created form PDF is ready.");
  } catch (error) {
    setError(error.message || "Could not generate the created form PDF.");
    updateStatus("Export failed.");
  }
});

resetButton.addEventListener("click", () => {
  state.blocks = [];
  state.selectedId = "";
  templateNameInput.value = "";
  setError("");
  updateStatus("Build your form on the right, then export it.");
  renderBuilder();
});

saveTemplateButton.addEventListener("click", () => {
  if (!state.blocks.length) {
    setError("Add blocks before saving a template.");
    return;
  }

  const name = getTemplateName();
  const templates = JSON.parse(localStorage.getItem(TEMPLATE_STORAGE_KEY) || "[]");
  const template = {
    id: crypto.randomUUID(),
    name,
    purpose: "Custom reusable form template",
    description: "Saved from the Create Form builder for future exact-placement filling.",
    blocks: state.blocks,
  };
  templates.push(template);
  localStorage.setItem(TEMPLATE_STORAGE_KEY, JSON.stringify(templates));
  setError("");
  updateStatus(`Template "${name}" saved. Open Known Forms to reuse it later.`);
});

renderBlockLibrary();
renderBuilder();
