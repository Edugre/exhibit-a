# Exhibit A: HW #4 design and playtest report

**Team:** Eduardo Goncalvez (6526311), Alex Waisman (6529880), Jonathan Serrano (6524435)
**Build tested:** `[TEAM: commit hash / tag hw4-r1]` (Round 1), `[TEAM: hw4-r2]` (Round 2). Godot 4.7.2 stable, Windows 11.
**Segment:** one full heist on room seed 42: plaza → Lobby → Hall of Arms (Laser Corridor) → Sculpture Hall → Security Office → Gallery + Vault → back out to the van.

> **Draft status.** Sections 1–4 and 9 are drafted from the build and need the team to confirm or edit (marked
> **[TEAM]**). Sections 5–8 must be filled from the real sessions in `hw4_playtest_log.csv`. Don't fill them
> with anything that didn't happen.

---

## 1. Intended experience and test questions

**Intended experience [TEAM: confirm or rewrite]:** *Two players should feel tense but in control as they cover
for each other to get the book out, and should understand why they were caught or why a risk paid off.*

**Test questions:**
1. **Q1:** Can a new pair work out the Hall of Arms' laser grid (the switch hand-off, or spending a jammer
   charge) without a hint? *Measures:* seconds from first seeing the grid to both players past it; alarms set off;
   method; hints.
2. **Q2:** Do players understand the crowbar's cost: when they break a case, do they expect the librarian, and do
   they still choose to? *Measures:* crowbar taken; cases broken; seconds from a break to the librarian
   arriving; debrief answer.

## 2. The segment, mapped

![Annotated top-down map of the seed-42 run](hw4_map.png)

*Rendered from the build (ceilings hidden), with markers placed from the live nodes.*

| Moment | Where | What it does |
|---|---|---|
| **Start** | Plaza, by the van | Both players spawn; the timer starts when the second joins. |
| **Introduce** | Lobby | No guards. The jammer (ticket desk), the crowbar and the Heel (coat check) are in reach; loot glints and the prompt teaches "E to pocket". The hotbar's slots fill as they pick things up. |
| **Introduce co-op + choice** | Hall of Arms | No staff this run. The laser grid blocks the middle: one player holds a switch while the other crosses, then the far switch brings the first over. Or spend one of the jammer's two charges for both at once. The Shield of Achilles case ($5,000) is the first crowbar temptation. |
| **Practice stealth** | Sculpture Hall | One night staff on a patrol loop; crates and draped statues for cover; the Heel to lure her; statue plinths to pose on. |
| **Practice / breather** | Security Office | No staff this run (guard budget); the librarian's route passes through. |
| **Test (combined)** | Gallery + Vault | A staff patrol around both plates and the librarian's start point. Both players must stand on the Achilles and Helen plates **at the same time** to open the vault; then one carries the book (both hands) back through every room under the timer. |
| **End** | Plaza, the van | The book in the van wins; a catch or the timer running out loses. The end card's Restart starts a new run without relaunching. |

**Meaningful choices:**
- **Jammer now or later:** two charges per heist. Spend one at the grid to skip the switch hand-off, or save it
  for the way back with the book.
- **Crack a case or not:** a case's prize is worth $1,500–$5,000 (small loot is $150–$500), but breaking one is a
  10 m noise and the librarian hears it anywhere and comes. The haul only counts if you escape.
- **Who carries the book:** it takes both hands. The carrier can't throw or use the jammer or crowbar; the
  other player has to cover.

**How the camera and interface support the plan:** first-person camera; the top bar shows time left, the
book's state ("locked in the vault", "vault open!", "carried by your partner"), the haul and the alert. Prompts
name what you're aiming at ("Press E to pocket: Ring of Gyges ($300)", "Left click: pry it open (loud!)"). The
hotbar shows what you hold and the jammer's charges. Each vault plate lights a lamp on the vault door while it's
pressed. "She's coming…" appears on both screens when a staff rings or a case breaks. Loot glints. EXIT signs
and cold moonlight at the front doors mark the way out. The objective and every control are on a card beside
the main menu, on screen for the first 8 seconds of each heist, and back whenever a player holds Tab ("Tab:
controls" stays on the top bar).

## 3. How the systems interact

**Guard budget × noise × the librarian's response.** A run keeps one night staff per two rooms behind the
lobby (`GuardBudget.ROOMS_PER_STAFF = 2`): two staff, plus the librarian, who roams every room. Staff never catch;
they ring a bell every 3 s while they can see you, and every bell sends the librarian hurrying to where you were
seen (her investigate speed is 3 m/s; her chase speed is 4.5 m/s, faster than sneaking at 2.5 but slower than
walking at 5). Noise works on distance: a thrown Heel is heard within 8 m, a coin within 6 m, and a breaking
case within 10 m. A case is also heard by the librarian anywhere.

So the number of staff decides how often the librarian is pulled across the museum, and that decides how safe
the risky actions (a loud case, a mistimed hand-off at the grid) really are.

**A parameter change and its consequence:** with `ROOMS_PER_STAFF = 1`, a normal run would keep four staff
instead of two: every room behind the lobby watched. Bells would come far more often, the librarian would rarely
be on her quiet route, and breaking a case would almost always have a staff member within 10 m. Pocketing loot
would become a much worse bet, and the timer (180 s + 30 s per pool room) would get tight. Two staff leave some
quiet rooms where the crowbar is tempting. **[TEAM: if a playtest shows this, cite it.]**

**Timer × room order:** the seed decides the rooms, and the timer grows by 30 s per pool room, so a three-room
run gets 4:30. Carrying the book means walking the whole route twice, so time pressure peaks on the way out.

## 4. HW #3 feedback response **[TEAM: paste the HW #3 grading feedback (released Nov 12) and fill in]**

| Feedback item | Change or justified deferral | File/system or build evidence | Verification / next step |
|---|---|---|---|
| | | | |
| | | | |

## 5. Test method

- **Participants:** [TEAM] testers from outside the team, IDs P1–P[n]. Two players per session (the game is
  two-player co-op); where only one outside tester was available, a team member partnered and was told to follow,
  not lead (logged as assistance).
- **Sessions:** [TEAM: dates]. Round 1: [n] sessions. Round 2: [n] sessions with returning tester(s) [IDs].
- **Same for everyone:** build [hash], room seed 42, the starting instruction and controls card in
  `hw4_playtest_kit.md`, the task (book to the van), and the limit (4:30 timer or one catch).
- **Hint rule:** a hint only after 60 s stuck in one spot; exact words and time logged.

## 6. Round 1 results **[TEAM: from the log, counts only; no claims beyond the sample]**

| Tester / round / build | Task and limit | Outcome and measures | Observation / player response | Assistance |
|---|---|---|---|---|
| P1 / R1 / | | | | |
| P2 / R1 / | | | | |
| P3 / R1 / | | | | |

**Q1:** [e.g. "x of y pairs got past the grid without a hint; median time z s; methods ..."]
**Q2:** [e.g. "x of y took the crowbar; x broke a case; x said they expected the librarian"]

## 7. Revisions based on Round 1 (at least two distinct changes)

| Observed problem (cite the session) | Hypothesis | Implemented change (file, build) | Retest result and limitation |
|---|---|---|---|
| | | | |
| | | | |

*Changes made before Round 1 (the hotbar, the guard budget, loot, the sign and guard-collision fixes) were not
driven by outside testers and are not counted here.*

## 8. Round 2 retest and limitations **[TEAM]**

- Returning tester(s): [IDs], same seed, task and measures.
- Comparison: [measure in R1 → R2].
- Limitations: returning testers already know the game; a small sample (n = [ ]); [team-member partner in some
  sessions]; [anything else that happened].

## 9. HW #5 plan (prioritized) **[TEAM: reorder after the playtests]**

1. Fix the problems found in the playtests that Round 2 didn't resolve.
2. Sneaking that matters: slower detection and quieter steps (today it only slows you down).
3. Finish scoring: a time bonus and an alert penalty on top of the haul.
4. Balance from the playtests: guard budget, noise radii, loot values, the timer.
5. Real staff character art (the placeholder reuses the player body), and first-person hands.
6. Lobby polish: a ready-up screen and showing the host's IP for joining.
