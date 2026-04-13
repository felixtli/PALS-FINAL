function initializeReferenceSheet() {
    const toggleButton = document.getElementById("reference-toggle");
    const modal = document.getElementById("reference-modal");
    const closeButton = document.getElementById("reference-close");
    const closeTargets = document.querySelectorAll("[data-reference-close]");

    if (!toggleButton || !modal || !closeButton) {
        return;
    }

    let referenceOpenedAt = null;

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let cookie of cookies) {
                cookie = cookie.trim();
                if (cookie.startsWith(name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function trackReferenceSheet(openedAt, closedAt) {
        if (!window.sessionID) return;
        fetch("/analytics/track-reference-sheet/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                session_id: window.sessionID,
                opened_at: openedAt,
                closed_at: closedAt,
            }),
        }).catch((err) => console.error("track-reference-sheet error:", err));
    }

    function openReference() {
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("reference-open");
        referenceOpenedAt = new Date().toISOString();
    }

    function closeReference() {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("reference-open");
        if (referenceOpenedAt) {
            trackReferenceSheet(referenceOpenedAt, new Date().toISOString());
            referenceOpenedAt = null;
        }
    }

    toggleButton.addEventListener("click", openReference);
    closeButton.addEventListener("click", closeReference);

    closeTargets.forEach((node) => {
        node.addEventListener("click", closeReference);
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && modal.classList.contains("open")) {
            closeReference();
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeReferenceSheet);
} else {
    initializeReferenceSheet();
}
