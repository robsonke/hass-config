// different custom scripts to fix small UI issues

// ---------------------------------------------------------------------------
// Reclaim the toolbar's space when the HA header is hidden (e.g. on the kiosk
// tablet). The Material You theme pins --header-height: 64px, so HA keeps a
// 64px padding-top on #view even after the header is hidden — leaving an empty
// gap at the top. This polls for the header's real visibility and zeroes the
// view's top padding only while it's hidden; on devices where the toolbar is
// shown it does nothing. Mechanism-agnostic: works no matter what hid it.
//
// It also clamps #view's min-height (HA forces it to 100vh) to the real
// visible height: on a kiosk webview 100vh can be taller than the visible
// area, so the over-tall container adds bottom whitespace and an unwanted
// scroll. Clamping to documentElement.clientHeight removes that scroll while
// still letting genuinely long content scroll normally.
(function () {
  let view = null,
    header = null;

  function locate() {
    const main = document
      .querySelector('home-assistant')
      ?.shadowRoot?.querySelector('home-assistant-main')?.shadowRoot;
    if (!main) return;
    // ha-panel-lovelace may sit directly under main or under the panel resolver
    const panel =
      main.querySelector('ha-panel-lovelace') ||
      main
        .querySelector('partial-panel-resolver, ha-drawer, app-drawer-layout')
        ?.querySelector?.('ha-panel-lovelace');
    const huiRoot = panel?.shadowRoot?.querySelector('hui-root')?.shadowRoot;
    if (!huiRoot) return;
    view = huiRoot.querySelector('#view');
    header = huiRoot.querySelector('.header');
  }

  function tick() {
    if (!view || !view.isConnected || !header || !header.isConnected) locate();
    if (!view || !header) return;
    const hidden = header.offsetHeight === 0;
    // top: drop the 64px header padding when the toolbar is hidden
    const padWanted = hidden ? 'env(safe-area-inset-top, 0px)' : '';
    if (view.style.paddingTop !== padWanted) view.style.paddingTop = padWanted;
    // bottom: clamp the 100vh min-height to the actual visible height so the
    // container doesn't overshoot the viewport and cause a needless scroll
    const mhWanted = hidden ? document.documentElement.clientHeight + 'px' : '';
    if (view.style.minHeight !== mhWanted) view.style.minHeight = mhWanted;
  }

  setInterval(tick, 1000);
  tick();
})();