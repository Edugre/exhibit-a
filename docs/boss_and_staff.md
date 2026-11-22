# The librarian and her staff: design note

Alex's idea, written up for the team to agree on. It changes guard rules, which the course says we write
together, so nothing here merges until Eduardo and Jonathan have had their say.

## The idea
Today every guard in a run (up to five) is the same old librarian, and any of them ends the heist. She
stops feeling special. Instead:

- **The librarian is the one boss.** There is only one of her, and she roams the whole museum.
- **Her staff are her eyes.** Calmer night staff patrol the rooms. They never catch you: when one spots
  you, they ring a hand bell, and she comes.

Seeing a staff member is still frightening, because it means she is on her way. But the rooms are
calmer, and the one deadly thing in the building is her.

## Rules (proposed)
**Staff**
- Patrol their room on its waypoints, with the same sight cone, range and suspicion build-up as the
  librarian (what you see is what catches you).
- When the meter fills they stop, turn to the player and ring a hand bell. While they can still see
  the player they ring again every 3 s. Once the player is out of sight they go back to their rounds.
- Never chase, never catch.
- The Heel distracts them and a statue pose fools them, exactly as with the librarian.

**The librarian**
- Walks a long route through every room, the entrance to the vault and back, pausing at each end.
- Hears every bell, wherever she is, and hurries to where the player was seen (her investigate speed:
  faster than her patrol, slower than her chase), then looks around and goes back to her route.
- If she sees a player herself, it is her normal chase, and her catch ends the heist, as now.
- On restart she starts again in the vault.

**Warnings**
- The bell is heard where it rings, and "She's coming…" shows on both players' screens.

## Where it changes things
| Change | File(s) | Owner |
|---|---|---|
| Staff behaviour: extends `Guard`, replaces only the moment she would start a chase | `scripts/staff.gd` (new) | B |
| Staff look: placeholder (the player body in a pale uniform, with a lantern beam) | `scripts/staff_model.gd`, `scenes/staff_model.tscn`, `scenes/staff.tscn` (new) | B |
| The boss: extends `Guard`, builds her route from the rooms after each build | `scripts/boss.gd` (new) | B |
| She lives in the museum, not in a room | `scenes/museum.tscn` (one node added) | **A** |
| Rooms swap their guards for staff | Sculpture Hall, Security Office (B); Laser Corridor (**C**); vault (**A**) | mixed |
| The bell | `assets/characters/staff_bell.wav` and its generator (new) | B |

`guard.gd`, `game_state.gd`, `museum_layout.gd` and the noise system are unchanged.

## Networking
As everywhere else: the host decides. Staff and the librarian are guards, synced the same way. A staff
member's ring count is synced, and every peer plays the bell and shows the warning when it changes.

## Not decided yet (for the team)
- Is this HW #4 or HW #5? It is built on its own branch so `main` stays as it is until we choose.
- The staff's proper look: the placeholder reuses the player body. A real staff character (sculpted,
  rigged and animated like the librarian) is its own art task.
- Numbers to tune by playing: ring interval, how fast she hurries, how long she searches.
