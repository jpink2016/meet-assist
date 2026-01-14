
let currentMeetId = null;
let currentGender = "M";
let selectedMeetEventId = null;
let currentMeet = null;
let selectedAthleteIds = new Set(); // athlete_id strings
let meetModalMode = "create"; // "create" | "edit"
let seasonsCache = []; // [{season_id, name, year, discipline}]

const elMeetList = document.getElementById("meetList");
const elStatus = document.getElementById("status");
const elMeetHeader = document.getElementById("meetHeader");
const elMeetEditor = document.getElementById("meetEditor");
const elMeetActions = document.getElementById("meetActions");
const elMeetMeta = document.getElementById("meetMeta");
const elMeetNotes = document.getElementById("meetNotes");

const elEventsCol = document.getElementById("eventsCol");
const elAthletesCol = document.getElementById("athletesCol");

const btnNewMeet = document.getElementById("btnNewMeet");
const btnAddEvent = document.getElementById("btnAddEvent");
const btnArchiveMeet = document.getElementById("btnArchiveMeet");

const createBackdrop = document.getElementById("meetCreateBackdrop");
const btnCloseCreate = document.getElementById("btnCloseCreate");
const btnCreateMeetSave = document.getElementById("btnCreateMeetSave");
const btnEditMeet = document.getElementById("btnEditMeet");
const meetModalTitle = document.getElementById("meetModalTitle");

const cName = document.getElementById("cName");
const cVarsity = document.getElementById("cVarsity");
const cVenue = document.getElementById("cVenue");
const cDate = document.getElementById("cDate");
const cLocation = document.getElementById("cLocation");
const cSeason = document.getElementById("cSeason");
const cNotes = document.getElementById("cNotes");
const hint = document.getElementById("cNameHint");

function getSelectedAthleteIdSet(meetEvents, selectedMeetEventId) {
  const me = meetEvents.find(x => String(x.meet_event_id) === String(selectedMeetEventId));
  const ids = (me?.entries || []).map(e => String(e.athlete_id));
  return new Set(ids);
}
function setStatus(msg) {
  elStatus.textContent = msg || "";
}

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  const text = await res.text();
  let json = null;
  try { json = text ? JSON.parse(text) : null; } catch {}
  if (!res.ok) throw new Error(json?.error || `${res.status} ${res.statusText}`);
  return json;
}
// --------load seasons -------

async function loadSeasons() {
  // cache so we don't refetch constantly
  if (seasonsCache.length) return seasonsCache;
  seasonsCache = await api("/api/seasons");
  return seasonsCache;
}

async function populateSeasonSelect(selectEl, selectedSeasonId = null) {
  if (!selectEl) return;

  const seasons = await loadSeasons();

  selectEl.innerHTML = `<option value="">— No Season —</option>`;

  seasons.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.season_id;

    // nicer label
    opt.textContent = s.name;

    if (String(s.season_id) === String(selectedSeasonId)) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  });
}


// -------------------- Meets list --------------------
async function loadMeets() {
  setStatus("loading meets…");
  const meets = await api("/api/meets");
  elMeetList.innerHTML = "";

  if (!meets.length) {
    elMeetList.innerHTML = `<li class="muted" style="cursor:default;">No meets yet</li>`;
    setStatus("");
    return;
  }

  meets.forEach((m) => {
    const li = document.createElement("li");
    const when = m.meet_date ? ` • ${m.meet_date}` : "";
    li.innerHTML = `<div><strong>${m.name}</strong><div class="muted">${m.location || "—"}${when}</div></div>`;
    li.addEventListener("click", () => openMeet(m.meet_id));
    elMeetList.appendChild(li);
  });

  setStatus("");
}

async function openCreateMeetModal() {
  meetModalMode = "create";
  meetModalTitle.textContent = "New Meet";
  btnCreateMeetSave.textContent = "Create";

  cName.value = "";
  cVarsity.checked = false;
  cVenue.value = "";
  cDate.value = "";
  cLocation.value = "";
  cNotes.value = "";
  await populateSeasonSelect(cSeason, null);
  createBackdrop.style.display = "flex";
}

async function openEditMeetModal() {
  if (!currentMeetId || !currentMeet) return;

  meetModalMode = "edit";
  meetModalTitle.textContent = "Edit Meet";
  btnCreateMeetSave.textContent = "Save";

  cName.value = currentMeet.name || "";
  cVarsity.checked = !!currentMeet.is_varsity;
  cVenue.value = currentMeet.venue_type || "";     // "indoor"/"outdoor"
  cDate.value = currentMeet.meet_date || "";
  cLocation.value = currentMeet.location || "";
  cNotes.value = currentMeet.notes || "";
  await populateSeasonSelect(cSeason, currentMeet.season_id);

  // clear any old validation UI
  cName.classList.remove("input-error");
  hint.style.display = "none";

  createBackdrop.style.display = "flex";
}

function closeCreateMeetModal() {
  createBackdrop.style.display = "none";
}

btnNewMeet.addEventListener("click", () => openCreateMeetModal());
btnEditMeet.addEventListener("click", () => openEditMeetModal());

btnCloseCreate.addEventListener("click", closeCreateMeetModal);
createBackdrop.addEventListener("click", (e) => {
  if (e.target === createBackdrop) closeCreateMeetModal();
});

btnCreateMeetSave.addEventListener("click", async () => {
  const name = cName.value.trim();

  // reset errors
  cName.classList.remove("input-error");
  hint.style.display = "none";

  if (!name) {
    cName.classList.add("input-error");
    hint.style.display = "block";
    cName.focus();
    return;
  }

  const payload = {
    name,
    is_varsity: cVarsity.checked,
    venue_type: cVenue.value || null,          // if dropdown
    meet_date: cDate.value || null,
    location: cLocation.value.trim() || null,
    season_id: cSeason.value === "" ? null : Number(cSeason.value),
    notes: cNotes.value.trim() || null,
  };

  try {
    setStatus(meetModalMode === "create" ? "creating meet…" : "saving…");

    if (meetModalMode === "create") {
      const meet = await api("/api/meets", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      closeCreateMeetModal();
      await loadMeets();
      await openMeet(meet.meet_id);
    } else {
      const updated = await api(`/api/meets/${currentMeetId}`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
      currentMeet = updated;
      closeCreateMeetModal();
      await loadMeetPage();
      await loadMeets(); // optional if list shows location/date, etc.
    }
  } catch (e) {
    alert(e.message);
  } finally {
    setStatus("");
  }
});

btnArchiveMeet.addEventListener("click", async () => {
  if (!currentMeetId || !currentMeet) return;

  const nextArchived = !currentMeet.is_archived;
  const label = nextArchived ? "archive" : "unarchive";

  if (!confirm(`Are you sure you want to ${label} this meet?`)) return;

  try {
    setStatus(`${label}…`);
    const updated = await api(`/api/meets/${currentMeetId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_archived: nextArchived }),
    });

    // Update local copy
    currentMeet = updated;

    // Your /api/meets list hides archived meets, so refresh list
    await loadMeets();

    if (nextArchived) {
      // Archived meet disappears from list; close editor view
      currentMeetId = null;
      selectedMeetEventId = null;
      elMeetEditor.style.display = "none";
      elMeetActions.style.display = "none";
      elMeetHeader.textContent = "Meet archived. Select another meet on the left.";
      elMeetMeta.textContent = null;
    } else {
      // If you later show archived meets somewhere, you could reload the meet page
      await loadMeetPage();
    }
  } catch (e) {
    alert(e.message);
    console.error(e);
  } finally {
    setStatus("");
  }
});
// -------------athlete event count function
function buildAthleteEntryCountMap(meetEvents = []) {
  const counts = new Map(); // key: String(athlete_id) -> number

  meetEvents.forEach((me) => {
    (me.entries || []).forEach((a) => {
      const key = String(a.athlete_id);
      counts.set(key, (counts.get(key) || 0) + 1);
    });
  });

  return counts;
}

// -------------------- Meet editor --------------------
async function openMeet(meetId) {
  currentMeetId = meetId;
  selectedMeetEventId = null;

  elMeetEditor.style.display = "none";
  elMeetHeader.textContent = "Loading meet…";

  await loadMeetPage();
}

async function loadMeetPage() {
  if (!currentMeetId) return;

  setStatus("loading meet…");
  const data = await api(`/api/meets/${currentMeetId}/page?gender=${currentGender}`);

  currentMeet = data.meet;
  await loadSeasons();
  elMeetHeader.innerHTML = `<strong>${data.meet.name}</strong> <span class="muted">(${data.gender === "M" ? "Boys" : "Girls"})</span>`;
  elMeetEditor.style.display = "block";
  
  function capitalize(s) {
    return s ? s.charAt(0).toUpperCase() + s.slice(1) : s;
  }

  const seasonName =
    data.meet.season_id != null
      ? (seasonsCache.find(s => String(s.season_id) === String(data.meet.season_id))?.name || null)
      : null;

  const metaParts = [
    data.meet.venue_type ? `${capitalize(data.meet.venue_type)}` : null,
    data.meet.meet_date ? `${data.meet.meet_date}` : null,
    data.meet.location ? `${data.meet.location}` : null,
    seasonName,
    (data.meet.is_varsity ? "Varsity" : null),
  ].filter(Boolean);

  elMeetMeta.textContent = metaParts.join(" • ");

  // notes (only show if present)
  elMeetNotes.textContent = data.meet.notes ? `Notes: ${data.meet.notes}` : "";

  elMeetActions.style.display = "flex";
  btnArchiveMeet.textContent = currentMeet.is_archived ? "Unarchive" : "Archive";

  renderEvents(data.meet_events);
  const selectedSet = getSelectedAthleteIdSet(data.meet_events, selectedMeetEventId);
  const entryCountMap = buildAthleteEntryCountMap(data.meet_events);
  renderAthletes(data.athletes, selectedSet, entryCountMap);

  setStatus("");
}

function renderEvents(meetEvents) {
  elEventsCol.innerHTML = "";

  if (!meetEvents.length) {
    elEventsCol.innerHTML = `<div class="muted">No events yet. Click “Add Event”.</div>`;
    return;
  }

  meetEvents.forEach((me) => {
    const div = document.createElement("div");
    div.className = "event" + (me.meet_event_id === selectedMeetEventId ? " selected" : "");
    div.dataset.meetEventId = me.meet_event_id;
    const entriesHtml = (me.entries || [])
      .map((a) => `
        <span
          class="pill${a.unavailable ? " pill-unavailable" : ""}"
          data-athlete-id="${a.athlete_id}"
        >
          ${a.last_name}, ${a.first_name}
        </span>
      `)
      .join("");

    div.innerHTML = `
      <div class="row">
        <div class="event-title-row">
          <strong>${me.event_name}</strong>
          <span class="muted event-group">${me.event_group || ""}</span>
        </div>
        <div class="muted">#${me.meet_event_id}</div>
      </div>
      <div style="margin-top:8px;">
        ${entriesHtml || `<span class="muted">No entries</span>`}
      </div>
    `;

    div.addEventListener("click", () => {
      selectedMeetEventId = me.meet_event_id;
      // rerender selection highlight (cheap way)
      loadMeetPage().catch((e) => alert(e.message));
    });

    // Allow removing an athlete by clicking their pill (nice little MVP)
    div.addEventListener("click", async (e) => {
      const pill = e.target.closest("[data-athlete-id]");
      if (!pill) return;
      e.stopPropagation();
      const athleteId = pill.dataset.athleteId;
      await api(`/api/meet-events/${me.meet_event_id}/entries/${athleteId}`, { method: "DELETE" });
      await loadMeetPage();
    });

    elEventsCol.appendChild(div);
  });
}

function renderAthletes(athletes, selectedSet = new Set(), entryCountMap = new Map()) {
  elAthletesCol.innerHTML = "";

  if (!athletes.length) {
    elAthletesCol.innerHTML = `<div class="muted">No athletes found for this gender.</div>`;
    return;
  }

  athletes.forEach((a) => {
    const varsityMeets = Number(a.varsity_meets || 0);
    const varsityText = `Varsity Meets: ${varsityMeets}`;
    const div = document.createElement("div");
    const athleteIdStr = String(a.athlete_id); 
    const isSelected = selectedSet.has(String(a.athlete_id));
    div.className = `event${isSelected ? " is-selected" : ""}`; // reuse styling
    const meta = [a.event_group_name,a.team_name].filter(Boolean).join(" • ");
    const badge = a.unavailable ? `<span class="badge badge-unavailable">Unavailable</span>` : "";
    const count = entryCountMap.get(athleteIdStr) || 0;
    const countText = `Events Entered: ${count}`;
    const count_meta = [countText,varsityText].filter(Boolean).join(" • ")

    div.innerHTML = `
      <div class="ath-row-top">
        <strong>${a.last_name}, ${a.first_name}</strong>
        ${badge}
      </div>
      <div class="muted ath-row-sub">${count_meta}</div>
      <div class="muted ath-row-meta">${meta}</div>    `;

    div.addEventListener("click", async () => {
      if (!selectedMeetEventId) {
        alert("Click an event first (left side).");
        return;
      }

      // optional: prevent duplicate add spam
      if (isSelected) return;

      try {
        await api(`/api/meet-events/${selectedMeetEventId}/entries`, {
          method: "POST",
          body: JSON.stringify({ athlete_id: a.athlete_id }),
        });
        await loadMeetPage();
      } catch (e) {
        alert(e.message);
      }
    });

    elAthletesCol.appendChild(div);
  });
}

// -------------------- Add event to meet --------------------
btnAddEvent.addEventListener("click", async () => {
  if (!currentMeetId) return;

  // Super simple picker for MVP: prompt for event_id
  // Next step we’ll replace this with a nice dropdown using GET /api/events.
  const eventId = prompt("Enter event_id to add (we’ll build a picker next):");
  if (!eventId) return;

  try {
    await api(`/api/meets/${currentMeetId}/meet-events`, {
      method: "POST",
      body: JSON.stringify({ event_id: Number(eventId), gender: currentGender, sort_order: 0 }),
    });
    await loadMeetPage();
  } catch (e) {
    alert(e.message);
  }
});

// -------------------- Gender tabs --------------------
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    currentGender = btn.dataset.gender;
    selectedMeetEventId = null;
    await loadMeetPage();
  });
});

// Boot
loadMeets().catch((e) => alert(e.message));
