from io import BytesIO

from django.test import TestCase
from PIL import Image

from apps.tanks_manager.foreground_labels import (
    STAGE_H,
    STAGE_W,
    analyze_stage_foreground,
    compute_foreground_label_profile,
    interpolate_stage_x_pct,
)


class ForegroundLabelProfileTests(TestCase):
    def test_interpolate_brackets(self):
        samples = [[0.0, 10.0], [50.0, 60.0], [100.0, 90.0]]
        self.assertAlmostEqual(interpolate_stage_x_pct(samples, 0), 10.0)
        self.assertAlmostEqual(interpolate_stage_x_pct(samples, 100), 90.0)
        self.assertAlmostEqual(interpolate_stage_x_pct(samples, 25), 35.0)

    def test_compute_finds_vertical_transparent_gap(self):
        img = Image.new("RGBA", (400, 400), (255, 0, 0, 255))
        for y in range(400):
            for x in range(160, 240):
                img.putpixel((x, y), (0, 0, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        profile = compute_foreground_label_profile(buf)
        self.assertGreater(len(profile), 8)
        mid_x = interpolate_stage_x_pct(profile, 50.0)
        self.assertGreater(mid_x, 35.0)
        self.assertLess(mid_x, 65.0)

    def test_analyze_detects_tank_vertical_band(self):
        img = Image.new("RGBA", (STAGE_W, STAGE_H), (10, 10, 10, 255))
        for y in range(200, 650):
            for x in range(STAGE_W):
                img.putpixel((x, y), (0, 0, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        profile, margins = analyze_stage_foreground(buf)
        self.assertIsNotNone(margins)
        top, bot = margins
        self.assertEqual(top, 200)
        self.assertEqual(bot, STAGE_H - 650)
        self.assertGreater(len(profile), 8)

    def test_analyze_extent_covers_two_separate_alpha_zones(self):
        img = Image.new("RGBA", (STAGE_W, STAGE_H), (10, 10, 10, 255))
        for y in range(100, 151):
            for x in range(STAGE_W):
                img.putpixel((x, y), (0, 0, 0, 0))
        for y in range(500, 601):
            for x in range(STAGE_W):
                img.putpixel((x, y), (0, 0, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        _profile, margins = analyze_stage_foreground(buf)
        self.assertIsNotNone(margins)
        top, bot = margins
        self.assertEqual(top, 100)
        self.assertEqual(bot, STAGE_H - 601)
