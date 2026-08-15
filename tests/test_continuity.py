import cv2
import numpy as np

from mouse_ar.tracker import (
    extract_contours,
    rect_long_axis_ends,
    resolve_tip,
    select_mouse_contour,
)


def _mouse_and_hand_scene():
    """Mouse ellipse (center 60,60, axes 20x8) + a much larger 'hand' circle."""
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, (60, 60), (20, 8), 0, 0, 360, 160, -1)  # mouse (~502 px)
    cv2.circle(frame, (130, 90), 25, 160, -1)  # hand (~1963 px)
    return extract_contours(frame, background, threshold=30, min_area=100)


def test_contour_selection_prefers_nearest_to_previous_tip():
    contours = _mouse_and_hand_scene()
    # prev_tip is the mouse's nose (80,60): continuity must win over size.
    sel = select_mouse_contour(contours, prev_tip=(80, 60))

    m = cv2.moments(sel)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    # Near the mouse center (60,60), not the hand (130,90).
    assert abs(cx - 60) < 15 and abs(cy - 60) < 15
    assert cv2.contourArea(sel) < 1000  # it's the mouse, not the larger hand


def test_contour_selection_falls_back_to_largest_without_previous_tip():
    contours = _mouse_and_hand_scene()
    sel = select_mouse_contour(contours, prev_tip=None)

    m = cv2.moments(sel)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    assert abs(cx - 130) < 15 and abs(cy - 90) < 15  # largest = the hand


def test_long_axis_ends_of_a_horizontal_mouse():
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, (60, 60), (20, 8), 0, 0, 360, 160, -1)
    contour = extract_contours(frame, background, threshold=30, min_area=100)[0]

    e1, e2 = rect_long_axis_ends(contour)

    # Ends are the two long-axis endpoints: left (40,60) and right (80,60).
    ends = np.array([e1, e2])
    assert len({tuple(np.round(e).astype(int)) for e in ends}) == 2
    xs = ends[:, 0].astype(int)
    assert set(xs) <= {39, 40, 41, 79, 80, 81}
    assert set(np.round(ends[:, 1]).astype(int)) <= {59, 60, 61}


def test_tip_resolves_to_nose_end_following_anchor():
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, (60, 60), (20, 8), 0, 0, 360, 160, -1)
    contour = extract_contours(frame, background, threshold=30, min_area=100)[0]

    tip, heading = resolve_tip(contour, anchor=(80, 60))  # nose on the right

    assert np.linalg.norm(np.array(tip) - np.array((80.0, 60.0))) < 1.5
    assert np.allclose(heading, (1.0, 0.0), atol=1e-3)


def test_sign_follows_anchor_to_the_other_end():
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, (60, 60), (20, 8), 0, 0, 360, 160, -1)
    contour = extract_contours(frame, background, threshold=30, min_area=100)[0]

    tip, heading = resolve_tip(contour, anchor=(40, 60))  # anchor moved to left end

    assert np.linalg.norm(np.array(tip) - np.array((40.0, 60.0))) < 1.5
    assert np.allclose(heading, (-1.0, 0.0), atol=1e-3)


def _rotated_mouse_contour():
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, (80, 80), (20, 8), 30, 0, 360, 160, -1)
    return extract_contours(frame, background, threshold=30, min_area=100)[0]


def test_long_axis_ends_are_rotation_invariant():
    contour = _rotated_mouse_contour()
    e1, e2 = rect_long_axis_ends(contour)
    a, b = np.array(e1, dtype=float), np.array(e2, dtype=float)

    # Ends straddle the center, ~40 apart (2x major radius) regardless of rotation.
    midpoint = (a + b) / 2.0
    assert np.linalg.norm(midpoint - np.array((80.0, 80.0))) < 2.0
    assert abs(np.linalg.norm(a - b) - 40.0) < 3.0


def test_tip_follows_anchor_on_a_rotated_mouse():
    contour = _rotated_mouse_contour()
    e1, _ = rect_long_axis_ends(contour)

    tip, heading = resolve_tip(contour, anchor=e1)

    assert np.linalg.norm(np.array(tip) - np.array(e1, dtype=float)) < 2.0
    assert abs(np.linalg.norm(heading) - 1.0) < 1e-6


def test_resolve_tip_without_anchor_does_not_crash():
    contour = _rotated_mouse_contour()

    tip, heading = resolve_tip(contour, anchor=None)

    x, y, w, h = cv2.boundingRect(contour)
    tx, ty = tip
    assert x - 1 <= tx <= x + w + 1 and y - 1 <= ty <= y + h + 1
    assert abs(np.linalg.norm(heading) - 1.0) < 1e-6

