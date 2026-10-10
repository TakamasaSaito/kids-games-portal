'use strict';
// Speech — VOICEVOX 音声再生 + TTS フォールバック
// グローバル名 Speech を予約 (R4: ゲーム側で再定義しない)
// ゲーム固有の追加メソッド (speakCount 等) はゲーム側で後付け拡張する
// audio-engine.js の後に読み込むこと (AudioEngine.isEnabled() を参照する)
const Speech = (() => {
  const supported = 'speechSynthesis' in window;
  let selectedVoice = null;

  function selectVoice() {
    if (!supported) return;
    try {
      const voices = speechSynthesis.getVoices();
      const ja = voices.filter(v => v.lang && v.lang.startsWith('ja'));
      if (!ja.length) return;
      selectedVoice =
        ja.find(v => /Nanami|Natural/i.test(v.name)) ||
        ja.find(v => v.name.includes('Google 日本語')) ||
        ja.find(v => v.name.includes('Kyoko')) ||
        ja[0];
    } catch (e) {}
  }

  // R1: タップハンドラの先頭で呼ぶ (iOS Safari TTS アンロック)
  function init() {
    if (!supported) return;
    try {
      speechSynthesis.addEventListener('voiceschanged', selectVoice);
      selectVoice();
      const u = new SpeechSynthesisUtterance('');
      u.lang = 'ja-JP';
      u.volume = 0;
      speechSynthesis.speak(u);
    } catch (e) {}
  }

  function _tts(text) {
    if (!supported) return;
    try {
      speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang  = 'ja-JP';
      u.rate  = 1.0;
      u.pitch = 1.1;
      if (selectedVoice) u.voice = selectedVoice;
      speechSynthesis.speak(u);
    } catch (e) {}
  }

  // file を指定すると AudioPlayer 経由で再生し、失敗時に TTS にフォールバック
  // AudioEngine がオフのときは何もしない (TTS も出力しない)
  function speak(text, file) {
    if (!AudioEngine.isEnabled()) return;
    if (file) {
      AudioPlayer.play(file, () => _tts(text));
      return;
    }
    _tts(text);
  }

  function cancel() {
    if (!supported) return;
    try { speechSynthesis.cancel(); } catch (e) {}
  }

  return { init, speak, cancel };
})();
