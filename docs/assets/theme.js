/* 明暗の切替。OSの設定に自動追従し、ボタンで上書きしたときだけ localStorage に覚える。
   上書きした結果がOSの設定と同じになったら記録を消して、自動追従に戻す。 */
(function () {
  var KEY = "theme";
  var root = document.documentElement;
  var mq = window.matchMedia("(prefers-color-scheme: dark)");
  var btn = document.querySelector(".theme-toggle");
  var metas = document.querySelectorAll('meta[name="theme-color"]');

  function isDark() {
    var t = root.getAttribute("data-theme");
    return t ? t === "dark" : mq.matches;
  }

  function sync() {
    var dark = isDark();
    if (btn) btn.setAttribute("aria-pressed", dark ? "true" : "false");
    var paper = getComputedStyle(root).getPropertyValue("--paper").trim();
    if (paper) {
      for (var i = 0; i < metas.length; i++) metas[i].setAttribute("content", paper);
    }
  }

  function set(dark) {
    var value = dark ? "dark" : "light";
    if (dark === mq.matches) {
      root.removeAttribute("data-theme");
      try { localStorage.removeItem(KEY); } catch (e) { /* 保存できなくても表示は切り替わる */ }
    } else {
      root.setAttribute("data-theme", value);
      try { localStorage.setItem(KEY, value); } catch (e) { /* 同上 */ }
    }
    sync();
  }

  if (btn) btn.addEventListener("click", function () { set(!isDark()); });
  if (mq.addEventListener) mq.addEventListener("change", sync);
  else if (mq.addListener) mq.addListener(sync);
  sync();
})();
