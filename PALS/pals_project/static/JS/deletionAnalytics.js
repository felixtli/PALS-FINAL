// Code solution deletion tracker
// TODO: Detect more types of deletions: write over selection and paste over selection
const input = document.getElementById("code-input-area");

let lastValue = input.value;

input.addEventListener("beforeinput", (e) => {

    // Only handle deletion events. Return if not a deletion.
    if (!e.inputType.startsWith("delete")) return;

    const start = input.selectionStart;
    const end = input.selectionEnd;

    let deletedText = "";

    // Case 1: Deleting a selection of text
    if (start !== end) {
        deletedText = input.value.substring(start, end);
    }
    else {
        // Case 2: Single-character delete (backspace or delete key)
        if (e.inputType === "deleteContentBackward") {
            if (start > 0) {
                deletedText = input.value[start - 1];
            }
        }
        if (e.inputType === "deleteContentForward") {
            if (start < input.value.length) {
                deletedText = input.value[start];
            }
        }
    }

    console.log("Deleted text:", JSON.stringify(deletedText));
    console.log("InputType:", e.inputType);
    if (deletedText.length != 0)
    {
        trackDeletion(deletedText);
    }
});

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
                "position" : input.selectionStart,
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