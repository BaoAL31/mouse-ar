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
- **Absence gate (from review):** to protect freeze-on-absence, if even the nearest
  qualifying contour sits farther than `absent_radius_mult` (default 2.5) × the mouse's
  last observed length from the frozen anchor, it is treated as absent (a hand left
  waving after the mouse is lifted), so the crosshair freezes instead of retargeting
  onto the hand. Continuity applied to absence detection — no shape machinery.
- **Known trade-off (decided):** the same gate would also freeze a *present* mouse that
  moves more than `absent_radius_mult` mouse-lengths in a single frame — an extreme
  flick (~2.5 m/s of hand motion at 25fps), unlikely in normal use. It is recoverable
  via the always-live seed tap, and normal motion stays well under the threshold. This
  is accepted to keep the far-hand freeze robust.
