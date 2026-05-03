"""
Stack Attack Reborn — Particles & Animation Helpers

Particle effects, push-animation interpolation, explosion floaters,
and the generic ``approach`` easing function.
"""
import random
import pygame
from constants import TILE_SIZE, PUSH_HORIZONTAL_SPEED, PUSH_SLIDE_SPEED, POWERUP_HELMET_TYPE, BOMB_TYPE
import state


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
def approach(a, b, speed):
    """Move value *a* toward *b* by at most *speed* per tick."""
    diff = b - a
    if abs(diff) <= speed:
        return b
    return a + speed * (1 if diff > 0 else -1)


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
def add_particles(x, y, color, count=10):
    for _ in range(count):
        state.particles.append({
            "x": x + random.randint(0, TILE_SIZE),
            "y": y + random.randint(0, TILE_SIZE),
            "vx": random.uniform(-3, 3),
            "vy": random.uniform(-5, -1),
            "life": random.randint(20, 40),
            "color": color,
        })


def update_particles():
    for p in state.particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vy"] += 0.2  # gravity
        p["life"] -= 1
        if p["life"] <= 0:
            state.particles.remove(p)


# ---------------------------------------------------------------------------
# Push animation & box visual interpolation
# ---------------------------------------------------------------------------
def register_push_animation(from_x, from_y, to_x, landing_y, crate_type, bomb_timer=0):
    slide_target_px = to_x * TILE_SIZE
    slide_target_py = from_y * TILE_SIZE
    final_target_py = landing_y * TILE_SIZE
    state.push_animations.append({
        "x": to_x,
        "y": landing_y,
        "type": crate_type,
        "px": from_x * TILE_SIZE,
        "py": from_y * TILE_SIZE,
        "target_px": slide_target_px,
        "target_py": slide_target_py,
        "final_py": final_target_py,
        "stage": "slide",
        "bomb_timer": bomb_timer,
    })


def update_box_visuals():
    """Interpolate falling-box and push-animation pixel positions each frame."""
    # Falling boxes smooth movement
    for box in state.falling_boxes:
        target_px = float(box["x"] * TILE_SIZE)
        target_py = float(box["y"] * TILE_SIZE)
        if "px" not in box:
            box["px"] = target_px
            box["py"] = target_py
        bpx_diff = abs(target_px - box["px"])
        bpy_diff = abs(target_py - box["py"])
        if bpx_diff > 0.5:
            box["px"] = approach(box["px"], target_px, max(14, bpx_diff * 0.9))
        else:
            box["px"] = target_px
        if bpy_diff > 0.5:
            box["py"] = approach(box["py"], target_py, max(16, bpy_diff * 0.95))
        else:
            box["py"] = target_py

    # Push animations
    completed_pushes = []
    for anim in state.push_animations[:]:
        px_diff = abs(anim["target_px"] - anim["px"])
        py_diff = abs(anim["target_py"] - anim["py"])
        if px_diff > 0.5:
            horizontal_speed = PUSH_HORIZONTAL_SPEED if anim["stage"] == "slide" else PUSH_SLIDE_SPEED
            anim["px"] = approach(anim["px"], anim["target_px"], max(horizontal_speed, px_diff * 0.18))
        else:
            anim["px"] = anim["target_px"]
        if py_diff > 0.5:
            anim["py"] = approach(anim["py"], anim["target_py"], max(12, py_diff * 0.55))
        else:
            anim["py"] = anim["target_py"]
        if anim["px"] == anim["target_px"] and anim["py"] == anim["target_py"]:
            if anim["stage"] == "slide" and anim["final_py"] != anim["target_py"]:
                anim["stage"] = "fall"
                anim["target_py"] = anim["final_py"]
            else:
                completed_pushes.append(anim)
                state.push_animations.remove(anim)

    # Floating explosions
    for exp in state.floating_explosions[:]:
        exp["timer"] -= 1
        if exp["timer"] <= 0:
            state.floating_explosions.remove(exp)

    # Finalize completed push animations
    from board import apply_board_gravity, do_post_landing  # deferred to avoid circular import

    for anim in completed_pushes:
        tx, ty = anim["x"], anim["y"]
        # If the destination was filled while we were sliding, stack on top
        while ty >= 0 and state.board[ty][tx] != 0:
            ty -= 1
        if ty >= 0:
            state.board[ty][tx] = anim["type"]
            if anim["type"] == POWERUP_HELMET_TYPE:
                state.helmet_timers[ty][tx] = anim.get("helmet_timer", 180)
            if anim["type"] == BOMB_TYPE:
                state.bomb_timers[ty][tx] = anim.get("bomb_timer", 180)

        state.combo_count = 0
        apply_board_gravity()
        do_post_landing()
