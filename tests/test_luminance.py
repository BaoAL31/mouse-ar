import numpy as np

from mouse_ar.tracker import normalize_luminance


def test_normalized_frame_mean_matches_background_mean():
    # Background: uniform mid-grey pad.
    background = np.full((100, 120), 100, dtype=np.uint8)
    # Same scene but re-balanced by AE: roughly a global scale up in brightness.
    frame = np.full((100, 120), 200, dtype=np.uint8)

    normalized = normalize_luminance(frame, background)

    assert normalized.dtype == np.uint8
    assert abs(float(normalized.mean()) - float(background.mean())) < 2.0


def test_constant_scene_produces_zero_diff_after_normalization():
    # A uniform pad with no mouse. After normalization the diff vs background is ~0,
    # i.e. AE re-balancing alone must not create a phantom blob.
    background = np.full((80, 80), 90, dtype=np.uint8)
    frame = np.full((80, 80), 180, dtype=np.uint8)

    normalized = normalize_luminance(frame, background)
    diff = np.abs(normalized.astype(np.int16) - background.astype(np.int16))

    assert diff.max() <= 1


def test_mouse_still_differs_after_normalization():
    # A real object (mouse) sits on the pad; it must survive normalization.
    background = np.full((100, 100), 100, dtype=np.uint8)
    frame = np.full((100, 100), 100, dtype=np.uint8)
    frame[40:60, 40:60] = 160  # the mouse

    normalized = normalize_luminance(frame, background)
    diff = np.abs(normalized.astype(np.int16) - background.astype(np.int16))

    # The mouse region must still differ enough to threshold.
    assert diff[40:60, 40:60].max() > 30


def test_large_bright_mouse_is_not_suppressed_by_its_own_mean():
    # Regression (review): with mean-based scaling a big bright mouse pushes the frame
    # mean up, shrinking the scale and thresholding itself out. Median scaling keeps the
    # pad background as the luminance reference so a large mouse still survives.
    background = np.full((100, 100), 40, dtype=np.uint8)
    frame = np.full((100, 100), 40, dtype=np.uint8)
    frame[30:70, 30:70] = 200  # mouse covers ~16% of the area, much brighter

    normalized = normalize_luminance(frame, background)
    diff = np.abs(normalized.astype(np.int16) - background.astype(np.int16))

    # The pad check is the regression guard: a mean-based scale would leave a phantom
    # diff on the pad (mean maps pad 40 -> ~24, i.e. diff ~16 > 1) that this rejects.
    assert diff[5:10, 5:10].max() <= 1
    # And the mouse still clears the threshold (sanity check on the region that should
    # survive).
    assert diff[30:70, 30:70].max() > 30

