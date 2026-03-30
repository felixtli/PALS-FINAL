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
    const BATCH_SIZE = 50;
    const SEND_INTERVAL_MS = 3000;

    const SESSION_KEY = sessionStorage.getItem("site_session_key") ||
    (function() {
      const key = "sess_" + Math.random().toString(36).slice(2);
      sessionStorage.setItem("site_session_key", key);
      return key;
    })();

    let lastMoveTime = 0;
    const MOVE_THROTTLE_MS = 50;

    function recordPoint(x, y) {
        const now = Date.now();
        if (now - lastMoveTime < MOVE_THROTTLE_MS) return;
        lastMoveTime = now;

        points.push({
            x: x,
            y: y,
            vw: window.innerWidth,
            vh: window.innerHeight,
            sy: window.scrollY || window.pageYOffset,
            t: now
        });

        if (points.length >= BATCH_SIZE) {
            sendBatch();
        }
    }

    function onMouseMove(e) {
        recordPoint(e.clientX, e.clientY);
    }

function sendBatch() {
        if (!points.length) return;
        const payload = {
            path: window.location.pathname,
            session_id: SESSION_KEY,
            points: points.splice(0, points.length)
        };

        fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": (typeof CSRFTOKEN !== "undefined" ? CSRFTOKEN : "")
            },
            body: JSON.stringify(payload),
            keepalive: true
        }).catch(() => {});
    }

    // Flush buffer every 3 seconds regardless of mouse activity
    setInterval(sendBatch, SEND_INTERVAL_MS);

    // Send remaining points when leaving the page
    window.addEventListener("beforeunload", sendBatch);

    // Only track on non-admin pages
    if (!window.location.pathname.startsWith("/admin/")) {
        window.addEventListener("mousemove", onMouseMove);
    }
})();
