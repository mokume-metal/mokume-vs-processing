// SPDX-FileCopyrightText: 2026 mokume-metal
// SPDX-License-Identifier: MIT

// ハーネスとの取り決め (harness/README.md「スケッチとの取り決め」) の Processing 側。
//
// 統計はここで取らない。フレームの間隔を生のまま書き出し、平均や分位はハーネスが両側に
// 同じ式で掛ける。mokume 側の Recorder.swift と振る舞いを揃えておく。
class Recorder {
  String implementation;
  int count;
  double warmup;
  double measure;
  String output;

  long start = -1;
  long last = -1;
  FloatList intervals = new FloatList();
  boolean finished = false;

  Recorder(String implementation) {
    this.implementation = implementation;
    count = envInt("MVP_COUNT", 10000);
    warmup = envDouble("MVP_WARMUP", 2);
    measure = envDouble("MVP_MEASURE", 5);
    output = System.getenv("MVP_OUT");
  }

  // draw() の頭で 1 度呼ぶ。間隔は draw の開始どうしで測る (mokume 側と同じ理由)
  void tick() {
    if (finished) return;
    long now = System.nanoTime();
    if (start < 0) {
      start = now;
      last = now;
      return;
    }
    double elapsed = (now - start) / 1e9;
    if (elapsed >= warmup) intervals.append((float) ((now - last) / 1e6));
    last = now;
    if (elapsed >= warmup + measure) finish();
  }

  void finish() {
    finished = true;
    // record とは名付けない。Java 16 からの予約語で、Processing の前処理が構文エラーにする
    JSONObject result = new JSONObject();
    result.setString("implementation", implementation);
    result.setInt("count", count);
    JSONArray values = new JSONArray();
    for (int i = 0; i < intervals.size(); i++) values.append(intervals.get(i));
    result.setJSONArray("intervals_ms", values);
    if (output != null) {
      saveJSONObject(result, output, "compact");
    } else {
      println(result.format(-1));
    }
    exit();
  }

  int envInt(String name, int fallback) {
    String value = System.getenv(name);
    return value == null ? fallback : Integer.parseInt(value);
  }

  double envDouble(String name, double fallback) {
    String value = System.getenv(name);
    return value == null ? fallback : Double.parseDouble(value);
  }
}
