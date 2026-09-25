// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

import Foundation

/// ハーネスとの取り決め (harness/README.md「スケッチとの取り決め」) の mokume 側。
///
/// **統計はここで取らない。** フレームの間隔を生のまま書き出し、平均や分位はハーネスが両側に
/// 同じ式で掛ける。Processing 側の `Recorder.pde` と振る舞いを揃えておく。
final class Recorder {
    let implementation: String
    let count: Int
    let warmup: Double
    let measure: Double
    let output: String?

    private var start: UInt64?
    private var last: UInt64?
    private var intervals: [Double] = []
    private var finished = false

    init(implementation: String, environment: [String: String] = ProcessInfo.processInfo.environment) {
        self.implementation = implementation
        count = environment["MVP_COUNT"].flatMap(Int.init) ?? 10_000
        warmup = environment["MVP_WARMUP"].flatMap(Double.init) ?? 2
        measure = environment["MVP_MEASURE"].flatMap(Double.init) ?? 5
        output = environment["MVP_OUT"]
    }

    /// `draw()` の頭で 1 度呼ぶ。間隔は draw の開始どうしで測る — draw の中は図形を溜めるだけで、
    /// 符号化と GPU への投入はその後に走るので、draw の所要時間では仕事の全体が見えない。
    func tick() {
        guard !finished else { return }
        let now = DispatchTime.now().uptimeNanoseconds
        guard let start else {
            self.start = now
            last = now
            return
        }
        let elapsed = Double(now - start) / 1e9
        if elapsed >= warmup, let last { intervals.append(Double(now - last) / 1e6) }
        last = now
        if elapsed >= warmup + measure { finish() }
    }

    private func finish() {
        finished = true
        let record: [String: Any] = [
            "implementation": implementation, "count": count, "intervals_ms": intervals,
        ]
        do {
            let data = try JSONSerialization.data(withJSONObject: record)
            if let output {
                try data.write(to: URL(fileURLWithPath: output))
            } else {
                FileHandle.standardOutput.write(data)
            }
            exit(0)
        } catch {
            FileHandle.standardError.write(Data("記録を書けない: \(error)\n".utf8))
            exit(1)
        }
    }
}
