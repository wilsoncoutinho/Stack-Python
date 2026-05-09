"""
Stack Attack Reborn — Crane Spawning & Update
"""
import random
from constants import (
    TILE_SIZE, COLS, WIDTH, CRANE_COUNT,
)
from assets_loader import CRANE_SPRITE_W, CRANE_SPRITE_H
from board import is_cell_occupied
import state


def current_crane_count():
    return max(1, int(state.difficulty))


def queue_crate_spawn(grid_x, crate_type):
    active_count = current_crane_count()
    if len(state.cranes) >= active_count:
        return

    speed = 2.0 + state.difficulty * 0.2
    if random.choice([True, False]):
        x = -CRANE_SPRITE_W
        vx = speed
    else:
        x = WIDTH + CRANE_SPRITE_W
        vx = -speed

    state.cranes.append({
        "x": float(x),
        "vx": float(vx),
        "drop_x": grid_x,
        "type": crate_type,
        "dropped": False,
    })


def update_crane():
    state.crane_frame = 0
    for c in state.cranes[:]:
        prev_x = c["x"]
        c["x"] += c["vx"]

        if not c["dropped"]:
            target_px = c["drop_x"] * TILE_SIZE + TILE_SIZE / 2
            curr_hook = c["x"] + CRANE_SPRITE_W / 2
            prev_hook = prev_x + CRANE_SPRITE_W / 2

            crossed = (
                (c["vx"] > 0 and prev_hook <= target_px <= curr_hook)
                or (c["vx"] < 0 and prev_hook >= target_px >= curr_hook)
            )

            if crossed:
                drop_x = c["drop_x"]
                drop_row = max(0, CRANE_SPRITE_H // TILE_SIZE)
                if not is_cell_occupied(drop_x, drop_row):
                    state.falling_boxes.append({
                        "x": drop_x,
                        "y": drop_row,
                        "type": c["type"],
                        "px": float(drop_x * TILE_SIZE),
                        "py": float(CRANE_SPRITE_H),
                    })
                    c["dropped"] = True

        if c["vx"] > 0 and c["x"] > WIDTH + CRANE_SPRITE_W:
            state.cranes.remove(c)
        elif c["vx"] < 0 and c["x"] < -CRANE_SPRITE_W * 2:
            state.cranes.remove(c)
