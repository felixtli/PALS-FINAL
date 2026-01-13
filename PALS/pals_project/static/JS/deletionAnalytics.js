// Tracks user code deletions
let oldValue = "";

document.addEventListener("DOMContentLoaded", function () {
  const editor = window.codeMirrorEditor;
  if (!editor) {
    console.error("CodeMirror editor not found. Ensure window.codeMirrorEditor is set.");
    return;
  }

  // Initialize baseline
  oldValue = editor.getValue();

  // Track changes via CodeMirror
  editor.on("change", () => {
    const newValue = editor.getValue();

    const diff = getDiff(oldValue, newValue);
    console.log(JSON.stringify(diff, null, 2));

    if (diff.isDeletion === true) {
      trackDeletion(diff);
    }

    oldValue = newValue;
  });
});

function getDiff(oldText, newText) {
  let start = 0;

  // Find first index where they differ
  while (
    start < oldText.length &&
    start < newText.length &&
    oldText[start] === newText[start]
  ) {
    start++;
  }

  // Find last index where they differ
  let endOld = oldText.length - 1;
  let endNew = newText.length - 1;

  while (endOld >= start && endNew >= start && oldText[endOld] === newText[endNew]) {
    endOld--;
    endNew--;
  }

  let isDeletion = false;
  let deletionLength = null;

  if (newText.length < oldText.length) {
    isDeletion = true;
    deletionLength = oldText.length - newText.length;
  }

  return {
    replaced: oldText.slice(start, endOld + 1),
    inserted: newText.slice(start, endNew + 1),
    startIndex: start,
    isDeletion,
    deletionLength,
  };
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

async function trackDeletion(diff) {
  const csrftoken = getCookie("csrftoken");

  try {
    const response = await fetch(`/analytics/track-deletion/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrftoken,
      },
      body: JSON.stringify({
        session_id: window.sessionID,
        deleted_content: diff.replaced,
        new_content: diff.inserted,
        position: diff.startIndex,
        length: diff.deletionLength,
      }),
    });

    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }
    const returned_json = await response.json();
    console.log(returned_json.status);
  } catch (error) {
    console.error(error.message);
  }
}