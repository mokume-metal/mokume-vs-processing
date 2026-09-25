// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

// 数万個の粒子を壁で跳ね返らせて描く。mokume/Sources/Particles/Particles.swift と同じ仕事をする
// (揃えている条件は docs/decisions/0001-fair-comparison.md)。

Recorder recorder;
float[] xs, ys, vxs, vys;

void settings() {
  // P2D は Processing の GPU の経路 (OpenGL)。既定の JAVA2D は CPU で描くので、比べる相手として
  // 公正でない (ADR-0001)
  size(1280, 720, P2D);
  pixelDensity(1);
}

void setup() {
  frameRate(60);
  surface.setTitle("particles — processing");
  recorder = new Recorder("processing");
  randomSeed(1);
  int n = recorder.count;
  xs = new float[n];
  ys = new float[n];
  vxs = new float[n];
  vys = new float[n];
  for (int i = 0; i < n; i++) {
    xs[i] = random(width);
    ys[i] = random(height);
    vxs[i] = random(-2, 2);
    vys[i] = random(-2, 2);
  }
}

void draw() {
  recorder.tick();
  background(0);
  noStroke();
  fill(255, 160);
  for (int i = 0; i < recorder.count; i++) {
    xs[i] += vxs[i];
    ys[i] += vys[i];
    if (xs[i] < 0 || xs[i] > width) vxs[i] = -vxs[i];
    if (ys[i] < 0 || ys[i] > height) vys[i] = -vys[i];
    circle(xs[i], ys[i], 4);
  }
}
