<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# particles — 大量の粒子

N 個の点を画面の中で等速で動かし、壁で跳ね返らせ、直径 4 px の半透明の円として描く。
creative coding で最もよく書かれる形の 1 つで、**1 フレームに描く図形の数**がそのまま負荷になる。

| | |
| --- | --- |
| mokume | [`mokume/Particles/Sources/Particles/Particles.swift`](mokume/Particles/Sources/Particles/Particles.swift) |
| Processing | [`processing/Particles/Particles.pde`](processing/Particles/Particles.pde) (P2D) |
| 負荷 | `MVP_COUNT` = 粒子の数 |

**両側は同じ書き方をしている** — 配列に位置と速度を持ち、`draw()` の中で 1 個ずつ動かして
`circle()` を呼ぶ。mokume にはもっと速い書き方 (`createShape` + `shape(_:at:)` で 1 回に置く・
GPU の粒子系) があるが、ここでは使わない。「Processing と同じコードを書いたときにどうなるか」を
先に押さえ、mokume らしい書き方は別の事例として足す。

### 揃えられない差

- **窓の大きさ。** Processing は `size(1280, 720)` で窓を 1280 × 720 点で開くが、mokume は
  描く解像度の半分の点で開き、大きさを選ぶ口が無い
  ([mokume#1624](https://github.com/mokume-metal/mokume/issues/1624))。mokume 側の
  `Recorder.swift` が最初のフレーム (暖機の中) で窓を 1280 × 720 点に広げて揃えている。
  両側とも 1280 × 720 px で描き、Retina では 2 倍に拡大して出す

## 回す

```bash
python3 harness/run.py particles
```

## 結果

まだ測っていない。
