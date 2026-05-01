# Stack Attack Reborn — Roadmap & Status Report

## ✅ Priority 1: Sound Effects System — DONE

The original `.mmf` (Yamaha SMAF) files cannot be loaded by pygame — they contain synthesizer instructions, not PCM audio. I solved this by generating **14 procedural retro WAV sound effects** that match the original mobile game's feel.

### Sound Effects Created

| Sound | File | Duration | Trigger Points |
|-------|------|----------|----------------|
| Jump | `jump.wav` | 0.15s | Player normal jump |
| Super Jump | `super_jump.wav` | 0.20s | Player super jump |
| Push | `push.wav` | 0.12s | Pushing a crate |
| Land | `land.wav` | 0.10s | Falling crate lands |
| Explode | `explode.wav` | 0.35s | Crate stomp/headbutt/bomb detonation |
| Powerup | `powerup.wav` | 0.30s | Catching falling powerup crate |
| Bomb Place | `bomb.wav` | 0.15s | Sam places a bomb |
| Stun | `stun.wav` | 0.25s | Player gets stunned |
| Combo | `combo.wav` | 0.25s | Match-3 combo triggered |
| Line Clear | `line_clear.wav` | 0.40s | Full row cleared |
| Game Over | `game_over.wav` | 0.80s | Player dies |
| Menu Move | `menu_move.wav` | 0.05s | Navigate menus |
| Menu Select | `menu_select.wav` | 0.12s | Confirm selection |
| Helmet | `helmet.wav` | 0.20s | Helmet powerup pickup |

### Integration Points in Code

- **Menus**: Title (enter), Character Select (arrows + enter + esc), Level Select (arrows + enter + esc)
- **Gameplay**: Jump, super jump, push, land, stun, bomb place, bomb explode, game over
- **Scoring**: Combo matches, full line clears
- **Powerups**: Helmet pickup (horizontal + vertical collision), falling powerup catch

---

## ✅ Priority 2: Verify & Fix Missing Assets — DONE

### Current Asset Status

| Category | Status | Notes |
|----------|--------|-------|
| Background (`back.png`) | ✅ OK | Loads and scales properly |
| Title (`title.png`) | ✅ OK | Displays on title screen |
| Crate sheet (`crates.png`) | ✅ OK | 5+ crate types + explosion frames |
| Bomb (`black_bomb.png`) | ✅ OK | Uses `convert_alpha()` |
| Crane (`crane.png`) | ✅ OK | Multi-frame sprite sheet |
| Character sprites (6 chars) | ✅ OK | All `man*.png`/`woman*.png` present |
| Character icons (6 chars) | ✅ OK | All `iconman*.png`/`icwoman*.png` present |
| MIDI music (4 files) | ✅ OK | `title.mid`, `fullrow.mid`, `gameover.mid`, `extra.mid` |
| WAV sounds (14 files) | ✅ OK | Just generated in `assets/sounds/` |

> [!NOTE]
> There are extra bomb assets (`bomb_cropped.png`, `bomb_new.png`, `bomb_tight.png`) in extracted/ that aren't used. These are variants from earlier development — no action needed.

---

## ✅ Priority 3: Gameplay Testing Checklist — DONE

- [x] **Title screen**: Music plays, ENTER transitions, Q quits
- [x] **Character select**: Arrow navigation, card animations, ENTER to confirm, ESC to return
- [x] **Level select**: Up/Down navigation, ENTER starts game at correct difficulty
- [x] **Gameplay - Movement**: Left/Right smooth, WASD alternative works
- [x] **Gameplay - Jumping**: Normal jump (Up/W), Super jump (Space) with limited count
- [x] **Gameplay - Pushing**: Push crates left/right, push animation, stacking after push
- [x] **Gameplay - Cranes**: Spawn from both sides, drop crates at target column
- [x] **Gameplay - Falling crates**: Smooth visual interpolation, correct gravity tick
- [x] **Gameplay - Landing**: Sound plays, collision with player stuns
- [x] **Gameplay - Match-3 combos**: Horizontal and vertical matches clear, combo counter works
- [x] **Gameplay - Full line clear**: All cells in row → explosion animation → gravity
- [x] **Gameplay - Bombs**: Sam can place (B key), 3x3 area destruction, explosion sound + animation
- [x] **Gameplay - Bomb crate**: 6% spawn chance, explodes on landing
- [x] **Gameplay - Powerup (Helmet)**: Helmet crate spawns, pickup grants headbutt, timer in HUD
- [x] **Gameplay - Headbutt**: Jumping into falling crate with helmet active destroys it
- [x] **Gameplay - Stomp**: Landing on top of falling crate destroys it
- [x] **Gameplay - Death**: Crushed by crate → game over screen + music + SFX
- [x] **Gameplay - Difficulty**: Score increases difficulty, spawn rate increases, more cranes
- [x] **Game Over**: Overlay displayed, R to restart, Q to quit
- [x] **Sound effects**: All 14 sounds trigger at correct moments
- [x] **Music**: Title loop, game over, full row clear

---

## ✅ Priority 4: Code Quality & Polish — IN PROGRESS

### Error Handling
- [ ] Wrap all asset loading in try/except with fallback sprites/sounds
- [ ] Handle missing font gracefully (fallback to default pygame font)
- [ ] Graceful exit if critical assets are missing

### Potential Improvements
- [x] **Pause menu**: Retro TV "PAUSE" overlay and ad-system monetization
- [x] **High score system**: Persistent JSON storage, per-character records
- [x] **Difficulty scaling refinement**: Adjusted formula for faster progression
- [x] **Crate spawn balance**: Implemented logarithmic difficulty scaling and reasonable spawn caps.
- [x] **Visual polish**: Added screen shake on explosions/landings, and particle effects for jumps, landings, combos, and powerups.

### Code Organization
- [ ] Consider splitting into modules: `player.py`, `board.py`, `ui.py`, `sounds.py`
- [ ] Replace global variables with a `GameState` class
- [ ] Add type hints for better maintainability
