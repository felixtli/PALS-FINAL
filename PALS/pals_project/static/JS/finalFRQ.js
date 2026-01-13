document.addEventListener("DOMContentLoaded", function () {
  const submit_button = document.getElementById("final-submit");

  if (window.codeMirrorEditor && typeof window.codeMirrorEditor.setValue === "function") {
    window.codeMirrorEditor.setValue(window.codeSubmission || "");
  }

  function getCSRFToken() {
    const name = "csrftoken=";
    const decodedCookie = decodeURIComponent(document.cookie);
    const parts = decodedCookie.split(";");
    for (let i = 0; i < parts.length; i++) {
      let c = parts[i].trim();
      if (c.indexOf(name) === 0) return c.substring(name.length, c.length);
    }
    return "";
  }

  submit_button.addEventListener("click", async function () {
    try {
      // 1) grade/save response
      await submitCode(window.sessionID);

      // 2) ask server where to go next
      const resp = await fetch("/final-frq/advance/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({}),
      });

      const data = await resp.json();

      // 3) redirect
      if (data && data.status === "ok" && data.next_url) {
        window.location.href = data.next_url;
      } else {
        window.location.href = "/final/";
      }
    } catch (err) {
      console.error("Final FRQ submit failed:", err);
      window.location.href = "/final/";
    }
  });
});
