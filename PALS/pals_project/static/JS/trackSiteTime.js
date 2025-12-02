(function(){

  if (window.location.pathname.startsWith("/admin/")) {
    return;
  }

  let active = true;
  let lastActive = Date.now();
  let totalActive = 0;
  let lastSend = Date.now();

  const SESSION_KEY = sessionStorage.getItem("site_session_key") ||
    (function() {
      const key = "sess_" + Math.random().toString(36).slice(2);
      sessionStorage.setItem("site_session_key", key);
      return key;
    })();

function updateActiveState() {
  const now = Date.now();

  if (document.hidden || !document.hasFocus()) { // Tab is not active
    if (active) {
      totalActive += now - lastActive; // close out the active period
      active = false;
    }
  } else { // Tab is visible and focused
    if (!active) {
      // Just became active again
      lastActive = now;
      active = true;
    } else {
      // Still active -> accumulate time since last check
      totalActive += now - lastActive;
      lastActive = now;
    }
  }
}

setInterval(() => {
  updateActiveState();

  if (Date.now() - lastSend >= 10000) {
    const duration = totalActive;
    totalActive = 0;
    lastSend = Date.now();

    navigator.sendBeacon(
      "/analytics/track-website-time/",
      new Blob(
        [JSON.stringify({
          session_key: SESSION_KEY,
          duration_ms: duration,
        })],
        { type: "application/json" }
      )
    );
  }
}, 1000);

  window.addEventListener("beforeunload", () => { // send any remaining time on unload
    updateActiveState();
    const duration = totalActive;
    if (duration > 0) {
      navigator.sendBeacon("/track_website_time/", new Blob([
        JSON.stringify({
          session_key: SESSION_KEY,
          duration_ms: duration,
        })
      ], {type: "application/json"}));
    }
  });
})();