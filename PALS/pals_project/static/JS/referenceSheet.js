function initializeReferenceSheet() {
    const toggleButton = document.getElementById("reference-toggle");
    const modal = document.getElementById("reference-modal");
    const closeButton = document.getElementById("reference-close");
    const closeTargets = document.querySelectorAll("[data-reference-close]");

    if (!toggleButton || !modal || !closeButton) {
        return;
    }

    function openReference() {
        modal.classList.add("open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("reference-open");
    }

    function closeReference() {
        modal.classList.remove("open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("reference-open");
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
