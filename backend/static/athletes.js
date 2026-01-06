
document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("athletes-body");

  const addBtn = document.getElementById("addBtn");
  const addStatus = document.getElementById("addStatus");
  const showInactive = document.getElementById("showInactive");

  // Form elements
  const teamSelect = document.getElementById("teamSelect");
  const eventGroupSelect = document.getElementById("eventGroupSelect");
  const varsityEl = document.getElementById("varsityYN");
  const firstEl = document.getElementById("firstName");
  const lastEl = document.getElementById("lastName");
  const genderSelect = document.getElementById("genderSelect");
  const availEl = document.getElementById("availableYN");
  const expectedEl = document.getElementById("expectedReturn");
  const gradEl = document.getElementById("gradYear");

  let TEAMS = [];        // [{team_id, name}]
  let EVENT_GROUPS = []; // [{event_group_id, name}]

  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function optionTags(items, idKey, labelKey, selectedId) {
    return items
      .map((it) => {
        const id = it[idKey];
        const label = it[labelKey];
        const sel = String(id) === String(selectedId) ? "selected" : "";
        return `<option value="${id}" ${sel}>${escapeHtml(label)}</option>`;
      })
      .join("");
  }

  function isValidNewAthlete() {
    const first = firstEl.value.trim();
    const last = lastEl.value.trim();

    if (!first || !last) return false;
    if (!teamSelect.value) return false;
    if (!eventGroupSelect.value) return false;

    const grad = gradEl.value.trim();
    if (grad !== "") {
      const gy = Number(grad);
      if (!Number.isInteger(gy) || gy < 2000 || gy > 2100) return false;
    }

    return true;
  }

  function refreshAddButtonState() {
    addBtn.disabled = !isValidNewAthlete();
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Request failed: ${url}`);
    return await res.json();
  }

  async function loadLookups() {
    TEAMS = await fetchJSON("/api/teams");
    EVENT_GROUPS = await fetchJSON("/api/event-groups");

    teamSelect.innerHTML = optionTags(TEAMS, "team_id", "name", TEAMS[0]?.team_id);
    eventGroupSelect.innerHTML = optionTags(EVENT_GROUPS, "event_group_id", "name", EVENT_GROUPS[0]?.event_group_id);

    refreshAddButtonState();
  }

  async function fetchAthletes() {
    const include = showInactive.checked ? "true" : "false";
    return await fetchJSON(`/api/athletes?include_inactive=${include}`);
  }

  async function loadAthletes() {
    const athletes = await fetchAthletes();

    tbody.innerHTML = "";
    for (const a of athletes) {
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${a.athlete_id}</td>

        <td>
          <select data-id="${a.athlete_id}" data-field="team_id">
            ${optionTags(TEAMS, "team_id", "name", a.team_id)}
          </select>
        </td>

        <td>
          <select data-id="${a.athlete_id}" data-field="event_group_id">
            ${optionTags(EVENT_GROUPS, "event_group_id", "name", a.event_group_id)}
          </select>
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
          <select data-id="${a.athlete_id}" data-field="gender">
            <option value="M" ${a.gender === "M" ? "selected" : ""}>M</option>
            <option value="F" ${a.gender === "F" ? "selected" : ""}>F</option>
            <option value="X" ${a.gender === "X" ? "selected" : ""}>X</option>
          </select>
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

      if (a.is_active === "N") tr.style.opacity = "0.55";

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

    const payload = {
      team_id: teamSelect.value,
      event_group_id: eventGroupSelect.value,
      varsity_yn: varsityEl.value,
      first_name: firstEl.value.trim(),
      last_name: lastEl.value.trim(),
      gender: genderSelect.value,
      available_yn: availEl.value,
    };

    if (expectedEl.value) payload.expected_return = expectedEl.value;
    if (gradEl.value.trim()) payload.grad_year = gradEl.value.trim();

    try {
      addStatus.textContent = "adding…";
      await createAthlete(payload);

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
    }
  });

  // Enter to submit from last name
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
      await loadAthletes();
    }
  });

  // Form validation wiring
  [
    teamSelect, eventGroupSelect, varsityEl, firstEl, lastEl, genderSelect, availEl, expectedEl, gradEl
  ].forEach((el) => {
    el.addEventListener("input", refreshAddButtonState);
    el.addEventListener("change", refreshAddButtonState);
  });

  showInactive.addEventListener("change", loadAthletes);

  // init
  (async () => {
    await loadLookups();
    await loadAthletes();
    refreshAddButtonState();
  })();
});
