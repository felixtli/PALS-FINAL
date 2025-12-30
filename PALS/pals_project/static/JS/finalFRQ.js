document.addEventListener("DOMContentLoaded", function () {
    const submit_button = document.getElementById("final-submit");

    submit_button.addEventListener("click", async function handleSubmitClick(e) {
        await submitCode(window.sessionID);

        window.location.href = '/final/'

        // Final tick and analytics send before continuing
        tick();
        if (idleTimer) clearTimeout(idleTimer);

        const end = Date.now();
        send(visibleAccum, end);
    });
});