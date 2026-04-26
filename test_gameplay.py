import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import unittest
from unittest.mock import patch
import pygame

# Initialize pygame normally but with dummy drivers
os.environ["SDL_AUDIODRIVER"] = "dummy"
pygame.init()
pygame.mixer.init()

import main

class TestGameplay(unittest.TestCase):
    def setUp(self):
        main.reset_game(1.0)
        
    def test_initial_state(self):
        self.assertEqual(main.score, 0)
        self.assertTrue(main.player.alive)
        self.assertEqual(main.player.grid_x, 5)
        self.assertEqual(main.player.grid_y, main.ROWS - 1)
        
    def test_line_matches(self):
        # Create a horizontal match
        main.board[main.ROWS-1][0] = 1
        main.board[main.ROWS-1][1] = 1
        main.board[main.ROWS-1][2] = 1
        
        matches = main.find_line_matches()
        self.assertIn((0, main.ROWS-1), matches)
        self.assertIn((1, main.ROWS-1), matches)
        self.assertIn((2, main.ROWS-1), matches)

    def test_gravity(self):
        # Place a block floating
        main.board[main.ROWS-3][5] = 2
        main.apply_board_gravity()
        # It should fall to ROWS-1
        self.assertEqual(main.board[main.ROWS-1][5], 2)
        self.assertEqual(main.board[main.ROWS-3][5], 0)

    def test_player_jump(self):
        # Let physics resolve initial spawn (snaps to floor)
        main.player.atualizar({"esquerda": False, "direita": False}, main.board)
        
        main.player.pular()
        self.assertTrue(main.player.jump_queued)
        
        # Call update with no keys to apply jump
        teclas = {"esquerda": False, "direita": False}
        main.player.atualizar(teclas, main.board)
        
        self.assertEqual(main.player.estado, "pulando")
        self.assertLess(main.player.vel_y, 0) # Moving up
        
    def test_player_push(self):
        # Let physics resolve initial spawn
        main.player.atualizar({"esquerda": False, "direita": False}, main.board)
        
        # Place a block to the right
        px = main.player.grid_x
        py = main.player.grid_y
        main.board[py][px + 1] = 1
        
        # Face right
        main.player.dir = 1
        
        # Move player exactly next to the block (gap <= 3)
        main.player.x = (px + 1) * main.TILE_SIZE - main.player.PW - 1
        
        prox = main.player._proximo_caixa(main.board)
        self.assertIsNotNone(prox)
        self.assertEqual(prox[0], "board")
        self.assertEqual(prox[1], px + 1)
        
        pode = main.player._pode_empurrar_para(main.board, px + 1, py)
        self.assertTrue(pode)
        
        # Actually push it
        main.player._empurrar_caixa(main.board, px + 1, py, px + 2)
        self.assertEqual(main.board[py][px + 1], 0)
        
        # Box should be animating to px + 2
        self.assertEqual(len(main.push_animations), 1)
        self.assertEqual(main.push_animations[0]["x"], px + 2)
        
    def test_falling_crate_crush(self):
        # Let physics resolve
        main.player.atualizar({"esquerda": False, "direita": False}, main.board)
        
        # Player is at x=5, y=11
        px = main.player.grid_x
        py = main.player.grid_y
        
        # Spawn falling crate exactly above player
        main.falling_boxes.append({
            "x": px,
            "y": py - 1,
            "type": 1,
            "px": float(px * main.TILE_SIZE),
            "py": float(main.player.y) # Bottom of crate overlaps top of player by TILE_SIZE
        })
        
        # Player standing still
        main.player.check_falling_collision(main.falling_boxes)
        # Assuming the collision logic triggers a crush
        self.assertFalse(main.player.alive)

if __name__ == '__main__':
    unittest.main()
