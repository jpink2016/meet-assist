// Find the form and leaderboard elements
const form = document.getElementById('movie-form');
const leaderboardBody = document.getElementById('leaderboard-body');
async function loadTitles() { 
    const res = await fetch('/titles'); 
    const titles = await res.json(); 
    const select = document.getElementById('movieTitle'); 
    select.innerHTML = '';

    const placeholder = document.createElement('option');
    placeholder.textContent = 'Select a Movie';
    placeholder.value = '';
    placeholder.disabled = true;
    placeholder.selected = true;
    select.appendChild(placeholder);

    titles.forEach(t => {
        const opt = document.createElement('option'); 
        opt.value = t.title_id; // or t.id if you want ids 
        opt.textContent = t.title; 
        select.appendChild(opt); 
    }); 
}
async function loadLeaderboard() {
    const res = await fetch('/leaderboard');
    const movies = await res.json();

    leaderboardBody.innerHTML = ''; // clear table

    movies.forEach(movie => {
        const row = document.createElement('tr');

        // Movie Name
        const nameCell = document.createElement('td');
        nameCell.textContent = movie.name;

        // Rating
        const ratingCell = document.createElement('td');
        ratingCell.textContent = movie.rating;

        // Action cell
        const actionCell = document.createElement('td');
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.addEventListener('click', async () => {
            await fetch(`/movies/${movie.rating_id}`, { method: 'DELETE' });
            loadLeaderboard();
        });
        actionCell.appendChild(deleteBtn);

        row.appendChild(nameCell);
        row.appendChild(ratingCell);
        row.appendChild(actionCell);

        leaderboardBody.appendChild(row);
    });
}
// Handle form submission
form.addEventListener('submit', async (e) => {
    e.preventDefault(); // prevent page reload

    const title_id = parseInt(document.getElementById('movieTitle').value);
    const rating = parseInt(document.getElementById('rating').value);

    // Send movie to backend
    await fetch('/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          title_id: title_id, 
          rating: rating
        })
    });
    form.reset();       // reset form
    loadTitles();       //reselect placeholder
    loadLeaderboard();  // refresh leaderboard
});

loadTitles();
// Load leaderboard when page first opens
loadLeaderboard();
