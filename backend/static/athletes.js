document.addEventListener("DOMContentLoaded", () => {

  const tbodyM = document.getElementById("athletes-body-m");
  const tbodyF = document.getElementById("athletes-body-f");
  const tbodyX = document.getElementById("athletes-body-x");
  const xSection = document.getElementById("x-roster-section");

  // Add form elements (already on your page)
  const teamSelect = document.getElementById("teamSelect");
  const eventGroupSelect = document.getElementById("eventGroupSelect");
  const genderSelect = document.getElementById("genderSelect");
  const varsityEl = document.getElementById("varsityYN");
  const firstEl = document.getElementById("firstName");
  const lastEl = document.getElementById("lastName");
  const availEl = document.getElementById("availableYN");
  const expectedEl = document.getElementById("expectedReturn");
  const gradEl = document.getElementById("gradYear");
  const addBtn = document.getElementById("addBtn");
  const addStatus = document.getElementById("addStatus");

  // Filters
  const searchName = document.getElementById("searchName");
  const filterTeam = document.getElementById("filterTeam");
  const filterEventGroup = document.getElementById("filterEventGroup");
  const filterGender = document.getElementById("filterGender");
  const filterAvailable = document.getElementById("filterAvailable");
  const showInactive = document.getElementById("showInactive");

  let TEAMS = [];
  let EVENT_GROUPS = [];
  let ATHLETES = []; // latest fetched from API

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

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Request failed: ${url}`);
    return await res.json();
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

  function isValidNewAthlete() {
    const first = firstEl.value.trim();
    const last = lastEl.value.trim();
    if (!first || !last) return false;
    if (!teamSelect.value) return false;
    if (!eventGroupSelect.value) return false;
    if (!genderSelect.value) return false;

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

  async function loadLookups() {
    TEAMS = await fetchJSON("/api/teams");
    EVENT_GROUPS = await fetchJSON("/api/event-groups");

    // Add form dropdowns
    teamSelect.innerHTML = optionTags(TEAMS, "team_id", "name", TEAMS[0]?.team_id);
    eventGroupSelect.innerHTML = optionTags(EVENT_GROUPS, "event_group_id", "name", EVENT_GROUPS[0]?.event_group_id);

    // Filter dropdowns (keep "All" first)
    filterTeam.innerHTML =
      `<option value="">All</option>` + optionTags(TEAMS, "team_id", "name", "");
    filterEventGroup.innerHTML =
      `<option value="">All</option>` + optionTags(EVENT_GROUPS, "event_group_id", "name", "");

    refreshAddButtonState();
  }

  async function loadAthletesFromApi() {
    const include = showInactive.checked ? "true" : "false";
    ATHLETES = await fetchJSON(`/api/athletes?include_inactive=${include}`);
  }

  function getFilteredAthletes() {
    const q = searchName.value.trim().toLowerCase();
    const teamId = filterTeam.value;
    const egId = filterEventGroup.value;
    const gender = filterGender.value;
    const avail = filterAvailable.value;

    return ATHLETES.filter((a) => {
      if (teamId && String(a.team_id) !== String(teamId)) return false;
      if (egId && String(a.event_group_id) !== String(egId)) return false;
      if (gender && a.gender !== gender) return false;
      if (avail && a.available_yn !== avail) return false;

      if (q) {
        const full = `${a.first_name} ${a.last_name}`.toLowerCase();
        if (!full.includes(q)) return false;
      }
      return true;
    });
  }

  function renderIntoTbody(tbody, athletesList) {
    tbody.innerHTML = "";

    for (const a of athletesList) {
      const tr = document.createElement("tr");

      // Use the same row HTML you already had in your single-table version
      tr.innerHTML = `
        <td><input data-id="${a.athlete_id}" data-field="first_name" value="${escapeHtml(a.first_name)}" /></td>
        <td><input data-id="${a.athlete_id}" data-field="last_name" value="${escapeHtml(a.last_name)}" /></td>

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
          <select data-id="${a.athlete_id}" data-field="gender">
            <option value="M" ${a.gender === "M" ? "selected" : ""}>M</option>
            <option value="F" ${a.gender === "F" ? "selected" : ""}>F</option>
            <option value="X" ${a.gender === "X" ? "selected" : ""}>X</option>
          </select>
        </td>

        <td>
          <select data-id="${a.athlete_id}" data-field="varsity_yn">
            <option value="Y" ${a.varsity_yn === "Y" ? "selected" : ""}>Y</option>
            <option value="N" ${a.varsity_yn === "N" ? "selected" : ""}>N</option>
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

        <td><input data-id="${a.athlete_id}" data-field="grad_year" value="${a.grad_year ?? ""}" size="6" /></td>

        <td class="status" data-status-for="${a.athlete_id}"></td>

        <td>
          ${
            a.is_active === "Y"
              ? `<button data-archive-id="${a.athlete_id}">Archive</button>`
              : `<button data-unarchive-id="${a.athlete_id}">Unarchive</button>`
          }
        </td>

      `;

      if (a.is_active === "N") tr.style.opacity = "0.55";

      tbody.appendChild(tr);
    }
  }

function renderTable() {
  const filtered = getFilteredAthletes();

  // sort by last name, then first name
  filtered.sort((a, b) => {
    const last = a.last_name.localeCompare(b.last_name);
    if (last !== 0) return last;
    return a.first_name.localeCompare(b.first_name);
  });

  const male = filtered.filter((a) => a.gender === "M");
  const female = filtered.filter((a) => a.gender === "F");
  const x = filtered.filter((a) => a.gender === "X");

  renderIntoTbody(tbodyM, male);
  renderIntoTbody(tbodyF, female);

  // Only show X section if there are any X athletes in the filtered results
  if (x.length > 0) {
    xSection.style.display = "block";
    renderIntoTbody(tbodyX, x);
  } else {
    xSection.style.display = "none";
    tbodyX.innerHTML = "";
  }
}

  async function refreshRoster() {
    await loadAthletesFromApi();
    renderTable();
  }

  // Add athlete
  addBtn.addEventListener("click", async () => {
    if (!isValidNewAthlete()) return;

    const payload = {
      team_id: teamSelect.value,
      event_group_id: eventGroupSelect.value,
      gender: genderSelect.value,
      varsity_yn: varsityEl.value,
      first_name: firstEl.value.trim(),
      last_name: lastEl.value.trim(),
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
      await refreshRoster();
    } catch (err) {
      addStatus.textContent = "error";
      alert(err.message);
    }
  });

 
  [tbodyM, tbodyF, tbodyX].forEach((tb) => {
    tb.addEventListener("change", async (e) => {
      const el = e.target;
      const id = el.dataset.id;
      const field = el.dataset.field;
      if (!id || !field) return;

      const statusCell = document.querySelector(`[data-status-for="${id}"]`);
      try {
        statusCell.textContent = "saving…";
        await patchAthlete(id, { [field]: el.value });
        statusCell.textContent = "saved";
        setTimeout(() => (statusCell.textContent = ""), 800);
        await refreshRoster(); // optional, but keeps everything consistent
      } catch (err) {
        statusCell.textContent = "error";
        alert(err.message);
        await refreshRoster();
      }
    });

    tb.addEventListener("click", async (e) => {
      const archiveBtn = e.target.closest("button[data-archive-id]");
      const unarchiveBtn = e.target.closest("button[data-unarchive-id]");
      if (!archiveBtn && !unarchiveBtn) return;

      const id = archiveBtn
        ? archiveBtn.dataset.archiveId
        : unarchiveBtn.dataset.unarchiveId;

      const newStatus = archiveBtn ? "N" : "Y";
      const statusCell = document.querySelector(`[data-status-for="${id}"]`);

      try {
        statusCell.textContent = archiveBtn ? "archiving…" : "unarchiving…";
        await patchAthlete(id, { is_active: newStatus });
        statusCell.textContent = archiveBtn ? "archived" : "restored";
        await refreshRoster();
      } catch (err) {
        statusCell.textContent = "error";
        alert(err.message);
        await refreshRoster();
      }
    });
  });

  // Filters re-render without refetch (fast)
  [searchName, filterTeam, filterEventGroup, filterGender, filterAvailable].forEach((el) => {
    el.addEventListener("input", renderTable);
    el.addEventListener("change", renderTable);
  });

  // Show inactive changes API fetch behavior
  showInactive.addEventListener("change", refreshRoster);

  // Form validation wiring
  [teamSelect, eventGroupSelect, genderSelect, varsityEl, firstEl, lastEl, availEl, expectedEl, gradEl].forEach((el) => {
    el.addEventListener("input", refreshAddButtonState);
    el.addEventListener("change", refreshAddButtonState);
  });

  // init
  (async () => {
    await loadLookups();
    await refreshRoster();
    refreshAddButtonState();
  })();
});
