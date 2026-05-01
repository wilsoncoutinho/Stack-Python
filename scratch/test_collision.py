
import pygame
import os

# Mocking some constants and structures to test the logic
TILE_SIZE = 40
COLS, ROWS = 12, 12
BOMB_TYPE = 8
POWERUP_HELMET_TYPE = 6

board = [[0 for _ in range(COLS)] for _ in range(ROWS)]
falling_boxes = []
push_animations = []

def is_cell_occupied(x, y):
    if not (0 <= x < COLS and 0 <= y < ROWS):
        return True
    if board[y][x] != 0:
        return True
    for fb in falling_boxes:
        if fb["x"] == x and fb["y"] == y:
            return True
    for pa in push_animations:
        if pa["x"] == x and pa["y"] == y:
            return True
    return False

# Test 1: Spawning overlap
print("Test 1: Spawning overlap")
drop_x = 5
drop_row = 2
falling_boxes.append({"x": drop_x, "y": drop_row, "type": 1})
print(f"Is occupied at ({drop_x}, {drop_row})? {is_cell_occupied(drop_x, drop_row)}")

# Test 2: Push animation overwrite
print("\nTest 2: Push animation overwrite")
board[10][5] = 1
# Simulate box finish animation at (10, 5)
anim = {"x": 5, "y": 10, "type": 2}
if board[anim["y"]][anim["x"]] != 0:
    print(f"CONFLICT! Cell ({anim['x']}, {anim['y']}) already has {board[anim['y']][anim['x']]}")
    # Fix: find next available row above
    target_y = anim["y"]
    while target_y >= 0 and board[target_y][anim["x"]] != 0:
        target_y -= 1
    if target_y >= 0:
        print(f"Fixed: Moving to {target_y}")
        board[target_y][anim["x"]] = anim["type"]
    else:
        print("Nowhere to go!")
else:
    board[anim["y"]][anim["x"]] = anim["type"]

print(f"Board[10][5]: {board[10][5]}, Board[9][5]: {board[9][5]}")
