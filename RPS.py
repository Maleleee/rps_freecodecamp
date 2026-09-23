# Multi-strategy player: detect which bot we are facing and counter it.
# Quincy cycles R-P-P-S-R. Kris always counters our last move. Mrugesh
# counters our most common move in the last 10. Abbey predicts our next
# move with a 2-gram Markov model on our history, then counters that.

BEAT = {"R": "P", "P": "S", "S": "R"}
QUINCY_CYCLE = ["R", "P", "P", "S", "R"]
PAIRS = ["RR", "RP", "RS", "PR", "PP", "PS", "SR", "SP", "SS"]


def _quincy_next(opponent_history):
    hist = opponent_history
    if not hist:
        return "R"
    best_off, best_matches = 0, -1
    for off in range(5):
        matches = sum(
            hist[i] == QUINCY_CYCLE[(off + i) % 5] for i in range(len(hist))
        )
        if matches > best_matches:
            best_matches = matches
            best_off = off
    return QUINCY_CYCLE[(best_off + len(hist)) % 5]


def _kris_next(my_history):
    last = my_history[-1] if my_history else "R"
    return BEAT[last]


def _mrugesh_next(my_history):
    # Mrugesh appends the empty first-call token, then our plays.
    seen = [""] + my_history
    last_ten = seen[-10:]
    most_frequent = max(set(last_ten), key=last_ten.count)
    if most_frequent == "":
        most_frequent = "S"
    return BEAT[most_frequent]


def _abbey_next(my_history):
    # Replay Abbey's exact state machine for this match.
    play_order = {k: 0 for k in PAIRS}
    history = []
    n = len(my_history) + 1
    prediction = "R"
    for i in range(n):
        prev = my_history[i - 1] if i else ""
        if not prev:
            prev = "R"
        history.append(prev)
        last_two = "".join(history[-2:])
        if len(last_two) == 2:
            play_order[last_two] += 1
        if i == n - 1:
            potential = [prev + m for m in ("R", "P", "S")]
            sub_order = {k: play_order[k] for k in potential}
            prediction = max(sub_order, key=sub_order.get)[-1]
    return BEAT[prediction]


def player(prev_play, opponent_history=[], state={}):
    if prev_play == "":
        opponent_history.clear()
        state.clear()
        state["my_history"] = []
        state["score"] = {"quincy": 0, "kris": 0, "mrugesh": 0, "abbey": 0}
        state["preds"] = {}
        guess = "P"
        state["my_history"].append(guess)
        return guess

    opponent_history.append(prev_play)

    for name, pred in state.get("preds", {}).items():
        if pred == prev_play:
            state["score"][name] += 1
        else:
            state["score"][name] -= 1

    preds = {
        "quincy": _quincy_next(opponent_history),
        "kris": _kris_next(state["my_history"]),
        "mrugesh": _mrugesh_next(state["my_history"]),
        "abbey": _abbey_next(state["my_history"]),
    }
    state["preds"] = preds

    best = max(state["score"], key=state["score"].get)
    guess = BEAT[preds[best]]
    state["my_history"].append(guess)
    return guess
