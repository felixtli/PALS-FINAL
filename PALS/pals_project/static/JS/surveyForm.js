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

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("survey-form");
  const submitBtn = document.getElementById("survey-submit");
  const feedbackContainer = document.getElementById('feedback-container');

  submitBtn.addEventListener("click", function(event) {
    event.preventDefault();

    const fieldsets = form.querySelectorAll("fieldset");
    const responses = {};
    let allAnswered = true;
    let firstMissingQuestion = null;

    fieldsets.forEach((fieldset) => {
      const radios = fieldset.querySelectorAll("input[type='radio']");
      const name = radios[0]?.name;

      const checked = fieldset.querySelector("input[type='radio']:checked");

      if (!checked) {
        allAnswered = false;
        if (!firstMissingQuestion) {
          firstMissingQuestion =
            fieldset.querySelector("legend")?.innerText ||
            "a question";
        }
      } else {
        responses[name] = checked.value;
      }
    });

    if (!allAnswered) {
      alert(`Please answer all questions.\nMissing: "${firstMissingQuestion}"`);
      return;
    }

    console.group("Survey Responses");
    Object.entries(responses).forEach(([key, value]) => {
      console.log(`${key}:`, value);
    });
    console.log("Session ID:", window.sessionID);
    console.groupEnd();

    feedbackContainer.style.visibility = 'visible';

    postSurveyResponse(responses);
  });
});

async function postSurveyResponse(surveyResponse) {
    const csrftoken = getCookie('csrftoken');
    try {
        const response = await fetch(`/${window.sessionID}/post-survey-response/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"survey_response" : surveyResponse})
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        
    } catch (error) {
        console.error(error.message);
    }
}

async function navigateToDashboard() {
    const csrftoken = getCookie('csrftoken');
    const response = await fetch("/dashboard/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrftoken
        },
        body: JSON.stringify({ request_type: "next_question" })
    });

    if (response.redirected) {
        window.location.href = response.url;
    } else {
        window.location.href = "/dashboard/";
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const surveySubmit = document.getElementById('survey-submit');
    const feedbackContainer = document.getElementById('feedback-container');
    surveySubmit.addEventListener('click', function (event) {
        event.preventDefault();

        feedbackContainer.style.visibility = 'visible';
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const navigationButton = document.getElementById("navigation-btn");
    navigationButton.addEventListener("click", function () {
        navigateToDashboard();
    });
});
