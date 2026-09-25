# SPDX-FileCopyrightText: 2026 mokume-metal
# SPDX-License-Identifier: MIT
"""1 事例を、粒子数などの負荷を段階的に上げながら両側で回し、フレーム間隔を集める。

    python3 harness/run.py particles
    python3 harness/run.py particles --counts 1000,20000 --impl mokume --measure 3 --repeat 1

- mokume 側は `swift build -c release` した実行ファイルを直に起こす (`mokume run` を介さない —
  debug で回すと数字が別物になる。版の正本は Package.resolved)
- Processing 側は Processing.app の `cli --run` で起こす。場所は `MVP_PROCESSING` で変えられる
- どちらも窓を出す。**計測中は他の窓を前に出さない** (背面に回ると描画の頻度が落ちる)
- 全段を `--repeat` 回掃く。段ごとに両側を続けて回し、**回ごとに先に回す側を入れ替える**
  (片側だけが温まった・冷えた状態で測らない)。表は回の中央値と、fps の最小〜最大を出す

結果は `results/<事例>-<時刻>/` に置く (gitignore 済み): 生の記録 1 回ぶんずつ・`summary.json` (1 回ずつの
`runs` と、段ごとにまとめた `aggregates`)・貼り付け用の Markdown の表 `summary.md`・子プロセスの出力 `logs/`。

端末には、途中は 1 回ごとの進み具合を 1 行ずつ (stderr)、最後に両側を並べた表を stdout に出す。
子プロセスの出力は `logs/` へ逃がし、失敗したときだけ末尾を端末に出す。
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


def run_logged(command: List[str], log: Path, *, cwd: Optional[Path] = None,
               env: Optional[Dict[str, str]] = None, timeout: Optional[float] = None) -> None:
    """出力を `log` へ書いて回す。失敗したら末尾を端末に出して止まる。"""
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with log.open("w") as handle:
            subprocess.run(command, cwd=cwd, env=env, timeout=timeout, check=True,
                           stdout=handle, stderr=subprocess.STDOUT)
    except subprocess.TimeoutExpired:
        raise SystemExit(f"{timeout:.0f} 秒で終わらなかった: {' '.join(command)}\n{tail(log)}")
    except subprocess.CalledProcessError as error:
        raise SystemExit(f"失敗した (終了コード {error.returncode}): {' '.join(command)}\n{tail(log)}")


def tail(log: Path, lines: int = 20) -> str:
    text = log.read_text(errors="replace").splitlines() if log.is_file() else []
    return "\n".join([f"--- {log} の末尾 ---", *text[-lines:]])


def build_mokume(package: Path, logs: Path) -> Path:
    print(f"build: {package.relative_to(cases.ROOT)} (release)", file=sys.stderr)
    run_logged(["swift", "build", "-c", "release"], logs / "mokume-build.log", cwd=package)
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


def run_once(command: List[str], env: Dict[str, str], output: Path, log: Path,
             timeout: float) -> Dict[str, object]:
    """1 回起こして記録を読む。**待つ側が期限を持つ** — 窓が閉じずに残ったら殺して失敗にする。"""
    output.unlink(missing_ok=True)
    run_logged(command, log, env={**os.environ, **env}, timeout=timeout)
    if not output.is_file():
        raise SystemExit(f"記録が書かれなかった: {output}\n{tail(log)}")
    return json.loads(output.read_text())


def order(implementations: List[str], repeat: int) -> List[str]:
    """その回に回す側の順。回ごとに入れ替え、どちらかが常に先 (冷えた機械) にならないようにする。"""
    return list(reversed(implementations)) if repeat % 2 else list(implementations)


def aggregates(runs: List[Dict]) -> List[Dict]:
    """(側, 段) ごとに回をまとめる。並びは最初に現れた順。"""
    grouped: Dict[tuple, List[Dict]] = {}
    for r in runs:
        grouped.setdefault((r["implementation"], r["count"]), []).append(r)
    return [{"implementation": i, "count": c, **stats.aggregate(group)}
            for (i, c), group in grouped.items()]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("case")
    parser.add_argument("--counts", default="1000,5000,10000,20000,50000,100000",
                        help="負荷 (MVP_COUNT) の段。カンマ区切り")
    parser.add_argument("--impl", default=",".join(IMPLEMENTATIONS), help="回す側。カンマ区切り")
    parser.add_argument("--warmup", type=float, default=2, help="捨てる秒数")
    parser.add_argument("--measure", type=float, default=5, help="測る秒数")
    parser.add_argument("--repeat", type=int, default=3, help="全段を掃く回数 (ADR-0001 決定 3)")
    parser.add_argument("--out", type=Path, help="結果の置き場 (既定は results/<事例>-<時刻>)")
    args = parser.parse_args()

    case = cases.load(args.case)
    counts = [int(c) for c in args.counts.split(",")]
    implementations = [i for i in args.impl.split(",") if i]
    unknown = set(implementations) - set(IMPLEMENTATIONS)
    if unknown:
        raise SystemExit(f"知らない側: {sorted(unknown)}")
    if args.repeat < 1:
        raise SystemExit("--repeat は 1 以上")

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out = (args.out or cases.ROOT / "results" / f"{case.name}-{stamp}").resolve()
    out.mkdir(parents=True, exist_ok=True)

    logs = out / "logs"
    processing = os.environ.get("MVP_PROCESSING", DEFAULT_PROCESSING)
    commands: Dict[str, List[str]] = {}
    if "mokume" in implementations:
        commands["mokume"] = [str(build_mokume(case.mokume, logs))]
    if "processing" in implementations:
        # --output はスケッチフォルダと別の場所でなければならず、--force は中身を消してから書く
        commands["processing"] = [processing, "cli", f"--sketch={case.processing}",
                                  f"--output={out / 'processing-build'}", "--force", "--run"]

    # Processing の cli は毎回コンパイルから始めるので、その分の余裕を見る
    timeout = args.warmup + args.measure + 120
    runs = []
    total = args.repeat * len(counts) * len(implementations)
    width = max(len(i) for i in implementations)
    for repeat in range(args.repeat):
        for count in counts:
            for implementation in order(implementations, repeat):
                name = f"{implementation}-{count}-r{repeat + 1}"
                record_path = out / f"{name}.json"
                print(f"[{len(runs) + 1:>{len(str(total))}}/{total}] r{repeat + 1} {implementation:<{width}} "
                      f"count={count:>7} ... ", end="", file=sys.stderr, flush=True)
                record = run_once(commands[implementation], {
                    "MVP_COUNT": str(count), "MVP_WARMUP": str(args.warmup),
                    "MVP_MEASURE": str(args.measure), "MVP_OUT": str(record_path),
                }, record_path, logs / f"{name}.log", timeout)
                run = {"implementation": implementation, "count": count, "repeat": repeat + 1,
                       **stats.summarize(record["intervals_ms"])}
                runs.append(run)
                print(f"{run['fps']:5.1f} fps (p95 {run['p95_ms']:.1f} ms)", file=sys.stderr)

    summary = {
        "case": case.name,
        "measured_at": stamp,
        "machine": machine(),
        "versions": {"mokume": mokume_version(case.mokume), "processing": processing_version(processing)},
        "warmup_s": args.warmup,
        "measure_s": args.measure,
        "repeat": args.repeat,
        "runs": runs,
        "aggregates": aggregates(runs),
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    (out / "summary.md").write_text(markdown_table(summary, counts, implementations) + "\n")
    print(file=sys.stderr)
    print(terminal_table(summary, counts, implementations))
    print(f"\n結果: {out}\n貼り付け用の表: {out / 'summary.md'}", file=sys.stderr)


def conditions(summary: Dict) -> str:
    """表に必ず添える条件の 1 行 (AGENTS.md「載せ方」)。"""
    versions = summary["versions"]
    m = summary["machine"]
    return (f"{m['chip']} ({m['model']}) / macOS {m['macos']} / mokume {versions['mokume']} / "
            f"Processing {versions['processing']} / warmup {summary['warmup_s']} s, "
            f"measure {summary['measure_s']} s, repeat {summary['repeat']}")


def ratio_applies(implementations: List[str]) -> bool:
    return set(IMPLEMENTATIONS) <= set(implementations)


def by_key(summary: Dict) -> Dict[tuple, Dict]:
    return {(a["implementation"], a["count"]): a for a in summary["aggregates"]}


def fps_range(a: Dict) -> str:
    """回ごとの fps の最小〜最大。1 回だけなら範囲は無い。"""
    return f"{a['fps_min']:.1f}–{a['fps_max']:.1f}" if a["repeats"] > 1 else ""


def terminal_table(summary: Dict, counts: List[int], implementations: List[str]) -> str:
    """端末で読む表。両側の fps と分位 (回の中央値) を並べ、繰り返したときは fps の最小〜最大を、
    両側を回したときは fps の比 (mokume ÷ processing) を足す。"""
    table = by_key(summary)
    metrics = ("fps", "p50_ms", "p95_ms", "p99_ms")
    ranged = summary["repeat"] > 1
    header = [f"{'count':>7}"]
    subheader = [" " * 7]
    for implementation in implementations:
        names = [f"{m.removesuffix('_ms'):>6}" for m in metrics]
        if ranged:
            names.insert(1, f"{'min–max':>11}")
        group = " ".join(names)
        header.append(f"{implementation:^{len(group)}}")
        subheader.append(group)
    if ratio_applies(implementations):
        header.append(f"{'ratio':>7}")
        subheader.append(f"{'m / p':>7}")
    rows = []
    for count in counts:
        cells = [f"{count:>7}"]
        for implementation in implementations:
            a = table[(implementation, count)]
            values = [f"{a[m]:>6.1f}" for m in metrics]
            if ranged:
                values.insert(1, f"{fps_range(a):>11}")
            cells.append(" ".join(values))
        if ratio_applies(implementations):
            ratio = table[("mokume", count)]["fps"] / table[("processing", count)]["fps"]
            cells.append(f"{ratio:>6.2f}x")
        rows.append(cells)
    widths = [len(c) for c in header]
    rule = "-+-".join("-" * w for w in widths)
    lines = [f"{summary['case']} — fps は多いほど、p50 / p95 / p99 (フレーム間隔 ms) は少ないほどよい"
             f" (値は {summary['repeat']} 回の中央値)",
             "", " | ".join(header).rstrip(), " | ".join(subheader), rule]
    lines += [" | ".join(cells) for cells in rows]
    lines += ["", conditions(summary)]
    return "\n".join(lines)


def markdown_table(summary: Dict, counts: List[int], implementations: List[str]) -> str:
    """事例の README に貼る表。fps は回の中央値と [最小–最大]、括弧は p95 の中央値。"""
    table = by_key(summary)
    lines = ["| count | " + " | ".join(f"{i} fps (p95 ms)" for i in implementations) + " |",
             "| ---: | " + " | ".join("---:" for _ in implementations) + " |"]
    for count in counts:
        cells = []
        for implementation in implementations:
            a = table[(implementation, count)]
            spread = f" [{fps_range(a)}]" if a["repeats"] > 1 else ""
            cells.append(f"{a['fps']:.1f}{spread} ({a['p95_ms']:.1f})")
        lines.append(f"| {count} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append(conditions(summary))
    return "\n".join(lines)


if __name__ == "__main__":
    main()
