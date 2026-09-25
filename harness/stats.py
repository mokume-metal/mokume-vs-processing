# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""フレーム間隔の列を要約する。**両側に同じ式を掛けるため、統計はスケッチの中で取らない。**"""

from __future__ import annotations

import math
import statistics
from typing import Dict, Mapping, Sequence


def percentile(values: Sequence[float], q: float) -> float:
    """最近順位法 (nearest-rank) の分位。補間しないので、報告する値は実際に観測した間隔のどれかになる。"""
    if not values:
        raise ValueError("間隔が 1 つも無い")
    if not 0 < q <= 100:
        raise ValueError(f"分位は (0, 100] で指定する: {q}")
    ordered = sorted(values)
    rank = math.ceil(q / 100 * len(ordered))
    return ordered[rank - 1]


def summarize(intervals_ms: Sequence[float]) -> Dict[str, float]:
    """fps は間隔の平均の逆数。フレームごとの fps を平均すると、遅いフレームが軽く数えられる。"""
    if not intervals_ms:
        raise ValueError("間隔が 1 つも無い — 計測区間が短すぎるか、スケッチが描けていない")
    mean = sum(intervals_ms) / len(intervals_ms)
    return {
        "frames": len(intervals_ms),
        "fps": 1000 / mean,
        "mean_ms": mean,
        "p50_ms": percentile(intervals_ms, 50),
        "p95_ms": percentile(intervals_ms, 95),
        "p99_ms": percentile(intervals_ms, 99),
    }


def aggregate(runs: Sequence[Mapping[str, float]]) -> Dict[str, float]:
    """同じ段を繰り返した回 (`summarize` の結果) をまとめる。

    中心は中央値 (1 回だけ外れた回に引きずられない)、ばらつきは回ごとの fps の最小と最大で示す。
    """
    if not runs:
        raise ValueError("回が 1 つも無い")
    fps = [r["fps"] for r in runs]
    return {
        "repeats": len(runs),
        "fps": statistics.median(fps),
        "fps_min": min(fps),
        "fps_max": max(fps),
        "p50_ms": statistics.median(r["p50_ms"] for r in runs),
        "p95_ms": statistics.median(r["p95_ms"] for r in runs),
        "p99_ms": statistics.median(r["p99_ms"] for r in runs),
    }
