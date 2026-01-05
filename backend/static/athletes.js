document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("athletes-body");
  const addBtn = document.getElementById("addBtn");

  async function loadAthletes() {
    const res = await fetch("/api/athletes");
    const athletes = await res.json();

    tbody.innerHTML = "";
    for (const a of athletes) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${a.athlete_id}</td>
        <td>${a.team_id}</td>
        <td>${a.varsity}</td>
        <td>${escapeHtml(a.first_name)}</td>
        <td>${escapeHtml(a.last_name)}</td>
        <td>${a.unavailable_yn}</td>
        <td>${escapeHtml(a.expected_return || "")}</td>
        <td>${a.grad_year ?? ""}</td>
        <td>${a.is_active}</td>
        <td></td>
        `;
      tbody.appendChild(tr);
    }
  }

  addBtn.addEventListener("click", async () => {
    const first = document.getElementById("firstName").value.trim();
    const last = document.getElementById("lastName").value.trim();
    if (!first || !last) {
      alert("First and last name required");
      return;
    }

    const res = await fetch("/api/athletes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ first_name: first, last_name: last }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(err.error || "Failed to add athlete");
      return;
    }

    document.getElementById("firstName").value = "";
    document.getElementById("lastName").value = "";

    await loadAthletes();
  });

  function escapeHtml(s) {
    return String(s ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  loadAthletes();
});
