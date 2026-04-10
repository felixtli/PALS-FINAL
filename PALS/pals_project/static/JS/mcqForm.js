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

// Highlight answered questions
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("mcq-form");

    form.addEventListener("change", (e) => {
        if (e.target.type === "radio") {
            const fieldset = e.target.closest("fieldset");
            if (fieldset) fieldset.classList.add("answered");
        }
    });
});

// Submit handler
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("mcq-form");
    const submitBtn = document.getElementById("mcq-submit");

    submitBtn.addEventListener("click", async (e) => {
        e.preventDefault();

        const answers = {};
        let allAnswered = true;

        for (let i = 1; i <= 10; i++) {
            const checked = form.querySelector(`input[name="q${i}"]:checked`);
            if (!checked) {
                allAnswered = false;
            } else {
                answers[`q${i}`] = checked.value;
            }
        }

        if (!allAnswered) {
            alert("Please answer all 10 questions before submitting.");
            return;
        }

        const csrftoken = getCookie("csrftoken");

        try {
            const response = await fetch("/mcq-assessment/submit/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken,
                },
                body: JSON.stringify({ answers: answers }),
            });

            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }

            const data = await response.json();
            
           // Redirect to final page
           window.location.href = "/final/";

        } catch (error) {
            console.error("MCQ submit error:", error.message);
            alert("Something went wrong submitting your assessment. Please try again.");
        }
    });
});
