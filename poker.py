import random
from collections import Counter

# =====================================================
# 1. CONSTANTS & CARD MAPPINGS
# =====================================================
RANKS = "23456789TJQKA"
SUITS = "cdhs"  # clubs, diamonds, hearts, spades

RANK_TO_INT = {r: i for i, r in enumerate(RANKS, start=2)}
INT_TO_RANK = {v: k for k, v in RANK_TO_INT.items()}

ALL_CARDS = [r + s for r in RANKS for s in SUITS]


# =====================================================
# 2. CARD CLASS & PARSING UTILITIES
# =====================================================
class Card:
    """Represents a single playing card."""
    __slots__ = ("rank", "suit")

    def __init__(self, rank: int, suit: str):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"{INT_TO_RANK[self.rank]}{self.suit}"


def parse_card(token: str) -> Card:
    """Converts a string like 'Ah' or 'TC' into a Card object."""
    if not token:
        raise ValueError("Empty card token")
    t = token.strip().upper()
    if len(t) != 2:
        raise ValueError(f"Invalid card: {token}")
    r, s = t[0], t[1].lower()
    if r not in RANK_TO_INT or s not in SUITS:
        raise ValueError(f"Invalid card: {token}")
    return Card(RANK_TO_INT[r], s)


def deck_without(exclude_cards):
    """Returns a deck list excluding the specified cards."""
    excl = {repr(c) for c in exclude_cards}
    return [parse_card(c) for c in ALL_CARDS if c not in excl]


# =====================================================
# 3. HAND EVALUATION LOGIC (7-CARD EVALUATOR)
# =====================================================
def evaluate_7(cards):
    """
    Evaluates the strength of a 7-card hand.
    Returns a tuple (rank_category, tie_breakers...) where higher is better.
    """
    ranks = [c.rank for c in cards]
    suits = [c.suit for c in cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)

    is_flush = any(cnt >= 5 for cnt in suit_counts.values())
    flush_suit = next((s for s, cnt in suit_counts.items() if cnt >= 5), None)
    flush_ranks = sorted([c.rank for c in cards if c.suit == flush_suit], reverse=True) if is_flush else []

    # ----- Check straights -----
    def best_straight(seq):
        if not seq:
            return 0
        uniq = sorted(set(seq), reverse=True)
        if 14 in uniq:  # Ace can be low (A-2-3-4-5)
            uniq.append(1)
        best = 0
        run = 1
        for i in range(1, len(uniq)):
            if uniq[i - 1] - 1 == uniq[i]:
                run += 1
                if run >= 5:
                    best = max(best, uniq[i - 4])
            else:
                run = 1
        return best

    straight_high = best_straight(ranks)
    straight_flush_high = 0
    if is_flush:
        straight_flush_high = best_straight(flush_ranks)

    # ----- Hand ranking categories -----
    if straight_flush_high:
        return (8, straight_flush_high)  # Straight flush

    quads = [r for r, c in rank_counts.items() if c == 4]
    if quads:
        quad = max(quads)
        kicker = max([r for r in ranks if r != quad])
        return (7, quad, kicker)  # Four of a kind

    trips = sorted([r for r, c in rank_counts.items() if c == 3], reverse=True)
    pairs = sorted([r for r, c in rank_counts.items() if c == 2], reverse=True)

    if trips and (len(trips) > 1 or pairs):
        trip = trips[0]
        house_pair = max([r for r in (trips[1:] + pairs)]) if (len(trips) > 1 or pairs) else 0
        return (6, trip, house_pair)  # Full house

    if is_flush:
        top5 = flush_ranks[:5]
        return (5, *top5)  # Flush

    if straight_high:
        return (4, straight_high)  # Straight

    if trips:
        trip = trips[0]
        kickers = sorted([r for r in ranks if r != trip], reverse=True)[:2]
        return (3, trip, *kickers)  # Three of a kind

    if len(pairs) >= 2:
        top2 = pairs[:2]
        kicker = max([r for r in ranks if r not in top2])
        return (2, *top2, kicker)  # Two pair

    if len(pairs) == 1:
        pair = pairs[0]
        kickers = sorted([r for r in ranks if r != pair], reverse=True)[:3]
        return (1, pair, *kickers)  # One pair

    top5 = sorted(ranks, reverse=True)[:5]
    return (0, *top5)  # High card


# =====================================================
# 4. MONTE CARLO SIMULATION FOR EQUITY
# =====================================================
def simulate_equity(hero, opponents, board, trials=20000):
    """
    Runs a Monte Carlo simulation to estimate win/tie probabilities.
    hero: list[Card]
    opponents: list[list[Card]]
    board: list[Card]
    trials: number of random runs
    """
    fixed = hero + [c for hand in opponents for c in hand] + board
    the_deck = deck_without(fixed)
    n_opp = len(opponents)
    wins, ties = 0, 0
    opp_wins = [0] * n_opp
    needed_board = 5 - len(board)

    for _ in range(trials):
        deck = the_deck[:]
        random.shuffle(deck)
        ptr = 0

        # --- Assign random opponent hands if missing ---
        sim_opps = []
        for i in range(n_opp):
            if opponents[i]:
                sim_opps.append(opponents[i])
            else:
                sim_opps.append([deck[ptr], deck[ptr + 1]])
                ptr += 2

        # --- Complete the community board ---
        sim_board = board[:]
        for _k in range(needed_board):
            sim_board.append(deck[ptr])
            ptr += 1

        # --- Evaluate hands ---
        hero_rank = evaluate_7(hero + sim_board)
        opp_ranks = [evaluate_7(h + sim_board) for h in sim_opps]

        best_rank = hero_rank
        best_idxs = ["hero"]

        for i, r in enumerate(opp_ranks):
            if r > best_rank:
                best_rank = r
                best_idxs = [i]
            elif r == best_rank:
                best_idxs.append(i)

        # --- Tally results ---
        if best_idxs == ["hero"]:
            wins += 1
        elif "hero" in best_idxs:
            ties += 1
        else:
            for i in best_idxs:
                if isinstance(i, int):
                    opp_wins[i] += 1

    # --- Normalize results ---
    total = float(trials)
    return {
        "hero": {"win": wins / total, "tie": ties / total},
        "opponents": [{"win": w / total} for w in opp_wins],
        "meta": {"trials": trials},
    }


# =====================================================
# 5. NUMPY-OPTIMIZED SIMULATION (FASTER VERSION)
# =====================================================
# import numpy as np  # (Disabled for now — using pure Python version)

# =====================================================
# (Optional) NUMPY VERSION REMOVED
# =====================================================
# The NumPy-based version was replaced by the original
# pure-Python Monte Carlo simulation for compatibility.
# If you ever want to re-enable it, re-import numpy and
# restore simulate_equity_numpy().
# from poker import parse_card, simulate_equity_numpy as simulate_equity

# RANKS = "23456789TJQKA"
# SUITS = "cdhs"
# RANK_TO_INT = {r: i for i, r in enumerate(RANKS, start=2)}
# SUIT_TO_INT = {s: i for i, s in enumerate(SUITS)}
# CARD_INT = {r + s: (RANK_TO_INT[r] - 2) * 4 + SUIT_TO_INT[s] for r in RANKS for s in SUITS}

# def int_to_card_objs(int_cards):
#     """Convert iterable of ints (0..51) into Card objects."""
#     cards = []
#     for v in int_cards:
#         rank = (int(v) // 4) + 2        # 2..14
#         suit = SUITS[int(v) % 4]        # 'c','d','h','s'
#         cards.append(Card(rank, suit))
#     return cards


# def simulate_equity_numpy(hero, opponents, board, trials=20000):
#     """
#     Optimized Monte Carlo simulation using NumPy integer deck.
#     Supports partial boards by simulating the unknown community cards each trial.
#     """
#     # --- Track used cards (by int) ---
#     used_cards = {CARD_INT[repr(c)] for c in hero}
#     for hand in opponents:
#         for c in hand:
#             used_cards.add(CARD_INT[repr(c)])
#     for c in board:
#         used_cards.add(CARD_INT[repr(c)])

#     # --- Prepare deck of remaining ints ---
#     full_deck = np.arange(52, dtype=np.int8)
#     deck = np.array([c for c in full_deck if c not in used_cards], dtype=np.int8)
#     n_opp = len(opponents)

#     hero_wins = 0
#     hero_ties = 0
#     opp_wins = np.zeros(n_opp, dtype=np.int32)

#     evaluate = evaluate_7           # local bind for speed
#     hero_cards = hero               # keep original Card objects
#     fixed_board = board[:]          # copy so we never mutate input

#     # Pre-count unknowns to draw each trial
#     missing_holes = 2 * sum(1 for h in opponents if not h)
#     base_missing_board = 5 - len(fixed_board)

#     for _ in range(trials):
#         # Draw exactly what's needed this trial
#         draw_needed = missing_holes + base_missing_board
#         draw = np.random.choice(deck, size=draw_needed, replace=False) if draw_needed > 0 else np.array([], dtype=np.int8)
#         drawn_idx = 0

#         # --- Fill missing opponent hands with Card objects ---
#         sim_opps = []
#         for hand in opponents:
#             if hand:
#                 sim_opps.append(hand)
#             else:
#                 sim_opps.append(int_to_card_objs(draw[drawn_idx:drawn_idx + 2]))
#                 drawn_idx += 2

#         # --- Complete board to full 5 cards with Card objects ---
#         sim_board = fixed_board.copy()
#         missing = 5 - len(sim_board)
#         if missing > 0:
#             sim_board.extend(int_to_card_objs(draw[drawn_idx:drawn_idx + missing]))
#             drawn_idx += missing

#         # --- Evaluate all players on a full 7-card context ---
#         hero_rank = evaluate(hero_cards + sim_board)
#         opp_ranks = [evaluate(o + sim_board) for o in sim_opps]

#         # --- Determine winner(s) ---
#         best_rank = hero_rank
#         best_idxs = ["hero"]
#         for i, r in enumerate(opp_ranks):
#             if r > best_rank:
#                 best_rank = r
#                 best_idxs = [i]
#             elif r == best_rank:
#                 best_idxs.append(i)

#         # --- Tally ---
#         if best_idxs == ["hero"]:
#             hero_wins += 1
#         elif "hero" in best_idxs:
#             hero_ties += 1
#         else:
#             for i in best_idxs:
#                 if isinstance(i, int):
#                     opp_wins[i] += 1

#     total = float(trials)
#     return {
#         "hero": {"win": hero_wins / total, "tie": hero_ties / total},
#         "opponents": [{"win": int(w) / total} for w in opp_wins],
#         "meta": {"trials": trials},
#     }
