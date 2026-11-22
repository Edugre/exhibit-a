# HW #4 spec

Source: instructor feedback on the project proposal (Kianoosh Boroojeni).
Questions or concerns go to the instructor via Canvas message.

## HW #4 scope (summary)

Start only after the first heist (HW #3) works reliably. Then add:

- A small number of additional rooms.
- Procedural room ordering.
- One further gadget.

Rules that still apply:

- The team writes the gameplay rules: puzzle conditions, artifact ownership and scoring,
  guard decisions, noise/distraction, timer, and outcome logic.
- Godot may provide rendering, physics, navigation support, and networking transport.
  Disclose these and credit external assets in the README.
- No prebuilt heist or puzzle gameplay packages.

Out of scope: playtesting, polish and balance (HW #5). Grappling and a large museum are
stretch goals.

---

## Full instructor feedback (verbatim)

Decision on the project proposal: Approve with Minor Revisions. Revised proposal: Exhibit A
remains a two-player online co-op museum heist using Godot and GDScript. Godot is approved
for the proposed custom puzzle, noise, guard, and gadget systems. Keep the initial museum
small so networking and a complete heist can be demonstrated together.

HW#3 will contain one connected museum room and an extraction area, with two controllable
players, one cooperative switch/pressure-plate puzzle that opens access to an artifact,
artifact pickup/carrying, and delivery to the van. Include one simple guard with
patrol/chase states, a visible short countdown, and a throwable object that distracts the
guard. Delivering the artifact before time expires wins; capture or timeout ends the
attempt, with synchronized restart and visible artifact/time/alert feedback. Networking
should synchronize these essential interactions, not only player positions. Placeholder
rooms and objects are acceptable.

Write the puzzle conditions, artifact ownership and scoring, guard decisions,
noise/distraction rules, timer, and outcome logic yourselves. Godot may provide rendering,
physics, navigation support, and networking transport; disclose these and credit external
assets in the README. Do not use prebuilt heist or puzzle gameplay packages.

HW#4 will add a small number of additional rooms, procedural room ordering, and one further
gadget after the first heist works reliably. HW#5 will focus on playtesting, cooperative
clarity, feedback, balance, and polish. Grappling and a large museum remain stretch goals.

If you have questions or concerns about this updated proposal, contact me (Kianoosh
Boroojeni) via Canvas message. Otherwise, begin working on your HW#3.
