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

document.addEventListener('DOMContentLoaded', function() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]');

  checkboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      if (this.checked) {
        checkboxes.forEach(otherCheckbox => {
          if (otherCheckbox !== this) {
            otherCheckbox.checked = false;
          }
        });
      }
    });
  });
});

async function postSurveyResponse(surveyResponse) {
    const csrftoken = getCookie('csrftoken');
    window.alert("This is the window id: " + window.sessionID);
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

        const checkedValues = Array.from(
            document.querySelectorAll('input[type="checkbox"]:checked')
        ).map(cb => cb.value);

        if (checkedValues.length === 0) {
            alert("Please select an option before submitting the survey.");
            return;
        }

        console.log("Submitted value: " + checkedValues);

        postSurveyResponse(checkedValues[0]);

        feedbackContainer.style.visibility = 'visible';
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const navigationButton = document.getElementById("navigation-btn");
    navigationButton.addEventListener("click", function () {
        navigateToDashboard();
    });
});
