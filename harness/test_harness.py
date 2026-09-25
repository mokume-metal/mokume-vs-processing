# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""ハーネスの GPU を要さない部分の検査。`make ci-check` から回る。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cases
import stats


class PercentileTests(unittest.TestCase):
    def test_nearest_rank_picks_an_observed_value(self):
        values = [10.0, 20.0, 30.0, 40.0]
        self.assertEqual(stats.percentile(values, 50), 20.0)
        self.assertEqual(stats.percentile(values, 95), 40.0)
        self.assertEqual(stats.percentile(values, 100), 40.0)

    def test_single_value(self):
        self.assertEqual(stats.percentile([16.7], 99), 16.7)

    def test_rejects_empty_and_out_of_range(self):
        with self.assertRaises(ValueError):
            stats.percentile([], 50)
        with self.assertRaises(ValueError):
            stats.percentile([1.0], 0)


class SummarizeTests(unittest.TestCase):
    def test_fps_is_inverse_of_mean_interval(self):
        # 10 ms と 30 ms が交互なら平均 20 ms で 50 fps。フレームごとの fps (100 と 33.3) を
        # 平均した 66.7 にはならない
        summary = stats.summarize([10.0, 30.0] * 5)
        self.assertAlmostEqual(summary["fps"], 50.0)
        self.assertEqual(summary["frames"], 10)

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            stats.summarize([])


class CaseLayoutTests(unittest.TestCase):
    def make_case(self, root: Path, name: str, sketch: str = "Sketch", pde: str = "Sketch.pde"):
        case_dir = root / "cases" / name
        (case_dir / "mokume" / sketch).mkdir(parents=True)
        (case_dir / "mokume" / sketch / "Package.swift").write_text("")
        (case_dir / "processing" / sketch).mkdir(parents=True)
        (case_dir / "processing" / sketch / pde).write_text("")
        (case_dir / "README.md").write_text("")
        return case_dir

    def test_complete_case_has_no_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.make_case(Path(tmp), "ok")
            self.assertEqual(cases.all_problems(Path(tmp)), [])

    def test_main_pde_must_match_folder_name(self):
        # Processing はフォルダ名と同じ名前の .pde を主として開く。ずれると cli が起動できない
        with tempfile.TemporaryDirectory() as tmp:
            self.make_case(Path(tmp), "bad", sketch="Sketch", pde="Other.pde")
            self.assertEqual(len(cases.all_problems(Path(tmp))), 1)

    def test_missing_mokume_side(self):
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = self.make_case(Path(tmp), "half")
            (case_dir / "mokume" / "Sketch" / "Package.swift").unlink()
            self.assertEqual(len(cases.all_problems(Path(tmp))), 1)

    def test_mokume_package_directly_under_side_is_rejected(self):
        # 直下に置くと SwiftPM の識別名が依存の mokume と衝突する (cases.py の冒頭)
        with tempfile.TemporaryDirectory() as tmp:
            case_dir = self.make_case(Path(tmp), "flat")
            (case_dir / "mokume" / "Sketch" / "Package.swift").rename(case_dir / "mokume" / "Package.swift")
            (case_dir / "mokume" / "Sketch").rmdir()
            self.assertEqual(len(cases.all_problems(Path(tmp))), 1)

    def test_repository_cases_are_complete(self):
        self.assertEqual(cases.all_problems(), [])


if __name__ == "__main__":
    unittest.main()
