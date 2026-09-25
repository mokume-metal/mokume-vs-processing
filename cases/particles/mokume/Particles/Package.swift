// swift-tools-version: 6.2
// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

import PackageDescription

// 1 事例の片側 = 1 SwiftPM パッケージ。`mokume run` の単位と同じで、実行ファイルは 1 つだけ
// 宣言する (ハーネスは products から名前を取る)
let package = Package(
    name: "Particles",
    platforms: [.macOS("26.0")],
    products: [.executable(name: "Particles", targets: ["Particles"])],
    dependencies: [
        // **どの版で測ったかは Package.resolved が持つ。** 結果にはこの版が刻まれる
        .package(url: "https://github.com/mokume-metal/mokume.git", exact: "0.11.2")
    ],
    targets: [
        .executableTarget(
            name: "Particles",
            dependencies: [.product(name: "mokume", package: "mokume")],
            swiftSettings: [.swiftLanguageMode(.v6), .defaultIsolation(MainActor.self)])
    ]
)
