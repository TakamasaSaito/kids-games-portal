'use strict';
// createGameState — localStorage を使ったゲーム状態管理のファクトリ
// グローバル名 createGameState を予約 (R4: ゲーム側で再定義しない)
//
// 使い方:
//   const GameState = createGameState('my-game-v1', () => ({
//     totalCorrect: 0,
//     setClearCount: 0,
//     myStats: { ... },
//   }));
//   let state = GameState.load();
//   GameState.save(state);
//   state = GameState.reset();
//
// load() は defaultsFn() の値をベースに保存済みデータを Object.assign でマージして返す
function createGameState(storageKey, defaultsFn) {
  function load() {
    try {
      const raw = localStorage.getItem(storageKey);
      if (raw) {
        const data = JSON.parse(raw);
        return Object.assign(defaultsFn(), data);
      }
    } catch (e) {}
    return defaultsFn();
  }

  function save(state) {
    try {
      localStorage.setItem(storageKey, JSON.stringify(state));
    } catch (e) {}
  }

  function reset() {
    try { localStorage.removeItem(storageKey); } catch (e) {}
    return defaultsFn();
  }

  return { load, save, reset };
}
