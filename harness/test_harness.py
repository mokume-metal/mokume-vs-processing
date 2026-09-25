# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""ハーネスの GPU を要さない部分の検査。`make ci-check` から回る。"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import cases
import run
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


class AggregateTests(unittest.TestCase):
    @staticmethod
    def run_with(fps, p95=17.0):
        return {"fps": fps, "p50_ms": 16.7, "p95_ms": p95, "p99_ms": 20.0}

    def test_center_is_median_and_spread_is_min_max(self):
        # 1 回だけ大きく外れた回 (30 fps) があっても、中心は中央値なので引きずられない
        a = stats.aggregate([self.run_with(60.0, 16.8), self.run_with(30.0, 40.0), self.run_with(59.0, 17.2)])
        self.assertEqual(a["repeats"], 3)
        self.assertEqual(a["fps"], 59.0)
        self.assertEqual((a["fps_min"], a["fps_max"]), (30.0, 60.0))
        self.assertEqual(a["p95_ms"], 17.2)

    def test_rejects_empty(self):
        with self.assertRaises(ValueError):
            stats.aggregate([])


class OrderTests(unittest.TestCase):
    def test_first_side_alternates_between_repeats(self):
        sides = list(run.IMPLEMENTATIONS)
        firsts = [run.order(sides, r)[0] for r in range(4)]
        self.assertEqual(firsts, [sides[0], sides[1], sides[0], sides[1]])

    def test_aggregates_group_repeats_of_the_same_step(self):
        runs = [{"implementation": i, "count": c, "repeat": r, "fps": f, "p50_ms": 1.0, "p95_ms": 1.0,
                 "p99_ms": 1.0}
                for r, f in ((1, 50.0), (2, 60.0)) for c in (1000, 2000) for i in ("mokume", "processing")]
        grouped = run.aggregates(runs)
        self.assertEqual(len(grouped), 4)
        self.assertTrue(all(a["repeats"] == 2 and a["fps"] == 55.0 for a in grouped))


def fake_summary(implementations, counts, repeat=1):
    runs = [{"implementation": i, "count": c, "repeat": r + 1, "frames": 300,
             "fps": (60.0 if i == "mokume" else 30.0) - r,
             "mean_ms": 16.7, "p50_ms": 16.7, "p95_ms": 17.0, "p99_ms": 120.5}
            for r in range(repeat) for c in counts for i in implementations]
    return {"case": "demo", "machine": {"model": "Mac17,2", "chip": "Apple M5", "macos": "26.6"},
            "versions": {"mokume": "0.11.2", "processing": "4.5.2"}, "warmup_s": 2, "measure_s": 5,
            "repeat": repeat, "runs": runs, "aggregates": run.aggregates(runs)}


class TableTests(unittest.TestCase):
    def test_terminal_table_columns_line_up(self):
        counts = [1000, 100000]
        for repeat in (1, 3):
            with self.subTest(repeat=repeat):
                text = run.terminal_table(fake_summary(run.IMPLEMENTATIONS, counts, repeat), counts,
                                          list(run.IMPLEMENTATIONS))
                rows = [line for line in text.splitlines() if "|" in line and "-+-" not in line]
                # 見出し・小見出し・各段で、区切りの位置が揃っている
                positions = {tuple(i for i, ch in enumerate(line) if ch == "|") for line in rows}
                self.assertEqual(len(positions), 1)
                self.assertEqual(len(rows), 2 + len(counts))

    def test_repeated_tables_show_the_spread(self):
        # 3 回の fps が 60, 59, 58 なら、中央値 59.0 と最小〜最大 58.0–60.0 を出す
        counts = [1000]
        summary = fake_summary(run.IMPLEMENTATIONS, counts, repeat=3)
        sides = list(run.IMPLEMENTATIONS)
        self.assertIn("58.0–60.0", run.terminal_table(summary, counts, sides))
        table = run.markdown_table(summary, counts, sides)
        self.assertIn("| 59.0 [58.0–60.0] (17.0) |", table)
        self.assertIn("mokume fps [最小–最大] (p95 ms)", table)

    def test_single_repeat_has_no_spread(self):
        counts = [1000]
        summary = fake_summary(run.IMPLEMENTATIONS, counts, repeat=1)
        sides = list(run.IMPLEMENTATIONS)
        self.assertNotIn("min–max", run.terminal_table(summary, counts, sides))
        self.assertIn("| 60.0 (17.0) |", run.markdown_table(summary, counts, sides))

    def test_ratio_is_mokume_over_processing(self):
        counts = [1000]
        text = run.terminal_table(fake_summary(run.IMPLEMENTATIONS, counts), counts, list(run.IMPLEMENTATIONS))
        self.assertIn("2.00x", text)

    def test_single_side_has_no_ratio(self):
        counts = [1000]
        text = run.terminal_table(fake_summary(["processing"], counts), counts, ["processing"])
        self.assertNotIn("ratio", text)

    def test_both_tables_carry_the_conditions_line(self):
        counts = [1000]
        summary = fake_summary(run.IMPLEMENTATIONS, counts)
        for table in (run.terminal_table, run.markdown_table):
            last = table(summary, counts, list(run.IMPLEMENTATIONS)).splitlines()[-1]
            self.assertEqual(last, run.conditions(summary))
            self.assertIn("mokume 0.11.2", last)
            self.assertIn("repeat 1", last)


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
