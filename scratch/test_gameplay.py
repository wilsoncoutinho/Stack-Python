"""Automated gameplay tests for Stack Attack Reborn."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Must set SDL to dummy before importing main
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1, 1))

# Now import game modules by exec'ing the setup portion
main_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "main.py"))
exec_globals = {"__file__": main_path, "__name__": "__test__"}
with open(main_path) as f:
    code = f.read()
# Execute everything before the main loop
setup_code = code.split("while True:")[0]
exec(compile(setup_code, main_path, "exec"), exec_globals)

# Pull out what we need
TILE_SIZE = exec_globals["TILE_SIZE"]
COLS = exec_globals["COLS"]
ROWS = exec_globals["ROWS"]
BOMB_TYPE = exec_globals["BOMB_TYPE"]
POWERUP_HELMET_TYPE = exec_globals["POWERUP_HELMET_TYPE"]
NUM_CRATE_TYPES = exec_globals["NUM_CRATE_TYPES"]
Personagem = exec_globals["Personagem"]
CHAR_DEFS = exec_globals["CHAR_DEFS"]
find_line_matches = exec_globals["find_line_matches"]
apply_board_gravity = exec_globals["apply_board_gravity"]
handle_bomb = exec_globals["handle_bomb"]
register_push_animation = exec_globals["register_push_animation"]

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name}")

def fresh_board():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]

def fresh_player(char_id="pete"):
    return Personagem(5, ROWS - 1, char_id)

# ─── TEST GROUP 1: Player Initialization ───
print("\n=== Player Initialization ===")
for cdef in CHAR_DEFS:
    p = fresh_player(cdef["id"])
    test(f"{cdef['name']} creates OK", p.alive and p.char_id == cdef["id"])
    test(f"{cdef['name']} super_jumps={cdef['super_jumps']}", p.super_jumps_left == cdef["super_jumps"])
    test(f"{cdef['name']} can_bomb={cdef['bomb']}", p.can_bomb == cdef["bomb"])

# ─── TEST GROUP 2: Movement ───
print("\n=== Movement ===")
board = fresh_board()
p = fresh_player()
# Simulate ground position
p.y = float((ROWS - 1) * TILE_SIZE)  # stand on bottom
p.no_chao = True
p.vel_y = 0

old_x = p.x
teclas_right = {"esquerda": False, "direita": True}
p.atualizar(teclas_right, board)
test("Move right increases x", p.x > old_x)
test("Direction set to 1 (right)", p.dir == 1)

p2 = fresh_player()
p2.y = float((ROWS - 1) * TILE_SIZE)
p2.no_chao = True
old_x2 = p2.x
teclas_left = {"esquerda": True, "direita": False}
p2.atualizar(teclas_left, board)
test("Move left decreases x", p2.x < old_x2)
test("Direction set to -1 (left)", p2.dir == -1)

# ─── TEST GROUP 3: Jumping ───
print("\n=== Jumping ===")
board = fresh_board()
p = fresh_player("lizzie")  # Has super jumps
floor_y = ROWS * TILE_SIZE
p.y = float(floor_y - p.PH)  # correct floor position
p.no_chao = True
p.vel_y = 0

p.pular()
test("Jump queued", p.jump_queued)
p.atualizar({"esquerda": False, "direita": False}, board)
test("After jump update, vel_y < 0", p.vel_y < 0)
test("No longer on ground", not p.no_chao)

p2 = fresh_player("lizzie")
p2.y = float(floor_y - p2.PH)
p2.no_chao = True
initial_sj = p2.super_jumps_left
p2.super_pular()
test("Super jump queued", p2.super_jump_queued)
p2.atualizar({"esquerda": False, "direita": False}, board)
test("Super jump vel_y < normal jump", p2.vel_y < -7.0)
test("Super jumps decremented", p2.super_jumps_left == initial_sj - 1)

# Pete has 0 super jumps
p3 = fresh_player("pete")
p3.y = float((ROWS - 1) * TILE_SIZE)
p3.no_chao = True
p3.super_pular()
p3.atualizar({"esquerda": False, "direita": False}, board)
test("Pete can't super jump (0 available)", p3.super_jumps_left == 0)

# ─── TEST GROUP 4: Match-3 System ───
print("\n=== Match-3 Combos ===")
# Horizontal match
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][0] = 1; b[11][1] = 1; b[11][2] = 1
matched = find_line_matches()
test("Horizontal 3-match detected", len(matched) == 3)
test("Correct cells matched", matched == {(0,11),(1,11),(2,11)})

# No match with only 2
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][0] = 1; b[11][1] = 1
matched = find_line_matches()
test("2 in a row = no match", len(matched) == 0)

# Vertical match
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[9][5] = 2; b[10][5] = 2; b[11][5] = 2
matched = find_line_matches()
test("Vertical 3-match detected", len(matched) == 3)

# 4 in a row
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][0] = 3; b[11][1] = 3; b[11][2] = 3; b[11][3] = 3
matched = find_line_matches()
test("4-match detected (4 cells)", len(matched) == 4)

# Mixed types no match
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][0] = 1; b[11][1] = 2; b[11][2] = 1
matched = find_line_matches()
test("Mixed types = no match", len(matched) == 0)

# Bombs don't match
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][0] = BOMB_TYPE; b[11][1] = BOMB_TYPE; b[11][2] = BOMB_TYPE
matched = find_line_matches()
test("Bombs excluded from matching", len(matched) == 0)

# ─── TEST GROUP 5: Board Gravity ───
print("\n=== Board Gravity ===")
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[5][3] = 1  # floating crate
apply_board_gravity()
b = exec_globals["board"]
test("Crate falls to bottom row", b[11][3] == 1 and b[5][3] == 0)

exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[11][3] = 2  # bottom crate
b[5][3] = 1   # floating crate
apply_board_gravity()
b = exec_globals["board"]
test("Crate stacks on top", b[10][3] == 1 and b[11][3] == 2)

# ─── TEST GROUP 6: Bomb Explosion ───
print("\n=== Bomb Explosion ===")
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
# Fill 3x3 around (5,5)
for dx in range(-1, 2):
    for dy in range(-1, 2):
        b[5+dy][5+dx] = 1
exec_globals["player"] = fresh_player()
exec_globals["player"].x = 0.0  # far away
exec_globals["player"].y = float((ROWS-1) * TILE_SIZE)
exec_globals["falling_boxes"] = []
exec_globals["push_animations"] = []

handle_bomb(5, 5)
b = exec_globals["board"]
all_cleared = all(b[5+dy][5+dx] == 0 for dx in range(-1, 2) for dy in range(-1, 2))
test("Bomb clears 3x3 area", all_cleared)

# Bomb at edge
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
b[0][0] = 1; b[0][1] = 1; b[1][0] = 1; b[1][1] = 1
handle_bomb(0, 0)
b = exec_globals["board"]
test("Edge bomb doesn't crash", b[0][0] == 0 and b[1][1] == 0)

# ─── TEST GROUP 7: Stun Mechanic ───
print("\n=== Stun Mechanic ===")
p = fresh_player()
p.y = float((ROWS-1) * TILE_SIZE)
p.no_chao = True
p.ativar_stun(25)
test("Stun sets timer", p.stun_timer == 25)
test("Stun zeroes velocity", p.vel_x == 0)

board = fresh_board()
p.atualizar({"esquerda": True, "direita": False}, board)
test("Stunned player can't move", p.vel_x == 0)
test("Estado is stun", p.estado == "stun")

# ─── TEST GROUP 8: Difficulty & Crane Count ───
print("\n=== Difficulty Scaling ===")
exec_globals["difficulty"] = 1.0
test("Diff 1 = 1 crane", exec_globals["current_crane_count"]() == 1)
exec_globals["difficulty"] = 2.0
test("Diff 2 = 2 cranes", exec_globals["current_crane_count"]() == 2)
exec_globals["difficulty"] = 5.0
test("Diff 5 = 5 cranes (max)", exec_globals["current_crane_count"]() == 5)
exec_globals["difficulty"] = 10.0
test("Diff 10 = capped at 5", exec_globals["current_crane_count"]() == 5)

# ─── TEST GROUP 9: Powerup Helmet ───
print("\n=== Powerup Helmet ===")
# Test POWERUP_HELMET_TYPE value overlap check
test("Helmet type != bomb type", POWERUP_HELMET_TYPE != BOMB_TYPE)
test("Helmet type (5) is within crate range", 1 <= POWERUP_HELMET_TYPE <= NUM_CRATE_TYPES)

# ─── TEST GROUP 10: Bomb Placement (Sam only) ───
print("\n=== Bomb Placement ===")
exec_globals["board"] = fresh_board()
b = exec_globals["board"]
sam = fresh_player("sam")
sam.y = float((ROWS-1) * TILE_SIZE)
sam.no_chao = True
sam.dir = 1
exec_globals["player"] = sam
exec_globals["falling_boxes"] = []
exec_globals["push_animations"] = []
result = sam.try_place_bomb(b)
test("Sam can place bomb", result == True)
target_x = sam.grid_x + 1
test("Bomb placed on board", b[sam.grid_y][target_x] == BOMB_TYPE)

pete = fresh_player("pete")
exec_globals["board"] = fresh_board()
b2 = exec_globals["board"]
result2 = pete.try_place_bomb(b2)
test("Pete cannot place bomb", result2 == False)

# ─── TEST GROUP 11: Sprite Frame Bounds ───
print("\n=== Sprite Frame Safety ===")
for cdef in CHAR_DEFS:
    p = fresh_player(cdef["id"])
    for estado in ["parado", "andando", "empurrando", "pulando", "stun"]:
        p.estado = estado
        p.dir = 1
        try:
            spr = p.get_sprite()
            ok = spr is not None
        except IndexError:
            ok = False
        test(f"{cdef['id']} sprite '{estado}' dir=1 safe", ok)
    # Test left direction
    for estado in ["andando", "empurrando", "pulando"]:
        p.estado = estado
        p.dir = -1
        try:
            spr = p.get_sprite()
            ok = spr is not None
        except IndexError:
            ok = False
        test(f"{cdef['id']} sprite '{estado}' dir=-1 safe", ok)

# ─── TEST GROUP 12: Full Line Clear ───
print("\n=== Full Line Clear ===")
exec_globals["board"] = fresh_board()
exec_globals["score"] = 0
exec_globals["combo_count"] = 0
exec_globals["difficulty"] = 1.0
exec_globals["line_clear_flash"] = 0
exec_globals["explosion_anim_cells"] = []
exec_globals["explosion_anim_timer"] = 0
b = exec_globals["board"]
for x in range(COLS):
    b[11][x] = (x % NUM_CRATE_TYPES) + 1  # fill bottom row with varied types
exec_globals["do_post_landing"]()
test("Full row cleared (score increased)", exec_globals["score"] >= 100)
test("Flash activated", exec_globals["line_clear_flash"] > 0)

# ─── TEST GROUP 13: Crate Sprite Mapping ───
print("\n=== Crate Sprite Mapping ===")
crate_sprite_for_type = exec_globals["crate_sprite_for_type"]
for ct in range(1, NUM_CRATE_TYPES + 1):
    try:
        s = crate_sprite_for_type(ct)
        test(f"Crate type {ct} has sprite", s is not None)
    except Exception as e:
        test(f"Crate type {ct} has sprite", False)
try:
    s = crate_sprite_for_type(BOMB_TYPE)
    test("Bomb type has sprite", s is not None)
except Exception:
    test("Bomb type has sprite", False)

# ─── SUMMARY ───
print(f"\n{'='*50}")
print(f"RESULTS: {passed} passed, {failed} failed out of {passed+failed} tests")
if failed == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {failed} test(s) failed!")
    sys.exit(1)
