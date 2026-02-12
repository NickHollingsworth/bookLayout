(function () {
  const DEV_PARAM_VALUES = ['true', 'yes', 'on'];
  const DEFAULT_POLL_INTERVAL_MS = 1000;

  document.addEventListener('DOMContentLoaded', () => {
    restoreScrollPosition();

    const intervalMs = getDevReloadIntervalMs();
    if (intervalMs === null) {
      return; // Stable mode: no auto reload
    }

    startDevReloadLoop(intervalMs);
  });

  function getDevReloadIntervalMs() {
    const params = new URLSearchParams(window.location.search);
    const reload = params.get('reload');
    if (!reload) return null;

    const v = reload.toLowerCase().trim();

    // Numeric value means seconds, e.g. ?reload=2 or ?reload=0.5
    const seconds = Number(v);
    if (Number.isFinite(seconds) && seconds > 0) {
      return Math.round(seconds * 1000);
    }

    // Boolean-style enable, e.g. ?reload=true / ?reload=yes / ?reload=on
    if (DEV_PARAM_VALUES.includes(v)) {
      return DEFAULT_POLL_INTERVAL_MS;
    }

    // Back-compat: ?reload=1 enables default interval
    if (v === '1') {
      return DEFAULT_POLL_INTERVAL_MS;
    }

    return null;
  }

  function startDevReloadLoop(intervalMs) {
    let lastSeenStamp = document.lastModified || null;

    setInterval(async () => {
      try {
        const response = await fetch(window.location.href, {
          method: 'HEAD',
          cache: 'no-store'
        });

        const serverStamp =
          response.headers.get('Last-Modified') ||
          response.headers.get('ETag') ||
          null;

        if (!serverStamp) {
          return;
        }

        if (lastSeenStamp && serverStamp !== lastSeenStamp) {
          rememberScrollPosition();
          window.location.reload();
        }

        lastSeenStamp = serverStamp;
      } catch (err) {
        console.error('Dev reload check failed:', err);
      }
    }, intervalMs);
  }

  function rememberScrollPosition() {
    try {
      const scrollY = window.scrollY || document.documentElement.scrollTop || 0;
      sessionStorage.setItem('reload_scrollY', String(scrollY));
    } catch (e) {
      // ignore storage issues
    }
  }

  function restoreScrollPosition() {
    try {
      const stored = sessionStorage.getItem('reload_scrollY');
      if (!stored) return;
      const y = parseInt(stored, 10);
      if (!Number.isNaN(y)) {
        window.scrollTo(0, y);
      }
    } catch (e) {
      // ignore storage issues
    }
  }
})();
