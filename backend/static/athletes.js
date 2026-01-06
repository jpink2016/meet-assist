document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("athletes-body");

  const addBtn = document.getElementById("addBtn");
  const addStatus = document.getElementById("addStatus");

  const showInactive = document.getElementById("showInactive");

  // Form elements
  const teamIdEl = document.getElementById("teamId");
  const varsityEl = document.getElementById("varsityYN");
  const firstEl = document.getElementById("firstName");
  const lastEl = document.getElementById("lastName");
  const availEl = document.getElementById("availableYN");
  const expectedEl = document.getElementById("expectedReturn");
  const gradEl = document.getElementById("gradYear");

  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function isValidNewAthlete() {
    const first = firstEl.value.trim();
    const last = lastEl.value.trim();
    const teamId = Number(teamIdEl.value);

    if (!first || !last) return false;
    if (!Number.isInteger(teamId) || teamId < 1) return false;

    // grad year optional; if provided, validate range
    const grad = gradEl.value.trim();
    if (grad !== "") {
      const gy = Number(grad);
      if (!Number.isInteger(gy) || gy < 2000 || gy > 2100) return false;
    }

    // varsity/available are selects, so always valid
    return true;
  }

  function refreshAddButtonState() {
    addBtn.disabled = !isValidNewAthlete();
  }

  async function fetchAthletes() {
    const include = showInactive.checked ? "true" : "false";
    const res = await fetch(`/api/athletes?include_inactive=${include}`);
    return await res.json();
  }

  async function loadAthletes() {
    const athletes = await fetchAthletes();

    tbody.innerHTML = "";
    for (const a of athletes) {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${a.athlete_id}</td>

        <td>
          <input data-id="${a.athlete_id}" data-field="team_id" value="${a.team_id ?? ""}" size="6" />
        </td>

        <td>
          <select data-id="${a.athlete_id}" data-field="varsity_yn">
            <option value="Y" ${a.varsity_yn === "Y" ? "selected" : ""}>Y</option>
            <option value="N" ${a.varsity_yn === "N" ? "selected" : ""}>N</option>
          </select>
        </td>

        <td>
          <input data-id="${a.athlete_id}" data-field="first_name" value="${escapeHtml(a.first_name)}" />
        </td>

        <td>
          <input data-id="${a.athlete_id}" data-field="last_name" value="${escapeHtml(a.last_name)}" />
        </td>

        <td>
          <select data-id="${a.athlete_id}" data-field="available_yn">
            <option value="Y" ${a.available_yn === "Y" ? "selected" : ""}>Y</option>
            <option value="N" ${a.available_yn === "N" ? "selected" : ""}>N</option>
          </select>
        </td>

        <td>
          <input type="date" data-id="${a.athlete_id}" data-field="expected_return"
            value="${escapeHtml(a.expected_return || "")}" />
        </td>

        <td>
          <input data-id="${a.athlete_id}" data-field="grad_year" value="${a.grad_year ?? ""}" size="6" />
        </td>

        <td class="status" data-status-for="${a.athlete_id}"></td>
      `;

      // If athlete is inactive, lightly flag the row (no extra CSS file needed)
      if (a.is_active === "N") {
        tr.style.opacity = "0.55";
      }

      tbody.appendChild(tr);
    }
  }

  async function createAthlete(payload) {
    const res = await fetch("/api/athletes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Create failed");
    }
    return await res.json();
  }

  async function patchAthlete(id, payload) {
    const res = await fetch(`/api/athletes/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Update failed");
    }
    return await res.json();
  }

  // Add athlete (top form)
  addBtn.addEventListener("click", async () => {
    if (!isValidNewAthlete()) return;

    const first = firstEl.value.trim();
    const last = lastEl.value.trim();

    const payload = {
      team_id: teamIdEl.value,
      varsity_yn: varsityEl.value,
      first_name: first,
      last_name: last,
      available_yn: availEl.value,
    };

    // only include optional fields if provided
    if (expectedEl.value) payload.expected_return = expectedEl.value;
    if (gradEl.value.trim()) payload.grad_year = gradEl.value.trim();

    try {
      addStatus.textContent = "adding…";
      await createAthlete(payload);

      // clear only the text fields + optionals; keep defaults for dropdowns/team
      firstEl.value = "";
      lastEl.value = "";
      expectedEl.value = "";
      gradEl.value = "";

      addStatus.textContent = "added";
      setTimeout(() => (addStatus.textContent = ""), 800);

      refreshAddButtonState();
      await loadAthletes();
    } catch (err) {
      addStatus.textContent = "error";
      alert(err.message);
      refreshAddButtonState();
    }
  });

  // Enter to submit (only when valid)
  lastEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !addBtn.disabled) {
      e.preventDefault();
      addBtn.click();
    }
  });

  // Inline edit save (event delegation)
  tbody.addEventListener("change", async (e) => {
    const el = e.target;
    const id = el.dataset.id;
    const field = el.dataset.field;
    if (!id || !field) return;

    const statusCell = document.querySelector(`[data-status-for="${id}"]`);
    const value = el.value;

    try {
      statusCell.textContent = "saving…";
      await patchAthlete(id, { [field]: value });
      statusCell.textContent = "saved";
      setTimeout(() => (statusCell.textContent = ""), 800);
    } catch (err) {
      statusCell.textContent = "error";
      alert(err.message);
      await loadAthletes(); // revert UI to DB truth
    }
  });

  // Validate form & refresh button state on inputs
  [
    teamIdEl, varsityEl, firstEl, lastEl, availEl, expectedEl, gradEl
  ].forEach((el) => {
    el.addEventListener("input", refreshAddButtonState);
    el.addEventListener("change", refreshAddButtonState);
  });

  showInactive.addEventListener("change", loadAthletes);

  // initial
  refreshAddButtonState();
  loadAthletes();
});
