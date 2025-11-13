from flask import Flask, send_from_directory, request, jsonify
from poker import parse_card, simulate_equity

# =====================================================
# 1. APP INITIALIZATION
# =====================================================
app = Flask(__name__, static_folder="static")


# =====================================================
# 2. FRONT-END ROUTES
# =====================================================
@app.route("/")
def index() -> str:
    """Serve the main web page."""
    return send_from_directory(".", "index.html")


# =====================================================
# 3. API ROUTES
# =====================================================
@app.route("/api/calc", methods=["POST"])
def calc():
    """
    POST /api/calc
    ----------------
    Request JSON:
        {
          "hero": ["Ah", "Kd"],
          "opponents": [["Qs", "Qh"], ["7c", "7d"]],
          "board": ["2h", "9d", "Tc"],
          "n_players": 3,
          "trials": 20000
        }

    Response JSON:
        {
          "hero": {"win": 0.63, "tie": 0.04},
          "opponents": [{"win": 0.31, "tie": 0.04}, ...],
          "meta": {"trials": 20000}
        }
    """
    try:
        data = request.get_json(force=True)
        hero = data.get("hero", [])
        opponents = data.get("opponents", [])
        board = data.get("board", [])
        n_players = int(data.get("n_players", max(2, 1 + len(opponents))))
        n_trials = int(data.get("trials", 20000))

        # ---------- Validation ----------
        if len(hero) != 2:
            return jsonify(error="Hero must have exactly 2 cards"), 400
        if not (2 <= n_players <= 9):
            return jsonify(error="n_players must be between 2 and 9"), 400

        # ---------- Normalize Opponents ----------
        # Ensure we have exactly n_players - 1 opponent slots
        opponents = (opponents + [[]] * (n_players - 1 - len(opponents)))[: n_players - 1]

        # ---------- Parse Cards ----------
        hero_cards = [parse_card(c) for c in hero]
        opp_cards = [[parse_card(c) for c in hand] if hand else [] for hand in opponents]
        board_cards = [parse_card(c) for c in board]

        # ---------- Simulation ----------
        result = simulate_equity(hero_cards, opp_cards, board_cards, n_trials)
        return jsonify(result), 200

    except (ValueError, KeyError, TypeError) as e:
        # Graceful fallback for malformed input
        return jsonify(error=str(e)), 400


@app.route("/test")
def test() -> str:
    """Simple test route to verify Flask setup."""
    return f"✅ Flask is running and serving static files from: {app.static_folder}"


# =====================================================
# 4. ENTRY POINT
# =====================================================
if __name__ == "__main__":
    # debug=True auto-reloads during development
    app.run(debug=True, host="127.0.0.1", port=5000)
