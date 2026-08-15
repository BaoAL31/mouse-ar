# Mouse AR

Tracks the nose of a mouse lying on a desk pad using a downward-pointing phone camera,
producing a real-time crosshair overlay. Phase 1 is a self-contained OpenCV-on-Android
app that glues a crosshair to the nose at ≥25 fps, measured via the debug harness
(stationary tip RMS ≤ 2 mm). Later phases (streaming, cursor, AR anchor) are explicitly
out of scope until the crosshair is glued.

## Language

**Mouse**:
The tracked object on the pad — the contour selected among those above min area by the
nearest-previous-tip rule (two-level continuity); the largest contour is only the
first-frame fallback. Not the physical rodent; the visible blob.
_Avoid_: blob (ambiguous), target

**Nose (tip)**:
The frontmost point of the mouse along its heading — where the crosshair is drawn.
_Avoid_: tip, head

**Background**:
The saved grayscale frame captured when the mouse is OFF the pad. The reference for
background subtraction.
_Avoid_: reference frame, baseline

**Difference image (diff)**:
The absolute difference between the current frame and the background, after luminance
normalization, thresholded to isolate the mouse. Its contours are the candidates the
two-level continuity rule selects from.
_Avoid_: absdiff result, foreground mask

**Two-level continuity**:
Continuity applied to both pipeline levels: among contours above min area, pick the one
nearest the previous tip (largest only as first-frame fallback); among that contour's
two long-axis ends, pick the one nearer the previous tip. Keeps a larger hand blob or a
fast rotation from stealing the crosshair.
_Avoid_: nearest-neighbor tracking, biggest contour

**Heading**:
The direction of the mouse's long axis, resolved each frame by continuity: among the two
`minAreaRect` long-axis endpoints, pick whichever is nearer the previous tip. Determines
which end is the nose.
_Avoid_: orientation, angle, carried sign

**Freeze-on-absence**:
While the blob is missing (mouse lifted), hold the last tip and skip drawing. On
reappearance, run the nearest-end rule against that frozen tip so lift/return is a
non-event rather than a coin flip.
_Avoid_: ghost tracking, last-known position

**Seed tap**:
Tapping the nose on screen to re-anchor which end is front. Stays live forever — it is
the escape hatch for the one case continuity can't heal (a ~180° rotated put-down, where
nearest-to-frozen-tip picks the tail).
_Avoid_: calibration, setup tap

**Luminance normalization (scale-to-mean)**:
Scaling the current frame to the background's mean luminance before the diff, making it
invariant to global auto-exposure re-balancing.
_Avoid_: white balance, calibration

**Re-capture**:
The first-class button that re-captures the background for real scene changes (light
switch, mug appears, lamp moved). Not an AE escape hatch.
_Avoid_: reset background, re-baseline

**Debug measurement harness**:
A debug-only, measurement-only screen (hidden from the tracking overlay) that computes a
one-off mm/px scale factor — user enters the mouse's known length (default 120 mm) and
taps nose + tail on a frozen frame — then reports stationary tip RMS in mm over a ~5 s
still window, plus p95/max excursion and fps. Not a runtime calibration; produces the
falsifiable DoD number.
_Avoid_: calibration screen, test fixture

**Stationary RMS jitter**:
The phase-1 DoD gate metric: root-mean-square of stationary tip displacement in mm over a
~5 s still window, at ≥ 25 fps. RMS is the energy (shimmer); p95/max excursion are the
worst-case teleport.
_Avoid_: jitter (ambiguous)
