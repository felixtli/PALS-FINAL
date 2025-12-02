function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

(function () {
    const CSRFTOKEN = getCookie("csrftoken");
    const endpoint = "/analytics/track-cursor/";
    const points = [];
    const BATCH_SIZE = 50;        // send after 50 points
    const SEND_INTERVAL_MS = 3000; // or every 3s

    const SESSION_KEY = sessionStorage.getItem("site_session_key") ||
    (function() {
      const key = "sess_" + Math.random().toString(36).slice(2);
      sessionStorage.setItem("site_session_key", key);
      return key;
    })();

    let lastSent = Date.now();
    let lastMoveTime = 0;
    const MOVE_THROTTLE_MS = 50; // capture at most ~20 times/second

    function onMouseMove(e) {
        const now = Date.now();
        if (now - lastMoveTime < MOVE_THROTTLE_MS) return;
        lastMoveTime = now;

        const vw = window.innerWidth;
        const vh = window.innerHeight;
        const sy = window.scrollY || window.pageYOffset;

        points.push({
            x: e.clientX,
            y: e.clientY,
            vw: vw,
            vh: vh,
            sy: sy,
            t: now
        });

        if (points.length >= BATCH_SIZE || now - lastSent > SEND_INTERVAL_MS) {
            sendBatch();
        }
    }

    function sendBatch() {
        if (!points.length) return;
        const payload = {
            path: window.location.pathname,
            session_id: SESSION_KEY,
            points: points.splice(0, points.length)
        };
        lastSent = Date.now();

        fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": (typeof CSRFTOKEN !== "undefined" ? CSRFTOKEN : "")
            },
            body: JSON.stringify(payload),
            keepalive: true // So it can send on unload
        }).catch(() => {
        });
    }

    // send remaining points when leaving the page
    window.addEventListener("beforeunload", sendBatch);

    // only track on non-admin pages
    if (!window.location.pathname.startsWith("/admin/")) {
        window.addEventListener("mousemove", onMouseMove);
    }
})();