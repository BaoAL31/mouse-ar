import cv2
import numpy as np

from mouse_ar.tracker import extract_contours


def _base_scene() -> tuple[np.ndarray, np.ndarray]:
    background = np.full((100, 150), 100, dtype=np.uint8)
    frame = background.copy()
    return background, frame


def test_only_contours_above_min_area_are_returned():
    background, frame = _base_scene()
    # Mouse: a filled ellipse, large area (~pi*20*8 ~= 502 px).
    cv2.ellipse(frame, (60, 60), (20, 8), 0, 0, 360, 160, -1)
    # Noise dot: tiny, must be filtered by min_area.
    frame[80:83, 120:123] = 160  # 3x3 = 9 px

    contours = extract_contours(frame, background, threshold=30, min_area=200)

    assert len(contours) == 1
    area = cv2.contourArea(contours[0])
    assert area > 400  # the mouse ellipse survived


def test_low_contrast_blob_is_thresholded_out():
    background, frame = _base_scene()
    # Below-threshold contrast: diff = 10 < threshold=30 -> must vanish.
    cv2.rectangle(frame, (10, 10), (40, 40), 110, -1)

    contours = extract_contours(frame, background, threshold=30, min_area=200)

    assert contours == []


def test_morphological_close_joins_fragments():
    background, frame = _base_scene()
    # Two dots separated by a 2px gap: close() should bridge them into one contour.
    cv2.rectangle(frame, (20, 50), (25, 55), 160, -1)  # left dot
    cv2.rectangle(frame, (28, 50), (33, 55), 160, -1)  # right dot, gap=2px

    contours = extract_contours(frame, background, threshold=30, min_area=10)

    # Without close these would be 2 small contours; with a large-enough kernel,
    # one merged contour.
    assert len(contours) == 1
