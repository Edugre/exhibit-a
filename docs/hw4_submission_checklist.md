# HW #4: what's left before submitting

A handover list for whoever (or whichever agent) finishes the submission. The spec is
`C:\Users\eduar\Downloads\CAP4052_HW4_Playable_Alpha_and_Playtesting.pdf`. **Deadline:** Sunday Nov 22, 11:59 pm
(Canvas accepts submissions until Nov 24, 11:59 pm). **Limit:** one ZIP, **50 MB max**, or it isn't graded.

---

## Where things stand (as of `main` @ `e6aa2fb`)

**The game is done** for HW #4. It runs as one heist: plaza → lobby → three seeded rooms → gallery and vault →
back to the van. It has:
- an end card and a Restart button;
- a HUD, a hotbar, and the objective and controls card (hold Tab);
- the jammer, loot and the crowbar;
- the librarian plus a budget of night staff.

**Already written:**

| What | Where |
|---|---|
| Playtest kit (the facilitator script, task, measures, debrief questions) | `docs/hw4_playtest_kit.md` |
| Blank session log, one row per person per session | `docs/hw4_playtest_log.csv` |
| Annotated top-down map of the seed-42 run | `docs/hw4_map.png` |
| Report draft: sections 1–4 and 9 filled from the build; **5–8 need real session data** | `docs/hw4_report.md` |
| HW #3 feedback response table (the feedback asked for no corrections) | `docs/hw4_report.md` section 4 |
| GenAI statement, rewritten to be accurate | `README.md` → "GenAI statement" |
| Script that builds the submission ZIP (about 47 MB) | `tools/make_submission.py` |
| Windows export preset (for tester `.exe` builds) | `export_presets.cfg` |

**Builds and tags:**
- Git tag **`hw4-r1`** = `07053d7`: the Round 1 game code. The game code on `main` hasn't changed since; only docs
  and tools have.
- `build/` is git-ignored and holds:
  - `CAP4052_HW4_Goncalvez_Waisman_Serrano.zip` (47 MB): a **test** build of the submission ZIP. **Rebuild it at
    the end.**
  - `ExhibitA-submission-build.zip` (89 MB): a double-click `.exe` exported **from that submission ZIP**. Give this
    to testers. **It is not submitted.**
  - `ExhibitA-hw4-r1.zip` (125 MB): an older tester `.exe` at full textures. Not needed any more.

---

## The list, in order

### 1. Round 1 playtests ⚠ the critical path (15 + 10 rubric points depend on it)
- [ ] **At least three different people outside the team** (Alex and Jonathan don't count). Each session needs two players.
- [ ] Testers play `build\ExhibitA-submission-build.zip` (unzip, run `ExhibitA.exe`).
  - Host: type **42** in *Room seed*, then click **Host**.
  - Other player, same Wi-Fi: type the host's local IP (`192.168.4.28` on Eduardo's PC), then click **Join**.
  - Remote: use Radmin VPN or Tailscale, plus a screen-shared call so the facilitator can watch.
- [ ] Follow `docs/hw4_playtest_kit.md` exactly: the same starting instruction, the hint rule (only after 60 s
      stuck; log the exact words), the same debrief questions.
- [ ] If a team member has to be a tester's partner, they **follow, never lead**; log it in *Assistance*.
- [ ] Fill one row per person per session in `docs/hw4_playtest_log.csv`. Build column: `e6aa2fb (submission build)`.
- [ ] Measures for the two test questions:
  - **Q1 (laser grid):** seconds from first seeing the grid until both are past it, alarms, method (switches or
    jammer), hints.
  - **Q2 (crowbar cost):** took the crowbar? cases broken, seconds until the librarian arrives, debrief answer.
  - **Always:** outcome, time left, haul, total hints, used Tab?
- [ ] **Never invent or "clean up" data.** The policy is explicit: fabricated testers or results don't count.
      Keep failed sessions and every hint.

### 2. Two evidence-based changes
- [ ] From the Round 1 log, pick the **two most important observed problems**. Cite the session rows.
- [ ] Make **two distinct changes**. Two edits to the same cue count as one.
- [ ] Run the checks (below), merge, and tag `hw4-r2`:
  ```
  git tag -a hw4-r2 -m "Round 2 build"
  git push origin hw4-r2
  ```
- [ ] Rebuild the tester `.exe` from the new submission ZIP (see "How to build" below).
- [ ] Record each change in `docs/hw4_report.md` section 7: problem → hypothesis → change → retest.

### 3. Round 2 retest
- [ ] **At least one returning Round 1 tester** plays the revised build: the same task, seed 42 and measures.
- [ ] Log it in the CSV (`round = R2`).
- [ ] Compare at least one changed thing with the same measure. Say that a returning player already knows the game.
      Mixed or worse results are fine if reported honestly.

### 4. Finish the report: `docs/hw4_report.md` (about 3–5 pages)
- [ ] Header: fill the build lines (`[TEAM: ...]`).
- [ ] Section 1: confirm or rewrite the intended-experience sentence.
- [ ] Section 3: cite a playtest observation if one supports the guard-budget explanation (or delete the `[TEAM]` note).
- [ ] Section 4: confirm from Round 1 that sessions played the full loop (plates → book → van → end card → Restart).
- [ ] Sections 5–8: method, Round 1 results (counts like "2 of 3"), revisions, Round 2 comparison, limitations.
      **Only real data.**
- [ ] Section 9: reorder the HW #5 plan after the playtests.
- [ ] Remove every `[TEAM]` marker and the "Draft status" note.
- [ ] Optional but nice: export the report to PDF (`docs/hw4_report.pdf`). The raw notes are the CSV; add any
      handwritten notes as `docs/hw4_raw_notes.md`.

### 5. README fixes (`README.md`)
- [ ] **GenAI statement:** resolve the three `[TEAM]` markers:
  - Alex and Jonathan say whether and how they used AI in HW #4.
  - They confirm their HW #3 parts.
  - Everyone confirms they can explain the systems, including the parts Claude Code wrote.
- [ ] **Contributions:** add **Alex's and Jonathan's HW #4 work**. It's missing; only Eduardo's is listed. From git
      history:
  - **Alex:** the interior kit (K0); crates, cases, bookcases; Sculpture Hall, Twin Archives, Security Office; the
    two-plate gate; paintings, doorways, fixtures; the statues; the boss and staff.
  - **Jonathan:** the jammer core (C1), the laser grid (C2), the Laser Corridor (C3).
  - Have each confirm their own lines.
- [ ] **Gameplay video:** replace the HW #3 YouTube link with the new HW #4 video (step 6).
- [ ] **Known limitations is out of date.** Remove "The Laser Corridor's displays are the shared crates and cases
      until its own props are made" (it has its Hall of Arms set now). Add what's true now:
  - the night staff use a placeholder body;
  - there are no first-person hands;
  - guards walk through each other (on purpose);
  - the submission ZIP's textures are scaled to 1024 px (see "The submission zip").
- [ ] **"Trying a specific run":** mention the menu's *Room seed* field. It now describes only the editor's Debug Seed.
- [ ] **Tested platform:** the spec asks for the tested OS, engine version and entry point. Add one line: "Tested on
      Windows 11 with Godot 4.7.2 stable; entry point `scenes/main.tscn` (the project's main scene)."
- [ ] **Team:** the spec says "solo or two-person"; we're three. Keep all three names and IDs (the team was approved
      for HW #3).

### 6. Gameplay video (2–4 min)
- [ ] Record the **final** build from a **normal launch**:
  - the menu and controls card, host and join;
  - real play showing a choice or two: the jammer or switches at the grid, the crowbar on a case or not;
  - the HUD, loot toast and "She's coming…";
  - an **end condition** (the end card), then **Restart**.
- [ ] Upload as unlisted on YouTube and put the link in the README. It doesn't need to show testers.

### 7. Build and submit the ZIP (last!)
- [ ] Commit and merge everything above first: the script packages **only committed files** (`git ls-files`).
- [ ] From the repo root:
  ```
  python tools/make_submission.py
  ```
  This writes `CAP4052_HW4_Goncalvez_Waisman_Serrano.zip`. It must say **under 50 MB** (it was 47.1 MB; use
  `--max-side 512` if it grows).
- [ ] Optional sanity check: unzip it into an empty folder, open `project.godot` in Godot 4.7.2, let it import and
      press F5.
- [ ] It contains: the source, assets, README, `docs/` (report, CSV log, map, kit) and the asset tools. It also has
      `CLAUDE.md` (agent instructions). Leaving it in is consistent with the GenAI disclosure; delete it from the ZIP
      if you prefer.
- [ ] Upload to Canvas. **One** team member submits.

---

## How to build and check (for an agent)

- **Godot:** `C:\Tools\Godot\Godot_v4.7.2-stable_win64_console.exe` (exactly 4.7.2; never upgrade the project).
- **Headless checks after any change** (both must show no `SCRIPT ERROR` or `Parse Error`):
  ```
  godot --headless --editor --quit
  godot --headless --path . --quit-after 300
  ```
- **Tester `.exe` that matches the submission:**
  1. Run `python tools/make_submission.py <zip>`.
  2. Unzip it into an empty folder.
  3. In that folder: `godot --headless --editor --quit`, then
     `godot --headless --path . --export-release "Windows Desktop" build/ExhibitA.exe`.
  4. Zip the `.exe` with a short how-to.
- **Multiplayer can't be checked headlessly in one process.** Run two instances (host and client) and compare, or
  play it. The host is peer 1 and decides everything; clients only ask (see `CLAUDE.md`).

## Repo conventions and gotchas

- **Workflow:** branch `hw4/<topic>` → commit → push → PR to `main` → merge when Eduardo says so.
- **Commits:** Eduardo doesn't want a "Co-Authored-By: Claude" trailer on commits.
- **Don't commit Eduardo's local changes:** `project.godot` has an uncommitted local edit (the `[rendering]`
  d3d12 driver block moved), and there's an untracked `assets/interior/office/cctv_screen.gdshader.uid`. If you
  must add something to `project.godot` (an input action, say), stage only that hunk.
- **`docs/` has a `.gdignore`** so Godot doesn't import the CSV as translations. Keep it.
- **Gameplay rules are team-written** (course rule). Say so in the PR when a change alters rules.
- **Godot only reimports a `.gltf` when the `.gltf` changes.** `int_mesh.export()` stamps a hash of the `.bin` into
  it for that reason; keep using it for rebuilt props.
- **Seed 42** is the playtest run: Lobby → Hall of Arms (Laser Corridor) → Sculpture Hall → Security Office →
  Gallery and vault, with two night staff (Sculpture Hall, vault) plus the librarian.
