/* =====================================================
   1. HELPER FUNCTIONS
===================================================== */

/**
 * Splits a string of card codes into an array.
 * Example: "Ah Ks" → ["Ah", "Ks"]
 */
function tokenizeCards(str) {
  return str.trim() ? str.trim().split(/\s+/) : [];
}

/**
 * Parses opponent card strings separated by semicolons.
 * Example: "Qh Qs; Ad Kd" → [["Qh", "Qs"], ["Ad", "Kd"]]
 */
function parseOpps(str) {
  if (!str.trim()) return [];
  return str.split(";").map(part => {
    const t = part.trim();
    if (!t) return [];
    return t.split(/\s+/);
  });
}

/* =====================================================
   2. ELEMENT REFERENCES
===================================================== */
const form = document.getElementById("calc-form");
const results = document.getElementById("results");

/* =====================================================
   3. FORM SUBMISSION & API CALL
===================================================== */
form.addEventListener("submit", async (e) => {
  e.preventDefault();

  // Hide and reset results box
  results.classList.add("hidden");
  results.innerHTML = "Calculating…";

  // Collect input values
  const n_players = Number(document.getElementById("players").value);
  const hero = tokenizeCards(document.getElementById("hero").value);
  const board = tokenizeCards(document.getElementById("board").value);
  const opponents = parseOpps(document.getElementById("opps").value);
  const trials = Number(document.getElementById("trials").value);

  /* ---------------------------------------------
     Send data to the backend odds API
  --------------------------------------------- */
  try {
    const res = await fetch("/api/calc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ n_players, hero, board, opponents, trials })
    });

    const json = await res.json();
    if (!res.ok) throw new Error(json.error || "Server error");

    /* ---------------------------------------------
       Build and display the results
    --------------------------------------------- */
    const heroPct = (json.hero.win * 100).toFixed(2);
    const heroTie = (json.hero.tie * 100).toFixed(2);

    let html = `<h2>Results</h2>`;
    html += `<p>Trials: ${json.meta.trials.toLocaleString()}</p>`;
    html += `<div class="card"><strong>Hero</strong>: Win ${heroPct}% · Tie ${heroTie}%</div>`;

    if (json.opponents && json.opponents.length) {
      html += `<div><strong>Opponents</strong></div>`;
      json.opponents.forEach((o, i) => {
        html += `<div>Villain ${i + 1}: Win ${(o.win * 100).toFixed(2)}%</div>`;
      });
    }

    results.innerHTML = html;
    results.classList.remove("hidden");

  } catch (err) {
    /* ---------------------------------------------
       Error handling
    --------------------------------------------- */
    results.innerHTML = `<div class="card">❌ ${err.message}</div>`;
    results.classList.remove("hidden");
  }
});
