# ADR 0003: Hand interference handled by two-level continuity (contour + end)

Continuity is applied at **both** levels of the pipeline, not just end-selection. Among
the contours above min area, select the one **nearest the previous tip** — not the
largest. Largest-contour remains only the first-frame fallback when there is no previous
tip. This converts "hand blob bigger than mouse steals the crosshair" (a teleport, the
most demo-destroying failure) into "crosshair doesn't blink."

**Considered options**
- Largest-contour selection everywhere — rejected: a separated hand blob larger than the
  mouse teleports the crosshair to the hand.
- Two-level continuity (contour nearest previous tip + end nearest frozen tip) — chosen;
  a couple of lines, zero new concepts. Q2 applied continuity only at end-selection;
  contour *selection* is the same mechanism one level up.

**Documented non-bugs (deferred to phase-2 asymmetry upgrade, same as rotation)**
- Nose-side contact or a merged hand mass distorting the tip (case 1) — reads as jitter,
  acceptable in phase 1.
- A hand blob that fully swallows the mouse contour so it ceases to be a distinct contour
  — continuity can't select what it can't see; collapses into case 1.

**Consequences**
- Phase-1 DoD survives contact with a real desk: a waving hand near the pad no longer
  moves the crosshair.
