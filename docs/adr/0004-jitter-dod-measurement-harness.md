# ADR 0004: Falsifiable jitter DoD via a debug-only measurement harness

Phase 1's definition of done makes a physical claim ("jitter ≤ ~2 mm") but the pipeline
emits pixels, and phase 1 has no runtime calibration. We resolve this with a **debug-only,
measurement-only harness** — not a runtime tracking calibration, so the "no calibration
loops" clause is not violated. It produces the actual number the sticker-free-vs-tag
decision depends on, instead of vibes.

**How it works**
- One-off scale factor: the harness prompts for the mouse's known length once (default
  120 mm, since mice run 90–130 mm), then you tap nose + tail on a **frozen** frame to
  compute mm/px. Tapping a live frame would inject finger jitter into the scale factor,
  poisoning every mm reading after it.
- The gate metric is **stationary RMS in mm over a ~5 s still window**, with p95 and max
  excursion logged for context, plus fps. RMS = energy (does the crosshair shimmer?), max
  = worst-case teleport.
- Output is both an on-screen readout and a logcat/CSV dump, so the numbers land in docs
  and the phase-2 call is made with data, not memory.

**DoD sentence**
Stationary tip RMS ≤ 2 mm at ≥ 25 fps, measured via the debug harness.

**Rejected**
- A (pure qualitative "eyeball it") — produces vibes, not the decision-driving number.
- C (in-frame ruler metrology) — building a product feature to test a prototype.
