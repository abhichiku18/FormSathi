const API_BASE_URL = "http://127.0.0.1:8000";
const checklistGrid = document.getElementById("checklistGrid");
const checklistSearch = document.getElementById("checklistSearch");

let checklistItems = [];

function renderChecklist(items) {
  checklistGrid.innerHTML = "";

  if (!items.length) {
    checklistGrid.innerHTML = '<section class="card"><p class="muted">No checklist matched your search.</p></section>';
    return;
  }

  items.forEach((item) => {
    const card = document.createElement("article");
    card.className = "checklist-card";
    card.innerHTML = `
      <p class="eyebrow">Document Checklist</p>
      <h3>${item.name}</h3>
      <p class="checklist-meta"><strong>Purpose:</strong> ${item.purpose}</p>
      <p class="checklist-meta"><strong>Benefit:</strong> ${item.benefit}</p>
      <p class="checklist-meta"><strong>Eligibility:</strong></p>
      <ul class="checklist-list">${item.eligibility.map((entry) => `<li>${entry}</li>`).join("")}</ul>
      <p class="checklist-meta" style="margin-top: 14px;"><strong>Required Documents:</strong></p>
      <ul class="checklist-list">${item.documents.map((entry) => `<li>${entry}</li>`).join("")}</ul>
      ${item.official_url ? `<div class="checklist-actions"><a class="primary-button" href="${item.official_url}" target="_blank" rel="noopener noreferrer">Official Website</a></div>` : ""}
    `;
    checklistGrid.appendChild(card);
  });
}

async function loadChecklists() {
  const response = await fetch(`${API_BASE_URL}/document-checklists`);
  const payload = await response.json();
  checklistItems = payload.items || [];
  renderChecklist(checklistItems);
}

checklistSearch?.addEventListener("input", (event) => {
  const query = event.target.value.trim().toLowerCase();
  if (!query) {
    renderChecklist(checklistItems);
    return;
  }

  const filtered = checklistItems.filter((item) => {
    const haystack = [
      item.name,
      item.purpose,
      item.benefit,
      ...(item.eligibility || []),
      ...(item.documents || []),
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  renderChecklist(filtered);
});

loadChecklists().catch(() => {
  checklistGrid.innerHTML = '<section class="card"><p class="error-text">Unable to load document checklists right now.</p></section>';
});
