"""
Tool for figuring out the overlay stuff!
"""

from __future__ import annotations

from typing import BinaryIO, List, Tuple

from PIL import Image

# Pixels with alpha below this count as transparent
ALPHA_THRESHOLD = 48

# Vertical sampling step (rows)
ROW_STEP = 4

# Rows qualify as interior if the widest transparent run is at least this wide
MIN_WIDE_RUN_RATIO = 0.18
MIN_WIDE_RUN_PX = 120

# Ignore auto-bounds when the overall vertical extent (top→bottom) is too small.
MIN_TANK_HEIGHT_ROWS = 64


def _widest_transparent_run_bounds(
    pixels, y: int, width: int
) -> tuple[int, int] | None:
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for x in range(width):
        pix = pixels[x, y]
        a = pix[3] if len(pix) >= 4 else 255
        if a < ALPHA_THRESHOLD:
            if start is None:
                start = x
        elif start is not None:
            runs.append((start, x))
            start = None
    if start is not None:
        runs.append((start, width))
    if not runs:
        return None
    return max(runs, key=lambda r: r[1] - r[0])


def _widest_transparent_run_center_x(pixels, y: int, width: int) -> float | None:
    b = _widest_transparent_run_bounds(pixels, y, width)
    if b is None:
        return None
    lo, hi = b
    return (lo + hi) / 2.0


def _widest_transparent_run_width(pixels, y: int, width: int) -> int:
    b = _widest_transparent_run_bounds(pixels, y, width)
    if b is None:
        return 0
    return b[1] - b[0]


def _open_foreground_rgba(file_obj: BinaryIO) -> Image.Image:
    file_obj.seek(0)
    img = Image.open(file_obj)
    if getattr(img, "n_frames", 1) > 1:
        img.seek(0)
    return img.convert("RGBA")


def _row_qualifies_for_tank_band(pixels, y: int, width: int) -> bool:
    need = max(MIN_WIDE_RUN_PX, int(width * MIN_WIDE_RUN_RATIO))
    return _widest_transparent_run_width(pixels, y, width) >= need


def detect_tank_vertical_offsets_from_pixels(
    pixels, width: int, height: int
) -> Tuple[int, int] | None:
    """
    Infer tank_top_offset and tank_bottom_offset

    Rows qualify when they have a wide transparent run (same threshold as label holes).
    Uses the overall vertical extent: topmost qualifying row through bottommost qualifying
    row, so multiple separate alpha zones still yield one tank span.
    """
    ymin: int | None = None
    ymax: int | None = None
    for y in range(height):
        if not _row_qualifies_for_tank_band(pixels, y, width):
            continue
        if ymin is None:
            ymin = ymax = y
        else:
            ymin = min(ymin, y)
            ymax = max(ymax, y)

    if ymin is None or ymax is None:
        return None

    extent = ymax - ymin + 1
    if extent < MIN_TANK_HEIGHT_ROWS:
        return None

    tank_top = ymin
    tank_bottom = height - (ymax + 1)
    if tank_top + tank_bottom >= height:
        return None
    return (tank_top, tank_bottom)


def _build_label_profile_from_pixels(
    pixels, width: int, height: int
) -> List[List[float]]:
    samples: List[List[float]] = []
    for y in range(0, height, ROW_STEP):
        cx = _widest_transparent_run_center_x(pixels, y, width)
        if cx is None:
            x_pct = 50.0
        else:
            x_pct = (cx / width) * 100.0
        y_pct = (y / height) * 100.0 if height else 0.0
        samples.append([round(y_pct, 4), round(x_pct, 4)])
    return samples


def analyze_stage_foreground(
    file_obj: BinaryIO,
) -> tuple[List[List[float]], Tuple[int, int] | None]:
    """
    Read the overlay at native size, then compute label profile and optional
    tank vertical margins from transparency.
    """
    img = _open_foreground_rgba(file_obj)
    width, height = img.size
    pixels = img.load()
    profile = _build_label_profile_from_pixels(pixels, width, height)
    margins = detect_tank_vertical_offsets_from_pixels(pixels, width, height)
    return profile, margins


def interpolate_stage_x_pct(samples: List[List[float]], y_pct: float) -> float:
    """Linear interpolation of stage X% (0=left, 100=right) at vertical position y_pct (from top)."""
    if not samples:
        return 50.0
    if y_pct <= samples[0][0]:
        return samples[0][1]
    if y_pct >= samples[-1][0]:
        return samples[-1][1]
    for i in range(len(samples) - 1):
        y0, x0 = samples[i]
        y1, x1 = samples[i + 1]
        if y0 <= y_pct <= y1:
            if y1 == y0:
                return x0
            t = (y_pct - y0) / (y1 - y0)
            return x0 + t * (x1 - x0)
    return 50.0


def band_anchor_stage_x_pct(
    samples: List[List[float]], y_top_lo: float, y_top_hi: float
) -> float:
    """Average interpolated X at band top, middle, and bottom for stability."""
    if y_top_hi < y_top_lo:
        y_top_lo, y_top_hi = y_top_hi, y_top_lo
    mid = (y_top_lo + y_top_hi) / 2.0
    xs = [
        interpolate_stage_x_pct(samples, y_top_lo),
        interpolate_stage_x_pct(samples, mid),
        interpolate_stage_x_pct(samples, y_top_hi),
    ]
    return sum(xs) / len(xs)
