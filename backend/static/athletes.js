
document.addEventListener("DOMContentLoaded", () => {
  const tbody = document.getElementById("athletes-body");
  const addBtn = document.getElementById("addBtn");

  let nextId = 1;
  const athletes = [];

  function render() {
    tbody.innerHTML = "";
    for (const a of athletes) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${a.id}</td>
        <td>${a.first}</td>
        <td>${a.last}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  addBtn.addEventListener("click", () => {
    const first = document.getElementById("firstName").value.trim();
    const last = document.getElementById("lastName").value.trim();

    if (!first || !last) {
      alert("First and last name required");
      return;
    }

    athletes.push({
      id: nextId++,
      first,
      last,
    });

    document.getElementById("firstName").value = "";
    document.getElementById("lastName").value = "";

    render();
  });

  render();
});

