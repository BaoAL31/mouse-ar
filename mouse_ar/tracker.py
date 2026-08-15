"""Phase-1 mouse-nose tracking algorithm.

Pure numpy/OpenCV logic, portable to the Android/Kotlin app. Implements the decisions
in docs/adr/0001-0003: illumination normalization, background-diff segmentation, and
two-level continuity for contour + end selection.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

import cv2

_EPS = 1e-6


def normalize_luminance(frame: np.ndarray, background: np.ndarray) -> np.ndarray:
    """Scale *frame* to the background's luminance (scale-to-median).

    Auto-exposure re-balancing is roughly a global gain step, so this makes the diff
    invariant to it (ADR 0001). We use the **median**, not the mean, for the frame's
    luminance estimate: the mean includes the mouse blob, which can suppress its own
    contrast (a large bright mouse pushes the mean up, shrinking the scale and
    thresholding itself out). Median stays on the pad background as long as the mouse
    covers < ~50% of the frame. Returns a uint8 frame.
    """
    bg_lum = float(np.median(background))
    frame_lum = float(np.median(frame))
    if bg_lum <= 0 or frame_lum <= 0:
        return frame
    scale = bg_lum / (frame_lum + _EPS)
    scaled = frame.astype(np.float32) * scale
    return np.clip(scaled, 0.0, 255.0).astype(np.uint8)


def extract_contours(
    frame: np.ndarray,
    background: np.ndarray,
    threshold: int = 30,
    min_area: float = 200.0,
    close_kernel: int = 5,
) -> list[np.ndarray]:
    """Segment the mouse from a normalized frame vs background.

    absdiff -> threshold -> morphological close -> external contours filtered by
    min_area. Returns the qualifying contours (each an Nx1x2 int32 array). The caller
    applies two-level continuity to select among them.
    """
    diff = cv2.absdiff(frame, background)
    _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    if close_kernel > 1:
        kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (close_kernel, close_kernel)
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [c for c in contours if cv2.contourArea(c) >= min_area]


def contour_centroid(contour: np.ndarray) -> tuple[float, float]:
    m = cv2.moments(contour)
    if m["m00"] == 0:
        return (0.0, 0.0)
    return (m["m10"] / m["m00"], m["m01"] / m["m00"])


def _dist(a, b) -> float:
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


def select_mouse_contour(
    contours: list[np.ndarray], prev_tip: tuple[float, float] | None
) -> np.ndarray | None:
    """Two-level continuity, level 1 (contour selection, ADR 0003).

    Among qualifying contours pick the one whose centroid is nearest the previous tip;
    largest contour is only the first-frame fallback when there is no previous tip.
    """
    if not contours:
        return None
    if prev_tip is None:
        return max(contours, key=cv2.contourArea)
    return min(
        contours, key=lambda c: _dist(contour_centroid(c), prev_tip)
    )


def rect_long_axis_ends(contour: np.ndarray) -> tuple[tuple[float, float], ...]:
    """The two long-axis endpoints of the contour's minAreaRect (ADR 0002).

    These are the midpoints of the two *short* sides of the box — the stable anchors we
    select between; not the output tip itself.
    """
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)  # 4 corners, ordered around the box
    corners = np.asarray(box, dtype=float)
    # Side length between consecutive corners; the two shortest sides are the short ones.
    edges = [
        (i, float(np.linalg.norm(corners[(i + 1) % 4] - corners[i]))) for i in range(4)
    ]
    short_edges = sorted(edges, key=lambda e: e[1])[:2]
    ends = []
    for i, _ in short_edges:
        mid = (corners[i] + corners[(i + 1) % 4]) / 2.0
        ends.append((float(mid[0]), float(mid[1])))
    return (ends[0], ends[1])


def resolve_tip(
    contour: np.ndarray, anchor: tuple[float, float] | None
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Level-2 continuity: pick the forward end and derive the tip (ADR 0002).

    Among the two long-axis ends, forward is the one nearer *anchor* (the previous /
    frozen tip). heading points from the rear end to the forward end; the tip is the
    extreme contour point along heading. Returns (tip, heading_unit).
    """
    ends = rect_long_axis_ends(contour)
    e0, e1 = ends
    if anchor is None:
        forward, rear = e0, e1
    else:
        forward, rear = (
            (e0, e1) if _dist(e0, anchor) <= _dist(e1, anchor) else (e1, e0)
        )
    axis = np.array(forward) - np.array(rear)
    norm = np.linalg.norm(axis)
    if norm == 0:
        return (forward, (1.0, 0.0))
    heading = axis / norm

    pts = contour.reshape(-1, 2).astype(float)
    projections = pts @ heading
    tip = pts[int(np.argmax(projections))]
    return (float(tip[0]), float(tip[1])), (float(heading[0]), float(heading[1]))


@dataclass
class Track:
    """Per-frame tracking result."""

    present: bool
    tip: tuple[float, float] | None = None
    heading: tuple[float, float] | None = None


class MouseTracker:
    """Stateful per-frame tracker (ADR 0001-0003).

    Call set_background once, seed() to anchor the nose, then process() each frame.
    """

    def __init__(
        self,
        threshold: int = 30,
        min_area: float = 200.0,
        close_kernel: int = 5,
        absent_radius_mult: float = 2.5,
    ) -> None:
        self.threshold = threshold
        self.min_area = min_area
        self.close_kernel = close_kernel
        self.absent_radius_mult = absent_radius_mult
        self._background: np.ndarray | None = None
        self._anchor: tuple[float, float] | None = None
        self._last_size: float | None = None

    def set_background(self, background: np.ndarray) -> None:
        """Store the background frame (mouse OFF the pad)."""
        self._background = background

    def seed(self, point: tuple[float, float]) -> None:
        """Anchor the nose end from a live seed tap (ADR 0002)."""
        self._anchor = point

    def process(self, frame: np.ndarray) -> Track:
        """Track one normalized gray frame. present=False on lift (freeze-on-absence)."""
        if self._background is None:
            raise ValueError("set_background() must be called before process()")
        normalized = normalize_luminance(frame, self._background)
        contours = extract_contours(
            normalized,
            self._background,
            threshold=self.threshold,
            min_area=self.min_area,
            close_kernel=self.close_kernel,
        )
        contour = select_mouse_contour(contours, self._anchor)
        if contour is None:
            # Nothing above threshold: mouse lifted, freeze the anchor, skip drawing.
            return Track(present=False)
        # Absence gate: even the nearest contour is far from where the mouse was, so it
        # is not the mouse (e.g. a hand waving after the mouse is lifted). Continuity
        # applied to absence detection — freeze rather than retarget onto the hand.
        if (
            self._anchor is not None
            and self._last_size is not None
            and _dist(contour_centroid(contour), self._anchor)
            > self.absent_radius_mult * self._last_size
        ):
            return Track(present=False)
        tip, heading = resolve_tip(contour, self._anchor)
        rect = cv2.minAreaRect(contour)
        self._last_size = max(rect[1])
        self._anchor = tip
        return Track(present=True, tip=tip, heading=heading)
