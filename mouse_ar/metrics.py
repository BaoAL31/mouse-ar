"""Jitter metrics for the phase-1 definition of done (ADR 0004).

Gate metric is stationary RMS in mm over a ~5 s still window; p95 and max excursion are
logged for context alongside fps. Units are whatever the caller feeds in (mm after the
debug harness applies the mm/px scale factor).
"""

from __future__ import annotations

import numpy as np


def stationary_jitter(
    points: list[tuple[float, float]],
) -> tuple[float, float, float]:
    """RMS / p95 / max excursion of *points* about their mean (stationary tip).

    Returns (rms, p95, max_excursion), each in the caller's units.
    """
    if not points:
        return (0.0, 0.0, 0.0)
    pts = np.asarray(points, dtype=float)
    if pts.shape[0] == 1:
        return (0.0, 0.0, 0.0)
    mean = pts.mean(axis=0)
    dists = np.linalg.norm(pts - mean, axis=1)
    rms = float(np.sqrt(np.mean(dists**2)))
    p95 = float(np.percentile(dists, 95))
    max_exc = float(dists.max())
    return (rms, p95, max_exc)
