# ADR 0002: Heading sign via continuity (nearest-to-frozen-tip), not a carried boolean

The nose/heading sign is resolved each frame by continuity, not a fixed carried sign.
The two candidates are the **long-axis endpoints of the `minAreaRect`** (midpoints of
the short sides); we pick whichever is nearer the previous tip, then the tip is the
extreme contour point along the chosen direction. We deliberately do **not** run
nearest-neighbor over raw contour points — the rect ends are the stable anchors, the
contour extreme is the output; conflating the two makes the tip walk along the
silhouette under jitter.

**Considered options**
- Mechanism A: carried `+1/-1` boolean from the seed — rejected: any mid-session rotation
  permanently swaps nose/tail until re-seed.
- Mechanism B + freeze-on-absence + permanent re-seed — chosen.

**Amendments that make B airtight**
- While the blob is absent (lift), hold the last tip; on reappearance run the nearest-end
  rule against that frozen tip. Makes lift/return a non-event, not a coin flip.
- The nose-tap re-seed stays live forever (not just setup), as the escape hatch for the
  one case B can't heal: a ~180° rotated put-down, where nearest-to-frozen-tip picks the
  tail. The button never leaves the UI.

**Consequences**
- Rotation is *tolerated if slow* (free side effect of B), *not guaranteed if fast or
  re-placed rotated*, and explicitly out of phase-1 DoD — treated as "tolerated but
  untested" so the side effect is not mistaken for a contract.
- Phase-2 upgrade when driving a cursor: fuse continuity with shape asymmetry (nose end
  narrower, hand mass on the tail side).
