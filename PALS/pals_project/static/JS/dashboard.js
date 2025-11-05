const endpoint = "/analytics/track-time/";
const startedAt = Date.now();
let visibleAccum = 0;
let lastTick = startedAt;
let isVisible = !document.hidden;
let idle = false;
const IDLE_MS = 120000; // pause if no activity for 2 mins
let idleTimer = null;

function tick() {
    const now = Date.now();
    if (isVisible && !idle) {
        visibleAccum += now - lastTick;
    }
    lastTick = now;
}

function resetIdle() {
    idle = false;
    lastTick = Date.now();
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { idle = true; tick(); }, IDLE_MS);
}

// Activity listeners for idle detection
["mousemove","keydown","wheel","touchstart"].forEach(ev => {
    window.addEventListener(ev, resetIdle, {passive: true});
});
resetIdle();

document.addEventListener("visibilitychange", () => {
    tick();
    isVisible = !document.hidden;
    lastTick = Date.now();
});

function send(durationMs, endedAtMs, heartbeat=false) {
    const payload = {
        duration_ms: Math.max(0, Math.round(durationMs)),
        started_at_ms: startedAt,
        ended_at_ms: endedAtMs,
        path: location.pathname + location.search + location.hash,
        referrer: document.referrer || "",
        visible_only: true,
        idle_threshold_ms: IDLE_MS,
        heartbeat: heartbeat
    };
    const blob = new Blob([JSON.stringify(payload)], {type:"application/json"});
    navigator.sendBeacon(endpoint, blob);
}

// Optional: heartbeat in case the tab crashes or the user closes the laptop.
const HEARTBEAT_MS = 120000; // 2 minutes
const hb = setInterval(() => { tick(); send(visibleAccum, Date.now(), true); }, HEARTBEAT_MS);

// On unload/navigation
window.addEventListener("pagehide", () => {
    tick();
    clearInterval(hb);
    send(visibleAccum, Date.now(), false);
});
