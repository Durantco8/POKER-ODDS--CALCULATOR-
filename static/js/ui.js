/* =====================================================
   1. GLOBAL VARIABLES
===================================================== */
const suits = ["c", "d", "h", "s"];
const ranks = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"];

const deckEl = document.getElementById("deck");
const boardEl = document.getElementById("board-cards");
const resultBox = document.getElementById("results");
const pokerTable = document.querySelector(".poker-table");

let numPlayers = 2;
let selected = {};
let undoStack = [];

// sound
const dealSound = new Audio("static/sounds/deal.mp3");
function playDealSound() {
  dealSound.currentTime = 0;
  dealSound.play();
}

/* =====================================================
   2. GAME INITIALIZATION
===================================================== */
document.getElementById("start-game").addEventListener("click", () => {
  numPlayers = parseInt(document.getElementById("player-count").value);
  document.getElementById("setup").classList.add("hidden");
  document.getElementById("poker-table").classList.remove("hidden");
  initGame();
});

function initGame() {
  // reset data
  selected = { board: [null, null, null, null, null] };
  undoStack = [];

  for (let i = 0; i < numPlayers; i++) {
    selected[`player${i}`] = [null, null]; // 2 hole cards each
  }

  // reset UI
  resultBox.textContent = "";
  deckEl.innerHTML = "";
  boardEl.innerHTML = "";
  document.getElementById("players").innerHTML = "";

  renderTable();
  renderDeck();
}

/* =====================================================
   3. TABLE RENDERING
===================================================== */
function renderTable() {
  const container = document.getElementById("players");
  container.innerHTML = "";

  const table = document.querySelector(".poker-table");
  const cx = table.offsetWidth / 2;
  const cy = table.offsetHeight / 2;
  const radiusX = table.offsetWidth * 0.42;
  const radiusY = table.offsetHeight * 0.32;

  for (let i = 0; i < numPlayers; i++) {
    const angle = (i / numPlayers) * 2 * Math.PI - Math.PI / 2;
    const x = cx + radiusX * Math.cos(angle);
    const y = cy + radiusY * Math.sin(angle);

    const seat = document.createElement("div");
    seat.className = "player-seat";
    seat.style.left = `${x}px`;
    seat.style.top = `${y}px`;

    const cardRow = document.createElement("div");
    cardRow.className = "card-row";
    cardRow.id = `player${i}-cards`;

    // 2 placeholders
    for (let j = 0; j < 2; j++) {
      const ph = document.createElement("div");
      ph.className = "placeholder";
      ph.dataset.target = `player${i}`;
      ph.dataset.index = j;
      addDropListeners(ph);
      cardRow.appendChild(ph);
    }

    const odds = document.createElement("div");
    odds.className = "odds";
    odds.id = `player${i}-odds`;
    odds.innerHTML = `
      <div class="odds-text">Win: –</div>
      <div class="odds-bar"><div class="fill"></div></div>
    `;

    seat.appendChild(cardRow);
    seat.appendChild(odds);
    container.appendChild(seat);
  }

  // board placeholders
  boardEl.innerHTML = "";
  for (let i = 0; i < 5; i++) {
    const ph = document.createElement("div");
    ph.className = "placeholder";
    ph.dataset.target = "board";
    ph.dataset.index = i;
    addDropListeners(ph);
    boardEl.appendChild(ph);
  }
}

/* =====================================================
   4. DROP LISTENER HELPER
===================================================== */
function addDropListeners(ph) {
  ph.addEventListener("dragover", (e) => {
    e.preventDefault();
    ph.classList.add("drop-hover");
  });

  ph.addEventListener("dragleave", () => {
    ph.classList.remove("drop-hover");
  });

  ph.addEventListener("drop", (e) => {
    e.preventDefault();
    ph.classList.remove("drop-hover");

    const card = e.dataTransfer.getData("text/plain");
    const deckCardEl = deckEl.querySelector(`[data-card="${card}"]`);

    if (!deckCardEl || deckCardEl.classList.contains("selected")) return;
    deckCardEl.classList.add("selected");
    playDealSound();

    const target = ph.dataset.target;
    const index = parseInt(ph.dataset.index);

    placeCard(target, index, card, ph);
  });
}

/* =====================================================
   5. DECK RENDERING
===================================================== */
function renderDeck() {
  deckEl.innerHTML = "";

  ranks.forEach((r) => {
    suits.forEach((s) => {
      const name = `${r}${s}`;

      const img = document.createElement("img");
      img.src = `static/img/cards/${name}.svg`;
      img.className = "card";
      img.dataset.card = name;

      // click-to-place
      img.addEventListener("click", () => clickPlaceCard(name, img));

      // drag-to-place
      img.draggable = true;
      img.addEventListener("dragstart", (e) => {
        e.dataTransfer.setData("text/plain", name);
        setTimeout(() => img.classList.add("dragging"), 0);
      });
      img.addEventListener("dragend", () => img.classList.remove("dragging"));

      deckEl.appendChild(img);
    });
  });
}

// HIDE DECK FUNCTION 
document.getElementById("toggle-deck").addEventListener("click", () => {
    deckEl.classList.toggle("hidden");

    const btn = document.getElementById("toggle-deck");
    if (deckEl.classList.contains("hidden")) {
        btn.textContent = "Show Deck";
    } else {
        btn.textContent = "Hide Deck";
    }
});


/* =====================================================
   6. CLICK-TO-PLACE CARD
===================================================== */
function clickPlaceCard(card, imgEl) {
  if (imgEl.classList.contains("selected")) return;

  imgEl.classList.add("selected");
  playDealSound();

  // find first empty slot: players first
  let target = null;
  let index = null;

  for (let p = 0; p < numPlayers; p++) {
    const hand = selected[`player${p}`];
    if (hand[0] === null) {
      target = `player${p}`;
      index = 0;
      break;
    }
    if (hand[1] === null) {
      target = `player${p}`;
      index = 1;
      break;
    }
  }

  // then board
  if (target === null) {
    for (let i = 0; i < 5; i++) {
      if (selected.board[i] === null) {
        target = "board";
        index = i;
        break;
      }
    }
  }

  if (target === null) return;

  const ph = document.querySelector(
    `.placeholder[data-target="${target}"][data-index="${index}"]`
  );
  if (!ph) return;

  placeCard(target, index, card, ph);
}

/* =====================================================
   7. PLACE A CARD (USED BY CLICK + DROP)
===================================================== */
function placeCard(target, index, card, placeholder) {
  // update UI
  const img = document.createElement("img");
  img.src = `static/img/cards/${card}.svg`;
  img.className = "card";
  placeholder.replaceWith(img);

  // update data
  selected[target][index] = card;

  // record undo
  undoStack.push({ target, index, card });

  if (readyToCalculate()) {
    calculateOdds();
  }
}

/* =====================================================
   8. UNDO
===================================================== */
document.getElementById("undo").addEventListener("click", () => {
  if (undoStack.length === 0) return;

  const { target, index, card } = undoStack.pop();

  // clear from data
  selected[target][index] = null;

  // make deck card available again
  const deckCardEl = deckEl.querySelector(`[data-card="${card}"]`);
  if (deckCardEl) deckCardEl.classList.remove("selected");

  // restore placeholder in UI
  const area =
    target === "board" ? boardEl : document.getElementById(`${target}-cards`);

  const imgs = area.querySelectorAll("img");
  for (const img of imgs) {
    if (img.src.includes(card)) {
      const ph = document.createElement("div");
      ph.className = "placeholder";
      ph.dataset.target = target;
      ph.dataset.index = index;
      addDropListeners(ph);
      img.replaceWith(ph);
      break;
    }
  }

  if (readyToCalculate()) {
    calculateOdds();
  } else {
    resultBox.textContent = "";
    document
      .querySelectorAll(".odds-text")
      .forEach((el) => (el.textContent = "Win: –"));
    document
      .querySelectorAll(".fill")
      .forEach((el) => (el.style.width = "0%"));
  }
});

/* =====================================================
   9. READY CHECK
===================================================== */
function readyToCalculate() {
  for (let i = 0; i < numPlayers; i++) {
    const hand = selected[`player${i}`];
    if (!hand || !hand[0] || !hand[1]) return false;
  }
  return true;
}

/* =====================================================
   10. CALCULATE ODDS
===================================================== */
async function calculateOdds() {
  resultBox.textContent = "Calculating…";

  const hero = selected["player0"];
  const opponents = [];
  for (let i = 1; i < numPlayers; i++) {
    opponents.push(selected[`player${i}`]);
  }

  // filter out null board cards
  const cleanBoard = selected.board.filter((c) => c !== null);

  try {
    const res = await fetch("/api/calc", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        hero,
        opponents,
        board: cleanBoard,
        n_players: numPlayers,
        trials: 20000,
      }),
    });

    const data = await res.json();
    if (!res.ok) {
      resultBox.textContent = "Error: " + data.error;
      return;
    }

    // hero odds
    const heroEl = document.getElementById("player0-odds");
    const heroWin = (data.hero.win * 100).toFixed(2);
    const heroTie = (data.hero.tie * 100).toFixed(2);
    heroEl.querySelector(
      ".odds-text"
    ).textContent = `Win ${heroWin}% · Tie ${heroTie}%`;
    heroEl.querySelector(".fill").style.width = `${heroWin}%`;

    // opponent odds
    data.opponents.forEach((o, i) => {
      const el = document.getElementById(`player${i + 1}-odds`);
      if (!el) return;
      const winPct = (o.win * 100).toFixed(2);
      el.querySelector(".odds-text").textContent = `Win ${winPct}%`;
      el.querySelector(".fill").style.width = `${winPct}%`;
    });

    resultBox.innerHTML = `<p>Simulated ${data.meta.trials.toLocaleString()} hands</p>`;

    pokerTable.classList.add("active");
    setTimeout(() => pokerTable.classList.remove("active"), 1500);
  } catch (err) {
    resultBox.textContent = "Error connecting to server.";
    console.error(err);
  }
}

/* =====================================================
   11. CLEAR
===================================================== */
document.getElementById("clear").addEventListener("click", () => {
  selected = {};
  undoStack = [];
  resultBox.innerHTML = "";
  deckEl.innerHTML = "";
  boardEl.innerHTML = "";
  document.getElementById("players").innerHTML = "";
  document.getElementById("poker-table").classList.add("hidden");
  document.getElementById("setup").classList.remove("hidden");
  // deck will be rebuilt after next start-game → initGame()
});
