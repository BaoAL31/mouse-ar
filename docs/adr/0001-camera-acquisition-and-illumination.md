# ADR 0001: JavaCameraView with luminance normalization instead of Camera2 AE lock

We acquire frames via OpenCV's `JavaCameraView` rather than `JavaCamera2View`. The
auto-exposure threat to background-diff is dissolved in the algorithm, not the camera
path: before `absdiff`, we scale the current frame to the background's luminance (one
scalar multiply, using the median — see the refinement note below), making the diff
invariant to global exposure re-balancing. We do
**not** attempt to lock AE, because the shipped `JavaCamera2View` does not expose its
`CameraDevice`, so AE lock would require forking OpenCV's view or dropping to raw
Camera2 — an expensive path for phase 1. A fixed threshold then behaves consistently
across lighting instead of needing constant retuning.

**Considered options**
- `JavaCamera2View` + AE lock via `CONTROL_AE_LOCK` — rejected: the wrapper doesn't
  expose AE lock; would require forking OpenCV or owning the camera.
- `JavaCameraView` + luminance normalization + first-class re-capture — chosen.

**Consequences**
- Background re-capture is a first-class feature for *scene* changes (light switch, mug
  appears), which no AE lock fixes anyway.
- Escalation path (phase 2, decided with data): if real-desk testing shows normalization
  is insufficient (brutal local shadows, per-frame tone mapping), own the camera with raw
  Camera2 + manual exposure/focus.

**Implementation refinement (from review):** we compute the scale with the frame's
**median** luminance, not the literal mean. The mean includes the mouse blob, so a large
bright mouse pushes it up, shrinks the scale, and can threshold itself out; the median
stays on the pad background while the mouse covers < ~50% of the frame. This preserves
the ADR's intent (neutralize global gain) without the mouse contaminating its own scale.
