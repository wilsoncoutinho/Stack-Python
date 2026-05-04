"""
Stack Attack Reborn — Entry Point
"""
import pygame
import os
import asyncio
from constants import WIDTH, HEIGHT, HUD_H, CONTROLS_H

# Initialization must happen BEFORE importing modules that load assets
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT + HUD_H + CONTROLS_H))
pygame.display.set_caption("Stack Attack")

# Now we can import the rest
import renderer
renderer.set_screen(screen)

from game import run_game

async def main():
    await run_game()

if __name__ == "__main__":
    asyncio.run(main())
