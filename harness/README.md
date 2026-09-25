<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# harness

事例を両側で回してフレーム間隔を集め、同じ式で要約する。使い方は `python3 harness/run.py --help`。

| | |
| --- | --- |
| [`run.py`](run.py) | 負荷の段ごとに両側を起こし、記録を集めて表にする |
| [`stats.py`](stats.py) | 間隔の列の要約 (fps・分位) |
| [`cases.py`](cases.py) | 事例の並びを読む・欠けを見つける |

## スケッチとの取り決め

両側のスケッチ (`Recorder.swift` / `Recorder.pde`) はこれに従う。**統計はスケッチの中で取らない。**

| 環境変数 | 意味 | 既定 |
| --- | --- | --- |
| `MVP_COUNT` | 負荷 (事例ごとに意味を README に書く) | 10000 |
| `MVP_WARMUP` | 捨てる秒数 | 2 |
| `MVP_MEASURE` | 測る秒数 | 5 |
| `MVP_OUT` | 記録を書くファイル。無ければ標準出力 | — |

- 最初の `tick()` で、窓の中身を描く大きさと同じ点に揃える (ADR-0001 決定 3「窓の大きさ」)。
  既定でそうなる側 (Processing) は何もしない
- `draw()` の頭で時刻を取り、最初の呼び出しからの経過が `MVP_WARMUP` を越えた後の間隔 (ms) を集める
- 経過が `MVP_WARMUP + MVP_MEASURE` を越えたら、次の JSON を書いて終了する

```json
{"implementation": "mokume", "count": 10000, "intervals_ms": [16.7, 16.6, ...]}
```

経路が環境変数なのは、`mokume run` が余分な引数を受け付けず、環境変数なら両側に同じ形で届くためである。
