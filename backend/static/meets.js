
let currentMeetId = null;
let currentGender = "M";
let selectedMeetEventId = null;
let currentMeet = null;

const elMeetList = document.getElementById("meetList");
const elStatus = document.getElementById("status");
const elMeetHeader = document.getElementById("meetHeader");
const elMeetEditor = document.getElementById("meetEditor");
const elMeetActions = document.getElementById("meetActions");

const elEventsCol = document.getElementById("eventsCol");
const elAthletesCol = document.getElementById("athletesCol");

const btnNewMeet = document.getElementById("btnNewMeet");
const btnAddEvent = document.getElementById("btnAddEvent");
const btnArchiveMeet = document.getElementById("btnArchiveMeet");

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

btnNewMeet.addEventListener("click", async () => {
  const name = prompt("Meet name?", "New Meet");
  if (name == null) return;

  setStatus("creating meet…");
  const meet = await api("/api/meets", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  setStatus("");
  await loadMeets();
  await openMeet(meet.meet_id);
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

  elMeetHeader.innerHTML = `<strong>${data.meet.name}</strong> <span class="muted">(${data.gender === "M" ? "Boys" : "Girls"})</span>`;
  elMeetEditor.style.display = "block";

  elMeetActions.style.display = "flex";
  btnArchiveMeet.textContent = currentMeet.is_archived ? "Unarchive" : "Archive";

  renderEvents(data.meet_events);
  renderAthletes(data.athletes);

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
      .map((a) => `<span class="pill" data-athlete-id="${a.athlete_id}">${a.last_name}, ${a.first_name}</span>`)
      .join("");

    div.innerHTML = `
      <div class="row">
        <div>
          <strong>${me.event_name}</strong>
          <div class="muted">${me.event_group || ""}</div>
        </div>
        <div class="muted">#${me.meet_event_id}</div>
      </div>
      <div style="margin-top:8px;">${entriesHtml || `<span class="muted">No entries</span>`}</div>
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

function renderAthletes(athletes) {
  elAthletesCol.innerHTML = "";

  if (!athletes.length) {
    elAthletesCol.innerHTML = `<div class="muted">No athletes found for this gender.</div>`;
    return;
  }

  athletes.forEach((a) => {
    const div = document.createElement("div");
    div.className = "event"; // reuse styling
    div.innerHTML = `<strong>${a.last_name}, ${a.first_name}</strong> <span class="muted">${a.varsity ? "Varsity" : "JV"}</span>`;
    div.addEventListener("click", async () => {
      if (!selectedMeetEventId) {
        alert("Click an event first (left side).");
        return;
      }
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
