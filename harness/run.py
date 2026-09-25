# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""1 事例を、粒子数などの負荷を段階的に上げながら両側で回し、フレーム間隔を集める。

    python3 harness/run.py particles
    python3 harness/run.py particles --counts 1000,20000 --impl mokume --measure 3

- mokume 側は `swift build -c release` した実行ファイルを直に起こす (`mokume run` を介さない —
  debug で回すと数字が別物になる。版の正本は Package.resolved)
- Processing 側は Processing.app の `cli --run` で起こす。場所は `MVP_PROCESSING` で変えられる
- どちらも窓を出す。**計測中は他の窓を前に出さない** (背面に回ると描画の頻度が落ちる)

結果は `results/<事例>-<時刻>/` に置く (gitignore 済み)。生の記録 1 回ぶんずつと、
`summary.json`、そして貼り付け用の Markdown の表を標準出力に出す。
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cases  # noqa: E402
import stats  # noqa: E402

DEFAULT_PROCESSING = "/Applications/Processing.app/Contents/MacOS/Processing"
IMPLEMENTATIONS = ("mokume", "processing")


def capture(command: List[str], cwd: Optional[Path] = None) -> str:
    return subprocess.run(command, cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def build_mokume(package: Path) -> Path:
    print(f"build: {package.relative_to(cases.ROOT)} (release)", file=sys.stderr)
    subprocess.run(["swift", "build", "-c", "release"], cwd=package, check=True)
    description = json.loads(capture(["swift", "package", "describe", "--type", "json"], cwd=package))
    executables = [p["name"] for p in description["products"] if "executable" in p["type"]]
    if len(executables) != 1:
        raise SystemExit(f"{package}: 実行ファイルの product はちょうど 1 つ要る ({executables})")
    return Path(capture(["swift", "build", "-c", "release", "--show-bin-path"], cwd=package)) / executables[0]


def mokume_version(package: Path) -> Optional[str]:
    resolved = package / "Package.resolved"
    if not resolved.is_file():
        return None
    for pin in json.loads(resolved.read_text()).get("pins", []):
        if pin.get("identity") == "mokume":
            return pin.get("state", {}).get("version")
    return None


def processing_version(executable: str) -> Optional[str]:
    plist = Path(executable).parent.parent / "Info.plist"
    try:
        return capture(["plutil", "-extract", "CFBundleShortVersionString", "raw", str(plist)])
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def machine() -> Dict[str, Optional[str]]:
    def sysctl(name: str) -> Optional[str]:
        try:
            return capture(["sysctl", "-n", name])
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    return {
        "model": sysctl("hw.model"),
        "chip": sysctl("machdep.cpu.brand_string"),
        "macos": platform.mac_ver()[0] or None,
    }


def run_once(command: List[str], env: Dict[str, str], output: Path, timeout: float) -> Dict[str, object]:
    """1 回起こして記録を読む。**待つ側が期限を持つ** — 窓が閉じずに残ったら殺して失敗にする。"""
    output.unlink(missing_ok=True)
    try:
        subprocess.run(command, env={**os.environ, **env}, timeout=timeout, check=True,
                       stdout=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"{timeout:.0f} 秒で終わらなかった: {' '.join(command)}")
    if not output.is_file():
        raise SystemExit(f"記録が書かれなかった: {output}")
    return json.loads(output.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case")
    parser.add_argument("--counts", default="1000,5000,10000,20000,50000,100000",
                        help="負荷 (MVP_COUNT) の段。カンマ区切り")
    parser.add_argument("--impl", default=",".join(IMPLEMENTATIONS), help="回す側。カンマ区切り")
    parser.add_argument("--warmup", type=float, default=2, help="捨てる秒数")
    parser.add_argument("--measure", type=float, default=5, help="測る秒数")
    parser.add_argument("--out", type=Path, help="結果の置き場 (既定は results/<事例>-<時刻>)")
    args = parser.parse_args()

    case = cases.load(args.case)
    counts = [int(c) for c in args.counts.split(",")]
    implementations = [i for i in args.impl.split(",") if i]
    unknown = set(implementations) - set(IMPLEMENTATIONS)
    if unknown:
        raise SystemExit(f"知らない側: {sorted(unknown)}")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = (args.out or cases.ROOT / "results" / f"{case.name}-{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=True)

    processing = os.environ.get("MVP_PROCESSING", DEFAULT_PROCESSING)
    commands: Dict[str, List[str]] = {}
    if "mokume" in implementations:
        commands["mokume"] = [str(build_mokume(case.mokume))]
    if "processing" in implementations:
        # --output はスケッチフォルダと別の場所でなければならず、--force は中身を消してから書く
        commands["processing"] = [processing, "cli", f"--sketch={case.processing}",
                                  f"--output={out / 'processing-build'}", "--force", "--run"]

    # Processing の cli は毎回コンパイルから始めるので、その分の余裕を見る
    timeout = args.warmup + args.measure + 120
    runs = []
    for count in counts:
        for implementation in implementations:
            record_path = out / f"{implementation}-{count}.json"
            print(f"run: {implementation} count={count}", file=sys.stderr)
            record = run_once(commands[implementation], {
                "MVP_COUNT": str(count), "MVP_WARMUP": str(args.warmup),
                "MVP_MEASURE": str(args.measure), "MVP_OUT": str(record_path),
            }, record_path, timeout)
            runs.append({"implementation": implementation, "count": count,
                         **stats.summarize(record["intervals_ms"])})

    summary = {
        "case": case.name,
        "measured_at": stamp,
        "machine": machine(),
        "versions": {"mokume": mokume_version(case.mokume), "processing": processing_version(processing)},
        "warmup_s": args.warmup,
        "measure_s": args.measure,
        "runs": runs,
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(table(summary, counts, implementations))
    print(f"\n結果: {out}", file=sys.stderr)


def table(summary: Dict, counts: List[int], implementations: List[str]) -> str:
    by_key = {(r["implementation"], r["count"]): r for r in summary["runs"]}
    lines = ["| count | " + " | ".join(f"{i} fps (p95 ms)" for i in implementations) + " |",
             "| ---: | " + " | ".join("---:" for _ in implementations) + " |"]
    for count in counts:
        cells = []
        for implementation in implementations:
            r = by_key[(implementation, count)]
            cells.append(f"{r['fps']:.1f} ({r['p95_ms']:.1f})")
        lines.append(f"| {count} | " + " | ".join(cells) + " |")
    versions = summary["versions"]
    m = summary["machine"]
    lines.append("")
    lines.append(f"{m['chip']} ({m['model']}) / macOS {m['macos']} / mokume {versions['mokume']} / "
                 f"Processing {versions['processing']} / warmup {summary['warmup_s']} s, measure {summary['measure_s']} s")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
