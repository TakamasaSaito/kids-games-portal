'use strict';
// AudioEngine — Web Audio API による効果音合成
// グローバル名 AudioEngine を予約 (R4: ゲーム側で再定義しない)
// ゲーム固有の追加メソッド (playPop 等) はゲーム側で後付け拡張する
const AudioEngine = (() => {
  let ctx = null;
  let masterGain = null;
  let enabled = true;

  function getCtx() {
    if (!ctx) {
      try {
        ctx = new (window.AudioContext || window.webkitAudioContext)();
        masterGain = ctx.createGain();
        masterGain.gain.value = 0.5;
        masterGain.connect(ctx.destination);
      } catch (e) { return null; }
    }
    return ctx;
  }

  // R1: タップハンドラの先頭で同期的に呼ぶ (iOS Safari 音声アンロック)
  function resume() {
    const c = getCtx();
    if (c && c.state === 'suspended') c.resume().catch(() => {});
  }

  function setEnabled(val) {
    enabled = val;
    if (masterGain) masterGain.gain.value = val ? 0.5 : 0;
  }

  function isEnabled() { return enabled; }

  function playTone(freq, type, startTime, duration, gainVal = 0.6) {
    const c = getCtx();
    if (!c || !enabled) return;
    try {
      const osc = c.createOscillator();
      const g   = c.createGain();
      osc.connect(g);
      g.connect(masterGain);
      osc.type = type;
      osc.frequency.setValueAtTime(freq, startTime);
      g.gain.setValueAtTime(gainVal, startTime);
      g.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
      osc.start(startTime);
      osc.stop(startTime + duration);
    } catch (e) {}
  }

  function playCorrect() {
    const c = getCtx();
    if (!c || !enabled) return;
    const now = c.currentTime;
    playTone(659.25, 'sine', now, 0.25, 0.7);
    playTone(1046.5, 'sine', now + 0.18, 0.35, 0.7);
  }

  function playWrong() {
    const c = getCtx();
    if (!c || !enabled) return;
    const now = c.currentTime;
    playTone(220, 'sine', now, 0.3, 0.35);
  }

  function playClear() {
    const c = getCtx();
    if (!c || !enabled) return;
    const now = c.currentTime;
    [523.25, 659.25, 783.99, 1046.5, 1318.5].forEach((f, i) =>
      playTone(f, 'sine', now + i * 0.12, 0.3, 0.6)
    );
  }

  function playClick() {
    const c = getCtx();
    if (!c || !enabled) return;
    const now = c.currentTime;
    playTone(880, 'sine', now, 0.06, 0.2);
  }

  return { resume, setEnabled, isEnabled, playCorrect, playWrong, playClear, playClick };
})();
