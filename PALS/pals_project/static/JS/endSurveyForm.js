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

async function postSurveyResponse() {
    const csrftoken = getCookie('csrftoken');
    const form = document.getElementById("survey-form");

    const getRadioValue = (name) => {
        const checked = form.querySelector(`input[name="${name}"]:checked`);
        return checked ? parseInt(checked.value) : null;
    };

    const getSelectValue = (name) => {
        const value = form.querySelector(`select[name="${name}"]`).value;
        if (value.endsWith("+")) {
            return parseInt(value); // "3+" → 3
        }
        return value === "" ? null : parseInt(value);
    };

    const getTextValue = (name) =>
        form.querySelector(`textarea[name="${name}"]`).value.trim();

    const surveyResponse = {
        // ======================
        // A. Background
        // ======================
        courses_completed: getSelectValue("courses_completed"),
        years_experience: getSelectValue("years_experience"),
        ml_familiarity: getRadioValue("ml_familiarity"),
        current_fatigue: getRadioValue("rested"),

        // ======================
        // B. Usability
        // ======================
        ease_of_use: getRadioValue("easy_to_use"),
        feedback_helpfulness: getRadioValue("helpful_feedback"),
        challenge_match: getRadioValue("challenge_match"),
        reuse_intent: getRadioValue("reuse_intent"),

        // ======================
        // C. Engagement & Attention
        // ======================
        focus_level: getRadioValue("focused"),
        time_distortion: getRadioValue("time_flew"),

        // ======================
        // D. Cognitive Load
        // ======================
        mental_demand: getRadioValue("mental_demand"),
        effort: getRadioValue("effort"),
        frustration: getRadioValue("frustration"),

        // ======================
        // E. Trust & Fairness
        // ======================
        trusted_system: getRadioValue("trusted_system"),
        fairness: getRadioValue("fair_system"),

        // ======================
        // F. Open-Ended
        // ======================
        liked_most: getTextValue("like_most"),
        liked_least: getTextValue("like_least"),
        change_one_thing: getTextValue("change_one"),
        additional_comments: getTextValue("additional_comments"),

        // ======================
        // G. Manipulation Check
        // ======================
        // difficulty_notice: form.querySelector(
            // 'input[name="noticed_adaptation"]:checked'
        // )?.value || null
    };

    try {
        const response = await fetch(
            `/post-experiment-survey-submission/`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrftoken
                },
                body: JSON.stringify({ survey_response: surveyResponse })
            }
        );

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        console.log("Survey successfully submitted");
    } catch (error) {
        console.error("Survey submission failed:", error.message);
    }
}

document.getElementById("survey-form").addEventListener("submit", async function (e) {
    e.preventDefault();
    await postSurveyResponse();
    window.location.href = "/mcq-assessment/";
});
