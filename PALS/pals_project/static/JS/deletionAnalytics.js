// Code solution deletion tracker
// TODO: Detect more types of deletions: write over selection and paste over selection
const textarea = document.getElementById("code-input-area");

let lastValue = textarea.value;
let oldValue = "";

textarea.addEventListener("input", () => {
    const newValue = textarea.value;

    const diff = getDiff(oldValue, newValue);
    console.log(JSON.stringify(diff, null, 2));

    oldValue = newValue;
});

function getDiff(oldText, newText) {
    let start = 0;

    // Find first index where they differ
    while (start < oldText.length && start < newText.length &&
           oldText[start] === newText[start]) {
        start++;
    }

    // Find last index where they differ
    let endOld = oldText.length - 1;
    let endNew = newText.length - 1;

    while (endOld >= start && endNew >= start &&
           oldText[endOld] === newText[endNew]) {
        endOld--;
        endNew--;
    }

    return {
        replaced: oldText.slice(start, endOld + 1),
        inserted: newText.slice(start, endNew + 1),
        startIndex: start
    };
}

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

async function trackDeletion(deleted_content) {
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch(`/analytics/track-deletion/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({
                "session_id" : window.sessionID,
                "content" : deleted_content,
                "position" : textarea.selectionStart,
                "length" : deleted_content.length
            })
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const returned_json = await response.json();
        console.log(returned_json.status);
    } catch (error) {
        console.error(error.message);
    }
}