# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""事例の並びを読む。並べ方の正本は README.md「並べ方」で、ここはそれを機械で引く側。

1 事例 = `cases/<名前>/` に 2 つの片側と README.md。片側はどちらも**フォルダを 1 つだけ**持つ:

- `mokume/<Sketch>/Package.swift` — 実行ファイルを 1 つ宣言する SwiftPM パッケージ
- `processing/<Sketch>/<Sketch>.pde` — Processing のスケッチフォルダ (フォルダ名と主 .pde の名前が一致する)

mokume 側を `mokume/` の直下にしないのは、SwiftPM がパッケージの識別名をフォルダ名から
取るためである。直下に置くと識別名が依存の `mokume` と衝突し、解決が失敗する。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Case:
    name: str
    mokume: Path
    processing: Path


def _only_folder(side: Path) -> Optional[Path]:
    folders = [p for p in side.glob("*") if p.is_dir() and not p.name.startswith(".")]
    return folders[0] if len(folders) == 1 else None


def problems(case_dir: Path) -> List[str]:
    """片側が欠けている・形が崩れているところを列挙する。空なら 1 事例として揃っている。"""
    found = []
    for side, main in (("mokume", "Package.swift"), ("processing", None)):
        folder = _only_folder(case_dir / side)
        if folder is None:
            found.append(f"{case_dir.name}: {side}/ の下にフォルダがちょうど 1 つ要る")
            continue
        expected = main or f"{folder.name}.pde"
        if not (folder / expected).is_file():
            found.append(f"{case_dir.name}: {side}/{folder.name}/{expected} が無い")
    if not (case_dir / "README.md").is_file():
        found.append(f"{case_dir.name}: README.md が無い (何を比べているかを書く)")
    return found


def load(name: str, root: Path = ROOT) -> Case:
    case_dir = root / "cases" / name
    if not case_dir.is_dir():
        raise SystemExit(f"事例が無い: cases/{name}")
    found = problems(case_dir)
    if found:
        raise SystemExit("\n".join(found))
    return Case(name, _only_folder(case_dir / "mokume"), _only_folder(case_dir / "processing"))


def all_problems(root: Path = ROOT) -> List[str]:
    found = []
    for case_dir in sorted(p for p in (root / "cases").glob("*") if p.is_dir()):
        found.extend(problems(case_dir))
    return found


if __name__ == "__main__":
    import sys

    issues = all_problems()
    for line in issues:
        print(f"NG: {line}", file=sys.stderr)
    if not issues:
        print("OK: 事例はどれも両側が揃っている")
    sys.exit(1 if issues else 0)
