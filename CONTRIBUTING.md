<!--
SPDX-FileCopyrightText: 2026 mokume-metal
SPDX-License-Identifier: MIT
-->

# CONTRIBUTING

進め方 (Issue → ブランチ → PR・Conventional Commits・squash merge) は
[mokume の AGENTS.md「進め方」](https://github.com/mokume-metal/mokume/blob/main/AGENTS.md#進め方) と同じ。
ここにはこのリポジトリで要る手順だけを書く。

## push の前に

```bash
make ci-check      # 事例の並び・ハーネスの検査・reuse lint (pip install reuse)
```

## 事例を足す

1. Issue (「事例の提案」のテンプレート) で、何を描いて何を負荷にするかを決める
2. `cases/<事例>/` に両側と README.md を置く (並べ方は README.md「並べ方」)
3. 両側のスケッチに `Recorder` を入れる。取り決めは [harness/README.md](harness/README.md)。
   今は事例ごとに写しを持つ — 2 件目の事例で揃え方が割れたら共有を考える
4. `python3 harness/run.py <事例>` で測り、事例の README の「結果」に表と最後の 1 行を貼る
5. PR の「確認方法」に同じ表を貼る

## mokume の版を上げる

`cases/*/mokume/*/Package.swift` の `exact:` を上げ、**全事例を測り直して**表を貼り替える。
表の版と Package.resolved の版がずれた状態で merge しない。

## 帰属

新しいファイルには、既存のファイルの冒頭と同じ SPDX ヘッダ (著作権 `2026 mokume-metal`・ライセンス MIT)
を付ける。ヘッダを持てないファイルだけ `REUSE.toml` に列挙する。
Processing の Examples など第三者のコードを移すときは、元の帰属とライセンスを正確に宣言する。
