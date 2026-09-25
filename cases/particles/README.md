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

## この題材を選んだ理由

- **creative coding で最もよく書かれる形の 1 つ**である。Processing の Examples にも、跳ね返る円は
  何度も出てくる (下の「書き方の出典」)
- **負荷が 1 つの数で素直に上がる。** 粒子の数を増やすと、1 フレームに描く図形の数と更新する配列の長さが
  そのまま増える。「60 fps を保てる最大の負荷」(ADR-0001 決定 1) を読み取りやすい

**この題材は mokume に有利に出うる。** 小さな円を大量に描くと、1 個あたりの描き方の違い
(下の「揃えられない差」の円の形) がそのまま効くからである。これは書き方の差ではなく実装の差なので、
この事例では揃えない。ただし、この 1 件だけで「mokume のほうが速い」とは言えない。
ほかの題材は別の事例として足す。

## 書き方の出典

Processing 側は、公式の Examples にある跳ね返りの書き方に沿っている。

- 壁で速度を反転する形は [Bounce](https://processing.org/examples/bounce.html) に沿う
  (`if (xpos > width-rad || xpos < rad) xdirection *= -1`)
- 塗りだけの半透明の白を黒に重ねる描き方は、[BouncyBubbles](https://processing.org/examples/bouncybubbles.html) に沿う
  (`noStroke()`・`fill(255, 204)`)
- **Examples と違うところ:** BouncyBubbles は粒子を `Ball` クラスの配列に持つが、ここでは位置と速度を
  `float[]` の配列 4 本に持つ。Java として素直な書き方で、オブジェクトを経由しないぶん Processing 側が
  遅くならない。mokume 側も同じデータ構造にして、両側を行単位で対応させている

## 揃えられない差

どれも、片側だけ設定を変えないと揃わない (AGENTS.md「条件」)。だから揃えず、ここに書く。
Processing に選べる設定がある差は、Processing 側が速くなる既定のままにしている。

- **窓の大きさ。** Processing は `size(1280, 720)` で窓を 1280 × 720 点で開くが、mokume は
  描く解像度の半分の点で開き、大きさを選ぶ口が無い
  ([mokume#1624](https://github.com/mokume-metal/mokume/issues/1624))。mokume 側の
  `Recorder.swift` が最初のフレーム (暖機の中) で窓を 1280 × 720 点に広げて揃えている。
  両側とも 1280 × 720 px で描き、Retina では 2 倍に拡大して出す
- **乱数列。** 両側とも `randomSeed(1)` を呼ぶが、乱数の生成器が違うので粒子の初期配置は一致しない。
  どちらも画面の中に一様に散らばるので、描く仕事の量は変わらない
- **色の合成。** mokume は線形の色空間で合成し、Processing は sRGB の 8 bit の値のまま合成する。
  同じ `fill(255, 160)` でも mokume の粒のほうが明るく見える。mokume に sRGB のまま合成する設定は無い
- **縁のアンチエイリアス。** mokume は円の縁の被覆率を距離から出す (MSAA は使わない)。Processing (P2D) は
  既定の `smooth()` で 2x MSAA をかける。Processing の `smooth(4)` 以上は Processing 側を遅くするので、
  既定のままにしている
- **円の形と 1 個あたりの幾何。** mokume は円 1 個を四角 1 枚 (三角形 2 枚) で描き、形はシェーダで切り出す。
  Processing は直径 4 の円を 20 角形 (三角形 20 枚) に CPU で分割する。**速さの差の一因になりうる**が、
  どちらもその道具で `circle()` を呼んだときの既定の振る舞いである

## 回す

```bash
python3 harness/run.py particles
```

## 結果

まだ測っていない。
