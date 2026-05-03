"""
Stack Attack Reborn — Highscore Persistence
"""
import json
import os
from constants import HIGHSCORES_FILE


def load_highscores():
    """Load highscores from disk; returns dict {char_id: best_score}."""
    if os.path.exists(HIGHSCORES_FILE):
        try:
            with open(HIGHSCORES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_highscores(scores):
    """Persist highscores dict to disk."""
    try:
        with open(HIGHSCORES_FILE, "w") as f:
            json.dump(scores, f)
    except Exception:
        pass


# Loaded once at import time; mutated by game logic and saved on game over.
highscores = load_highscores()
