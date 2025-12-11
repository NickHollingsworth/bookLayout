(function () {
  const DEV_PARAM_VALUES = ['1', 'true', 'yes', 'on'];
  const DEFAULT_POLL_INTERVAL_MS = 1000;

  document.addEventListener('DOMContentLoaded', () => {
    restoreScrollPosition();

    if (!isDevModeEnabled()) {
      return; // Stable mode: no auto reload
    }

    startDevReloadLoop(DEFAULT_POLL_INTERVAL_MS);
  });

  function isDevModeEnabled() {
    const params = new URLSearchParams(window.location.search);
    const dev = params.get('dev');
    if (!dev) return false;
    return DEV_PARAM_VALUES.includes(dev.toLowerCase());
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
      sessionStorage.setItem('dev_scrollY', String(scrollY));
    } catch (e) {
      // ignore storage issues
    }
  }

  function restoreScrollPosition() {
    try {
      const stored = sessionStorage.getItem('dev_scrollY');
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

