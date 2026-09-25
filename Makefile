# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT

# 検査の入口は ci-check の 1 つ。CI はこれを呼ぶだけ (mokume ADR-0026 決定 1 の第 1 段)。
# 計測 (harness/run.py) は窓と GPU が要るのでここには入れない。

.PHONY: ci-check cases harness-test reuse-lint

ci-check: cases harness-test reuse-lint ## push の前に通す

cases: ## どの事例も両側と README が揃っているか
	python3 harness/cases.py

harness-test: ## ハーネスの GPU を要さない部分
	python3 -m unittest discover -s harness -p 'test_*.py'

reuse-lint: ## 帰属の宣言 (pip install reuse)
	reuse lint
