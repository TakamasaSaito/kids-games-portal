'use strict';
// AudioPlayer — VOICEVOX 音声ファイル再生 (プール管理)
// グローバル名 AudioPlayer を予約 (R4: ゲーム側で再定義しない)
// 使い方:
//   AudioPlayer.preload(['q_a.wav', 'praise_1.wav', ...]);  // ゲーム側が呼ぶ
//   AudioPlayer.unlock();  // ユーザーのタップ時に同期的に呼ぶ (R1)
//   AudioPlayer.play('q_a.wav', fallbackFn);
//
// ゲーム固有の追加プール (counting-game の countPool 等) はゲーム側で管理する
const AudioPlayer = (() => {
  const SILENT = 'data:audio/wav;base64,UklGRiYAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQIAAAAAAA==';
  const pool = new Map();

  // ゲーム側が起動時に呼ぶ。files は 'audio/' 以下のファイル名の配列
  function preload(files) {
    files.forEach(file => {
      if (pool.has(file)) return;
      const a = new Audio();
      a.preload = 'auto';
      a.src = file.startsWith('../../') ? file : `audio/${file}`;
      pool.set(file, a);
    });
  }

  // R1: タップハンドラの先頭で同期的に呼ぶ (iOS Safari 音声アンロック)
  function unlock() {
    const u = new Audio(SILENT);
    u.play().catch(() => {});
    pool.forEach(a => { if (a.readyState === 0) a.load(); });
  }

  function play(file, fallback) {
    try { if ('speechSynthesis' in window) speechSynthesis.cancel(); } catch (e) {}
    const a = pool.get(file);
    if (!a) { fallback && fallback(); return; }
    pool.forEach((el, f) => { if (f !== file && !el.paused) { el.pause(); el.currentTime = 0; } });
    a.currentTime = 0;
    const p = a.play();
    if (p) p.catch(err => {
      if (err && err.name === 'AbortError') return;
      fallback && fallback();
    });
  }

  return { preload, unlock, play };
})();
