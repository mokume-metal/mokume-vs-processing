<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# mokume-vs-processing

[Processing](https://processing.org/) で書かれるのとほぼ同じスケッチを
[mokume](https://github.com/mokume-metal/mokume) (Swift + Metal) でも書き、**同じ機械・同じ条件で
並べて**、速さと書き味を比べる事例集。

- **速さ** — 目標 60 fps のまま、負荷 (粒子の数など) をどこまで上げられるか
- **書き方** — 同じ絵を描くコードが、両側でどう違うか

比べ方の条件 (何を揃え、何を比べないか) は [ADR-0001](docs/decisions/0001-fair-comparison.md) が正本。
数字を読む前に一度読んでほしい。

## 事例

| 事例 | 何を描くか | 負荷 |
| --- | --- | --- |
| [particles](cases/particles/) | 壁で跳ね返る半透明の円 | 粒子の数 |

## 並べ方

```
cases/<事例>/
  README.md                        何を比べているか・結果の表
  mokume/<Sketch>/Package.swift    mokume 側 (SwiftPM パッケージ。mokume の版は exact で固定)
  processing/<Sketch>/<Sketch>.pde Processing 側 (スケッチフォルダ)
harness/                           両側を回して集計する (スケッチとの取り決めは harness/README.md)
```

## 回す

要るもの: macOS 26 以降の Apple Silicon の Mac、Xcode (Swift 6.2 以降)、
[Processing 4](https://processing.org/download) (`/Applications/Processing.app`)。

```bash
python3 harness/run.py particles                 # 両側を負荷の段ごとに回して表を出す
mokume run -c release cases/particles/mokume/Particles   # mokume 側を窓で見るだけ
```

計測中は両側の窓が順に開く。**他の窓を前に出さない** — 背面に回った窓は描画の頻度が落ちる。

## ライセンス

[MIT](LICENSE)
