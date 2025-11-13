from flask import Flask, send_from_directory, request, jsonify
from poker import parse_card, simulate_equity

# =====================================================
# 1. APP INITIALIZATION
# =====================================================
app = Flask(__name__, static_folder="static")


# =====================================================
# 2. STATIC FILE ROUTES (robots.txt, sitemap.xml)
# =====================================================
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    return send_from_directory('static', 'sitemap.xml')


# =====================================================
# 3. FRONT-END ROUTES
# =====================================================
@app.route("/")
def index() -> str:
    """Serve the main web page."""
    return send_from_directory(".", "index.html")


# =====================================================
# 4. API ROUTES
# =====================================================
@app.route("/api/calc", methods=["POST"])
def calc():
    try:
        data = request.get_json(force=True)
        hero = data.get("hero", [])
        opponents = data.get("opponents", [])
        board = data.get("board", [])
        n_players = int(data.get("n_players", max(2, 1 + len(opponents))))
        n_trials = int(data.get("trials", 20000))

        if len(hero) != 2:
            return jsonify(error="Hero must have exactly 2 cards"), 400
        if not (2 <= n_players <= 9):
            return jsonify(error="n_players must be between 2 and 9"), 400

        opponents = (opponents + [[]] * (n_players - 1 - len(opponents)))[: n_players - 1]

        hero_cards = [parse_card(c) for c in hero]
        opp_cards = [[parse_card(c) for c in hand] if hand else [] for hand in opponents]
        board_cards = [parse_card(c) for c in board]

        result = simulate_equity(hero_cards, opp_cards, board_cards, n_trials)
        return jsonify(result), 200

    except (ValueError, KeyError, TypeError) as e:
        return jsonify(error=str(e)), 400


@app.route("/test")
def test() -> str:
    return f"✅ Flask is running and serving static files from: {app.static_folder}"


# =====================================================
# 5. ENTRY POINT
# =====================================================
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
