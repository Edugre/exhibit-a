# HW #4 playtest kit

Everything a facilitator needs to run both rounds the same way. Record what testers **actually do and say**:
the spec doesn't accept invented testers or results, and neither do we. Fill in `hw4_playtest_log.csv`
(one row per person per session) as you go, then copy the counts into `hw4_report.md`.

---

## Before Round 1 (team, once)

- [ ] **Pick the build and freeze it.** Use `main` at the commit you test (write the short hash in the log, e.g.
      `550d034`), and tag it: `git tag hw4-r1 && git push origin hw4-r1`. Don't change code between Round 1 sessions.
- [x] **Controls and objective in game.** The menu shows a card with the job and every key; it's on screen for
      the first 8 seconds of each heist and whenever a player holds Tab. Don't hand out the printed card below:
      watching whether testers find the in-game one is part of the test. Keep the printed version only as a
      backup if the build fails.
- [ ] **Room seed 42 for every session.** Type `42` in the menu's room seed field on the host. Everyone gets the
      same rooms: Lobby → Hall of Arms (Laser Corridor) → Sculpture Hall → Security Office → Gallery + Vault,
      with the same loot and the same two night staff.
- [ ] **Two machines (or two windows) ready**, the host started, the client one click from Join.
- [ ] Print or open this kit and the log.

## Who plays

The game needs two players per session. Testers must be **outside the team** (friends, family, classmates).

- Best: two outside testers play together (P1 + P2 in one session, P3 + P4 in another).
- If you only have three people: P3 plays with a **team member as partner**. The partner must follow, not lead:
  no pointing, no explaining, no solving puzzles for P3. Log it in the *Assistance* column and in the limitations.
- Round 2: at least one Round 1 tester comes back (e.g. P1, with P2 or a team member).
- Ask permission before recording anyone. Don't collect names: use P1, P2, P3...

## Starting instruction (read exactly this to every tester)

> "You and your partner are thieves breaking into a museum at night. Your goal is to steal the Last Book of
> Alexandria from the vault and get it into your van before time runs out. If the librarian catches either of
> you, it's over. Please think out loud as you play. I won't help unless you're completely stuck."

**Backup controls card** (only if the in-game card isn't available; log it if used):

| | |
|---|---|
| Move / look | W A S D / mouse |
| Jump / sneak | Space / Ctrl |
| Pick up, pocket loot, drop the book | E |
| Hotbar slot | 1-4 or mouse wheel |
| Throw, fire the jammer, pry a case (what's in your hand) | Left click |
| Fire the jammer from anywhere | Q |
| Put down what's in your hand | G |

## Task and limit

- **Task:** steal the book and deliver it to the van.
- **Limit:** the in-game timer (4:30 for this run) or one caught attempt, whichever comes first. If they lose
  early and there's time, they may restart once; log both attempts.
- **Restart:** the Restart button on the end card (it shows the "restart without relaunching" requirement).

## The two test questions and what to measure

**Q1. Can a new pair work out the Hall of Arms' laser grid (the switch hand-off, or spending a jammer charge) without a hint?**
- ⏱ *Seconds* from the first time either player sees the laser grid to both players being past it.
- 🔢 *Alarms* set off by walking into the beams.
- ✔ *How they got past*: switches / jammer / both / didn't.
- 🔢 *Hints* given at the grid.

**Q2. Do players understand the crowbar's cost: when they break a case open, do they expect the librarian, and do they still choose to?**
- ✔ *Picked up the crowbar?* (Y/N)
- 🔢 *Cases broken*, and which ones.
- ⏱ *Seconds* from a break until the librarian reaches or spots them (or "never").
- 💬 Debrief answer to "What happened after you broke the case?" (understood / partly / no).

**Every session also logs:** outcome (won / caught / timed out), time at the end, the haul, total hints, and
whether the player held Tab to bring the controls back (Y/N).

## During the session

- Say nothing beyond the starting instruction unless they're completely stuck for **60 seconds** at one spot.
  Then give the **smallest** hint (e.g. "Look around the room"), write down the exact words and the time, and
  count it as a hint.
- Write **observations, not opinions**: "P2 walked into the beams twice" (yes), "the lasers are confusing" (save
  that for later).
- Note when thinking aloud changes what they do.
- If the game crashes or blocks play, write it down, fix it, and run another session.

## Debrief (ask every tester the same questions, write their words)

1. "What did you think the goal was?"
2. "Where were you unsure what to do?"
3. "How did you get past the laser grid? How did you decide?"
4. "What happened after you broke the case?" (or "Why didn't you use the crowbar?")
5. "What caused your last failure or success?"
6. Optional: "From 1 to 5, how clear was what to do next?" (only as a supplement)

## Between rounds: revise

1. List the most important problems you **observed** (cite session rows).
2. Make **at least two distinct changes** justified by them (two cosmetic edits to the same cue count as one).
3. Note the build (commit) and tag it `hw4-r2`.
4. Round 2: a returning tester plays the **same task, seed and measures**. Acknowledge that they already know the game.

## Round 2 checklist

- [ ] Same seed (42), same starting instruction, same limit, same measures.
- [ ] At least one returning tester (familiarity is a limitation: say so).
- [ ] At least one of your changes is checked with a comparable measure.
- [ ] Mixed or worse results are reported honestly: full credit doesn't need every number to improve.
