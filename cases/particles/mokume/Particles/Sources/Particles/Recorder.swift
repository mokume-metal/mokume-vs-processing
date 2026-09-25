// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

import AppKit
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

    /// 窓の中身を何点に広げるか。描く大きさ (`SketchSettings` の幅と高さ) を渡す。
    private let windowSize: NSSize

    init(
        implementation: String, windowWidth: Int, windowHeight: Int,
        environment: [String: String] = ProcessInfo.processInfo.environment
    ) {
        windowSize = NSSize(width: windowWidth, height: windowHeight)
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
            matchWindowSize()
            self.start = now
            last = now
            return
        }
        let elapsed = Double(now - start) / 1e9
        if elapsed >= warmup, let last { intervals.append(Double(now - last) / 1e6) }
        last = now
        if elapsed >= warmup + measure { finish() }
    }

    /// 窓の中身を、描く大きさと同じ点に広げる。
    ///
    /// mokume は窓を描く解像度の**半分の点**で開き、大きさを選ぶ口が無い
    /// ([mokume#1624](https://github.com/mokume-metal/mokume/issues/1624))。Processing の
    /// `size(1280, 720)` は 1280×720 点で開くので、そのままでは窓の見た目と画面へ出す画素数が
    /// 片側だけ違う。描く解像度は変えず、窓だけを Processing と同じ大きさにする。
    /// 最初の tick は暖機の中なので、広げた後の揺れは計測に入らない。口ができたらここを外す。
    private func matchWindowSize() {
        for window in NSApp.windows where window.styleMask.contains(.titled) {
            window.setContentSize(windowSize)
            // 左下を起点に広がるので、そのままだと画面の上へはみ出すことがある
            window.center()
        }
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
