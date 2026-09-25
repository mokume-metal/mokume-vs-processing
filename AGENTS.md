<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# AGENTS.md

**規約の正典は [mokume の AGENTS.md](https://github.com/mokume-metal/mokume/blob/main/AGENTS.md) である。**
Issue の起こし方・分類・コメントの置き場と署名・コミットと PR の書式・機構を足す順序 (実害 → Issue → 機構)
は、あちらを読んで同じように振る舞う。**ここには写しを置かない** (mokume ADR-0026 決定 3)。

このファイルが持つのは、**このリポジトリだけで違うこと**だけである。

## 違うこと

| | mokume | ここ |
| --- | --- | --- |
| 何のためのリポジトリか | ライブラリ本体 | **外の人に見せる事例集。** 数字は mokume を選ぶ根拠として読まれる |
| 設計判断の正典 | `docs/decisions/` の ADR | **同じく持つ** — ただし扱うのは比べ方だけ ([ADR-0000](docs/decisions/0000-record-decisions.md))。外のパッケージが ADR を持たない (ADR-0026 第 3 段) のから外れる |
| 検査 | `make ci-check` | `make ci-check` (**事例の並び・ハーネス・reuse lint の 3 本**)。足すのは実害が出てから |
| 描画の証跡 | 描画 PR に必須 | **求めない** (ADR-0026 第 3 段)。代わりに、スケッチを触った PR には計測の表を貼る |
| ルールセットと App | あり | **まだ無い** (ADR-0026 第 2 段。育ってから 2 つ同時に入れる) |
| 版の張り方 | — | mokume は **`exact`** で固定する。版を上げる PR で全事例を測り直して表を貼り替える |

## 比べ方を崩さないこと

- **1 つの事例の中で両側のコードは同じ書き方に揃える。** mokume にしかない速い書き方は別の事例にする ([ADR-0001](docs/decisions/0001-fair-comparison.md) 決定 4)
- **mokume に有利な条件を足さない。** 迷ったら Processing 側を速くする方へ倒す (P2D を使う・暖機を捨てる)。偏りが後で見抜かれると、全部の数字が信用を失う
- **debug の数字を載せない。** harness は release で組む
- **表には harness が出す最後の 1 行 (機械・版・条件) を必ず添える**

## 踏みやすいこと

- mokume 側のパッケージを `mokume/` の直下に置かない。SwiftPM の識別名がフォルダ名から付き、依存の `mokume` と衝突する (`harness/cases.py` の冒頭)
- Processing 側で `record` を変数名にしない。Java 16 からの予約語で、前処理が構文エラーにする
- **計測は CI では回らない。** 窓と GPU が要る。CI の緑は「数字が正しい」を意味しない
- mokume の不具合を見つけたら mokume 側へ起票する。ここに回避策を書き足さない
