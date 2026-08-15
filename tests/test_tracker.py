import cv2
import numpy as np

from mouse_ar.tracker import MouseTracker


def _mouse_frame(mouse_center=(60, 60), axes=(20, 8), with_hand=False):
    background = np.full((120, 160), 100, dtype=np.uint8)
    frame = background.copy()
    cv2.ellipse(frame, mouse_center, axes, 0, 0, 360, 160, -1)
    if with_hand:
        cv2.circle(frame, (130, 90), 25, 160, -1)
    return background, frame


def test_seed_then_track_reaches_the_nose():
    background, frame = _mouse_frame()
    t = MouseTracker(threshold=30, min_area=100)
    t.set_background(background)
    t.seed((80, 60))  # tap the nose (right end)

    res = t.process(frame)

    assert res.present
    assert np.linalg.norm(np.array(res.tip) - np.array((80.0, 60.0))) < 1.5


def test_absence_freezes_tip_and_recovers_on_return():
    background, mouse = _mouse_frame()
    t = MouseTracker(threshold=30, min_area=100)
    t.set_background(background)
    t.seed((80, 60))
    t.process(mouse)  # track once, tip ~ (80,60)

    absent = t.process(background.copy())  # mouse lifted
    assert not absent.present

    returned = t.process(mouse)  # mouse put back
    assert returned.present
    # Recovered against the frozen tip, nose still front.
    assert np.linalg.norm(np.array(returned.tip) - np.array((80.0, 60.0))) < 1.5


def test_first_frame_without_seed_selects_largest_contour():
    background, frame = _mouse_frame(with_hand=True)
    t = MouseTracker(threshold=30, min_area=100)
    t.set_background(background)
    # No seed: largest contour (the hand) is selected.

    res = t.process(frame)

    assert res.present
    # Tip lands somewhere on the hand blob (center ~ (130,90), radius 25).
    assert np.linalg.norm(np.array(res.tip) - np.array((130.0, 90.0))) <= 30


def test_process_requires_a_background():
    _, frame = _mouse_frame()
    t = MouseTracker(threshold=30, min_area=100)

    try:
        t.process(frame)
    except ValueError:
        return  # expected
    raise AssertionError("expected ValueError when no background is set")


def test_hand_during_lift_reports_absent_not_follow_the_hand():
    # Small-ish mouse (minAreaRect ~20px) so the absence gate threshold (2.5x=50) is
    # small relative to the frame, letting a far hand trigger the gate.
    background = np.full((120, 160), 100, dtype=np.uint8)
    mouse = background.copy()
    cv2.ellipse(mouse, (40, 60), (10, 5), 0, 0, 360, 160, -1)  # area ~157
    hand_only = background.copy()
    cv2.circle(hand_only, (130, 90), 25, 160, -1)  # a far hand, no mouse

    t = MouseTracker(threshold=30, min_area=100, absent_radius_mult=2.5)
    t.set_background(background)
    t.seed((50, 60))
    t.process(mouse)  # track the mouse; anchor -> ~(50,60), last_size ~20

    res = t.process(hand_only)  # mouse lifted, hand waving far away

    assert not res.present  # freeze instead of retargeting onto the hand
    # Recovery when the mouse returns.
    returned = t.process(mouse)
    assert returned.present
    assert np.linalg.norm(np.array(returned.tip) - np.array((50.0, 60.0))) < 3.0

