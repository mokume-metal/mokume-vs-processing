<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# 0000 — このリポジトリの判断を ADR に残す

## 状態

採用 (2026-09-25)

## 文脈

mokume の外のパッケージは ADR を持たず、判断は mokume の ADR に従う (mokume ADR-0026 決定 1 の
第 3 段)。しかしこのリポジトリはパッケージではなく、**比べ方**という mokume の ADR が扱わない
判断を自分で持つ。比べ方の根拠が残っていないと、数字を読んだ人に「なぜこの条件か」を答えられない。

## 決定

- このリポジトリだけが持つ判断 (比べ方・事例の選び方・結果の出し方) は `docs/decisions/` に
  ADR として残す。書き方は mokume の `docs/decisions/AGENTS.md` に倣う
- mokume 自身の設計判断はここに書かない。mokume に求めることができたら mokume 側へ Issue を立てる

## 影響

- mokume ADR-0026 の第 3 段 (ADR を持たない) から外れる。外れる理由は AGENTS.md の「違うこと」に書く
