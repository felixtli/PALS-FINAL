// Helper function to get CSRF token from cookies
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


// Analytics tracking code starts here
const endpoint = "/analytics/track-time/";
const startedAt = Date.now();
let visibleAccum = 0;
let lastTick = startedAt;
let isVisible = !document.hidden;
let idle = false;
const IDLE_MS = 120000; // pause if no activity for 2 mins
let idleTimer = null;

function tick() {
    const now = Date.now();
    if (isVisible && !idle) {
        visibleAccum += now - lastTick;
    }
    lastTick = now;
}

function resetIdle() {
    tick();
    idle = false;
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { 
        idle = true;
        tick();     
    }, IDLE_MS);
}

// Activity listeners for idle detection
["mousemove","keydown","wheel","touchstart"].forEach(ev => {
    window.addEventListener(ev, resetIdle, {passive: true});
});
resetIdle();

document.addEventListener("visibilitychange", () => {
    tick();
    isVisible = !document.hidden;
    lastTick = Date.now();
});

function send(durationMs, endedAtMs) {
    const payload = {
        duration_ms: Math.max(0, Math.round(durationMs)),
        started_at_ms: startedAt,
        ended_at_ms: endedAtMs,
        path: location.pathname + location.search + location.hash,
        referrer: document.referrer || "",
        visible_only: true,
        idle_threshold_ms: IDLE_MS,
        heartbeat: false        // always false now: this is a final submit
    };
    const blob = new Blob([JSON.stringify(payload)], { type: "application/json" });
    navigator.sendBeacon(endpoint, blob);
}
// Analytics tracking code ends here


// Loads saved code submission on page load // CHECK IF THIS IS BROKEN
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('code-input-area');
    textarea.value = window.codeSubmission;
});

// Saves code submission to server
async function saveCode(id) {
    const code = window.codeMirrorEditor.getValue();
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch(`/${id}/save/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : code})
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

async function createCompilerOutputElement(compiled_output) {
    const now = new Date();

    const formatted_date = now.toLocaleString('en-US', {
        weekday: 'long',   
        year: 'numeric',  
        month: 'long',     
        day: 'numeric',    
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    }) + '<br>';

    const newOutput = document.createElement("p");
    newOutput.classList.add("compiler-output");

    newOutput.innerHTML = formatted_date + "\n" + compiled_output;

    document.querySelector(".compiler-container").appendChild(newOutput);
}

async function askAI(id) {
    const code = window.codeMirrorEditor.getValue();
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    await testCode(id); // Compile code before asking AI
    const compiler_output = document.querySelector(".compiler-container").lastElementChild.innerText; // Get latest compiler output

    try {
        const response = await fetch(`/${id}/ask-ai/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : code, "compiler_output" : compiler_output})
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const returned_json = await response.json();
        const AI_response = returned_json.AI_response;
        
        createCompilerOutputElement(AI_response); // Display compiler output
        saveCode(id); // Save code after compilation
        
    } catch (error) {
        console.error(error.message);
    }
}

// Sends code to server for compilation and displays output
async function testCode(id)
{
    const code = window.codeMirrorEditor.getValue();
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch("/compile/", {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : code})
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }
        const returned_json = await response.json();
        const compiled_output = returned_json.compiled_output;

        createCompilerOutputElement(compiled_output); // Display compiler output
        saveCode(id); // Save code after compilation
        
    } catch (error) {
        console.error(error.message);
    }
}

async function submitCode(id) {
    const code = window.codeMirrorEditor.getValue();
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie
    await saveCode(id); // Save code before submission

    try {
        const response = await fetch(`/${id}/submit-code/`, {
            method: "POST",   // changed to POST
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrftoken
            },
            body: JSON.stringify({
                code: code  // send the code if you want backend to use it
            })
        });

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const returned_json = await response.json();
        const status = returned_json.status;
        const casesSolved = returned_json.casesSolved;

        // Create a final heartbeat send at submission time
        tick();
        clearInterval(hb);
        send(visibleAccum, Date.now(), false);

    } catch (error) {
        console.error("Error in submitCode:", error.message);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const test_button = document.getElementById("test");
    test_button.addEventListener("click", function () {
        testCode(window.sessionID);
    })
})

document.addEventListener("DOMContentLoaded", function () {
    const ask_ai_button = document.getElementById("ask-ai");
    ask_ai_button.addEventListener("click", function () {
        askAI(window.sessionID);
    })
})

document.addEventListener("DOMContentLoaded", function () {
    const clear_compiler_button = document.getElementById("clear-compiler");
    const compiler_container = document.querySelector(".compiler-container");
    clear_compiler_button.addEventListener("click", function () {
        const paragraphs = compiler_container.querySelectorAll("p");

        paragraphs.forEach(p => {
            if (p.id !== "original-compiler-message") {
                p.remove();
            }
        });
    })
})

document.addEventListener("DOMContentLoaded", function () {
    const submit_button = document.getElementById("submit");

    submit_button.addEventListener("click", async function handleSubmitClick(e) {
        await submitCode(window.sessionID);

        window.location.href = `/${window.sessionID}/survey/`

        // Final tick and analytics send before continuing
        tick();
        if (idleTimer) clearTimeout(idleTimer);

        const end = Date.now();
        send(visibleAccum, end);
    });
});

window.addEventListener("beforeunload", function() {
    console.log("beforeunload fired!");
    const code = window.codeMirrorEditor.getValue();
    const csrftoken = getCookie("csrftoken");

    const payload = JSON.stringify({
        submission: code
    });

     const blob = new Blob([payload], {
        type: "application/json"
    });

    const url = `/${window.sessionID}/save/`;

    navigator.sendBeacon(url, blob);
});