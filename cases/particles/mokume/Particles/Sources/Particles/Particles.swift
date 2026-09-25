// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

import mokume

/// 数万個の粒子を壁で跳ね返らせて描く。`processing/Particles/Particles.pde` と同じ仕事をする
/// (揃えている条件は docs/decisions/0001-fair-comparison.md)。
@main
final class Particles: Sketch {
    var settings = SketchSettings(
        width: 1280, height: 720, frameRate: 60, title: "particles — mokume", pixelDensity: 1)

    lazy var recorder = Recorder(
        implementation: "mokume", windowWidth: settings.width, windowHeight: settings.height)
    var xs: [Float] = []
    var ys: [Float] = []
    var vxs: [Float] = []
    var vys: [Float] = []

    func setup() {
        randomSeed(1)
        for _ in 0..<recorder.count {
            xs.append(random(width))
            ys.append(random(height))
            vxs.append(random(-2, 2))
            vys.append(random(-2, 2))
        }
    }

    func draw() {
        recorder.tick()
        background(0)
        noStroke()
        fill(255, 160)
        for i in 0..<recorder.count {
            xs[i] += vxs[i]
            ys[i] += vys[i]
            if xs[i] < 0 || xs[i] > width { vxs[i] = -vxs[i] }
            if ys[i] < 0 || ys[i] > height { vys[i] = -vys[i] }
            circle(xs[i], ys[i], 4)
        }
    }
}
