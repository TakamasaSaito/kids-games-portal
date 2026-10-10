'use strict';
// UICommon — 全ゲーム共通の画面遷移・アニメ・イベントハンドラ
// グローバル名 UICommon を予約 (R4: ゲーム側で再定義しない)
//
// 依存: audio-engine.js / audio-player.js / speech.js (この順で先に読み込む)
//
// 使い方:
//   UICommon.init({
//     onStart:      () => { startGame(); },
//     onSpeakGame:  () => { Speech.speak(...); },
//     onNextClear:  () => { startGame(); },
//     onReset:      () => { state = GameState.reset(); },
//     renderStats:  () => { document.getElementById('parent-stats').innerHTML = ...; },  // 省略可
//     extraScreens: { level: document.getElementById('screen-level') },                  // 省略可
//   });
//
//   UICommon.showScreen('game');
//   UICommon.renderProgress(3, 10);
//   UICommon.jumpCharacter();
//   UICommon.spawnStars(cardElement);
//   UICommon.spawnConfetti();
const UICommon = (() => {
  let _screens = {};
  let _cfg = {};

  // ---- 画面切り替え ----
  function showScreen(name) {
    Object.values(_screens).forEach(s => s.classList.remove('active'));
    _screens[name].classList.add('active');
  }

  // ---- 進捗ドット ----
  function renderProgress(current, total) {
    document.getElementById('progress-label').textContent = `${current} / ${total}`;
    const dots = document.getElementById('progress-dots');
    dots.innerHTML = '';
    for (let i = 0; i < total; i++) {
      const d = document.createElement('div');
      d.className = 'progress-dot' + (i < current ? ' filled' : '');
      dots.appendChild(d);
    }
  }

  // ---- キャラジャンプ ----
  function jumpCharacter() {
    const c = document.getElementById('char-game');
    c.classList.remove('jump');
    void c.offsetWidth;
    c.classList.add('jump');
    setTimeout(() => c.classList.remove('jump'), 600);
  }

  // ---- スター演出 ----
  function spawnStars(el) {
    const rect = el.getBoundingClientRect();
    const cx   = rect.left + rect.width  / 2;
    const cy   = rect.top  + rect.height / 2;
    const stars = ['⭐','✨','🌟'];
    for (let i = 0; i < 5; i++) {
      const star  = document.createElement('div');
      star.className = 'star-burst';
      star.textContent = stars[i % stars.length];
      const angle = (i / 5) * Math.PI * 2;
      const dist  = 60 + Math.random() * 50;
      star.style.setProperty('--dx', Math.cos(angle) * dist + 'px');
      star.style.setProperty('--dy', Math.sin(angle) * dist + 'px');
      star.style.left = cx + 'px';
      star.style.top  = cy + 'px';
      document.body.appendChild(star);
      setTimeout(() => star.remove(), 850);
    }
  }

  // ---- 紙吹雪 ----
  // R6統一: タイムアウト 4500ms
  function spawnConfetti() {
    const container = document.getElementById('confetti-container');
    container.innerHTML = '';
    const colors = ['#FF6B6B','#FECA57','#48DBFB','#FF9FF3','#54A0FF','#1DD1A1','#FF9F43'];
    for (let i = 0; i < 60; i++) {
      const piece = document.createElement('div');
      piece.className = 'confetti-piece';
      piece.style.left = Math.random() * 100 + 'vw';
      piece.style.background = colors[Math.floor(Math.random() * colors.length)];
      piece.style.width  = (8 + Math.random() * 8) + 'px';
      piece.style.height = (8 + Math.random() * 8) + 'px';
      piece.style.animationDuration = (2 + Math.random() * 2) + 's';
      piece.style.animationDelay    = (Math.random() * 1) + 's';
      piece.style.borderRadius = Math.random() > 0.5 ? '50%' : '2px';
      container.appendChild(piece);
    }
    setTimeout(() => { container.innerHTML = ''; }, 4500);
  }

  // ---- 音量UI更新 ----
  function updateVolumeUI() {
    const on = AudioEngine.isEnabled();
    document.getElementById('toggle-volume').classList.toggle('on', on);
    document.getElementById('volume-label').textContent = on ? 'オン' : 'オフ';
  }

  // ---- 親メニューを開く ----
  function openParentMenu() {
    // R5: #parent-stats が存在しない場合 (hiragana-hunt 等) も例外を出さない
    const statsEl = document.getElementById('parent-stats');
    if (statsEl && _cfg.renderStats) {
      try { _cfg.renderStats(); } catch (e) {}
    }
    updateVolumeUI();
    document.getElementById('modal-parent').classList.add('active');
  }

  // ---- 初期化 ----
  function init(cfg) {
    _cfg = cfg || {};

    // 標準スクリーンを登録
    _screens = {
      splash: document.getElementById('screen-splash'),
      start:  document.getElementById('screen-start'),
      game:   document.getElementById('screen-game'),
      clear:  document.getElementById('screen-clear'),
    };
    // ゲーム固有スクリーン (hiragana-hunt の 'level' 等) を追加
    if (_cfg.extraScreens) Object.assign(_screens, _cfg.extraScreens);

    // ---- はじめるボタン ----
    // R1: AudioEngine.resume / AudioPlayer.unlock は同期的にタップハンドラの先頭で呼ぶ
    document.getElementById('btn-start').addEventListener('click', () => {
      AudioEngine.resume();
      AudioPlayer.unlock();
      Speech.init();
      AudioEngine.playClick();
      _cfg.onStart && _cfg.onStart();
    });

    // ---- 🏠 ホームボタン (ゲーム中) ----
    // iframe 内なら postMessage で親に通知、単体表示ならスタート画面へ
    document.getElementById('btn-home-game').addEventListener('click', () => {
      AudioEngine.playClick();
      Speech.cancel();
      if (window.parent !== window) {
        window.parent.postMessage({ type: 'go-home' }, '*');
      } else {
        showScreen('start');
      }
    });

    // ---- 🔊 スピークボタン ----
    document.getElementById('btn-speak').addEventListener('click', () => {
      AudioEngine.playClick();
      _cfg.onSpeakGame && _cfg.onSpeakGame();
    });

    // ---- クリア後「もういちど」/「つぎへ」ボタン ----
    document.getElementById('btn-next').addEventListener('click', () => {
      AudioEngine.playClick();
      _cfg.onNextClear && _cfg.onNextClear();
    });

    // ---- おわるボタン ----
    document.getElementById('btn-quit').addEventListener('click', () => {
      AudioEngine.playClick();
      Speech.cancel();
      showScreen('start');
    });

    // ---- ⚙ ギアボタン 長押し (3秒) ----
    let gearTimer = null;
    const gearBtn = document.getElementById('btn-gear');
    function startGearHold(e) {
      gearBtn.setPointerCapture(e.pointerId);
      gearBtn.classList.add('holding');
      gearTimer = setTimeout(() => {
        gearBtn.classList.remove('holding');
        openParentMenu();
      }, 3000);
    }
    function cancelGearHold() {
      if (gearTimer) { clearTimeout(gearTimer); gearTimer = null; }
      gearBtn.classList.remove('holding');
    }
    gearBtn.addEventListener('pointerdown',  startGearHold);
    gearBtn.addEventListener('pointerup',    cancelGearHold);
    gearBtn.addEventListener('pointercancel', cancelGearHold);
    gearBtn.addEventListener('pointerleave', cancelGearHold);
    gearBtn.addEventListener('contextmenu', e => e.preventDefault());

    // ---- 親メニュー とじる ----
    document.getElementById('btn-parent-close').addEventListener('click', () => {
      document.getElementById('modal-parent').classList.remove('active');
    });

    // ---- 音量トグル ----
    document.getElementById('toggle-volume').addEventListener('click', () => {
      const newVal = !AudioEngine.isEnabled();
      AudioEngine.setEnabled(newVal);
      if (newVal) AudioEngine.resume();
      updateVolumeUI();
    });

    // ---- リセット確認 ----
    document.getElementById('btn-reset-confirm').addEventListener('click', () => {
      document.getElementById('modal-parent').classList.remove('active');
      document.getElementById('modal-reset').classList.add('active');
    });

    // ---- リセット実行 ----
    // ゲーム側の onReset でステートをリセット後、共通でモーダル・音声・画面を処理
    document.getElementById('btn-reset-do').addEventListener('click', () => {
      _cfg.onReset && _cfg.onReset();
      document.getElementById('modal-reset').classList.remove('active');
      Speech.cancel();
      showScreen('start');
    });

    // ---- リセットキャンセル ----
    document.getElementById('btn-reset-cancel').addEventListener('click', () => {
      document.getElementById('modal-reset').classList.remove('active');
      document.getElementById('modal-parent').classList.add('active');
    });

    // ---- スプラッシュ → スタート ----
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      showScreen('start');
    } else {
      let splashDone = false;
      function endSplash() {
        if (splashDone) return;
        splashDone = true;
        _screens.splash.removeEventListener('pointerdown', endSplash);
        showScreen('start');
      }
      _screens.splash.addEventListener('pointerdown', endSplash);
      setTimeout(endSplash, 1500);
    }
  }

  return { init, showScreen, renderProgress, jumpCharacter, spawnStars, spawnConfetti };
})();
