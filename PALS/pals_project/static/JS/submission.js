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

// Loads saved code submission on page load
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('code-input-area');
    textarea.value = window.codeSubmission;
});

// Allows for "tab" inputs in code area
document.addEventListener('DOMContentLoaded', () => {
    const textarea = document.getElementById('code-input-area');
    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                e.preventDefault();

                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;

                // Insert tab character at cursor position
                textarea.value = textarea.value.substring(0, start) + "\t" + textarea.value.substring(end);

                // Move cursor to after the tab
                textarea.selectionStart = textarea.selectionEnd = start + 1;
            }
        });
    }
});

// Saves code submission to server
async function saveCode(id) {
    const textarea = document.getElementById("code-input-area");
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch(`/${id}/save/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : textarea.value})
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
    const textarea = document.getElementById("code-input-area")
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
            body: JSON.stringify ({"submission" : textarea.value, "compiler_output" : compiler_output})
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
    const textarea = document.getElementById("code-input-area")
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch("/compile/", {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : textarea.value})
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
    const textarea = document.getElementById("code-input-area")
    const csrftoken = getCookie("csrftoken"); // Get CSRF token from cookie

    try {
        const response = await fetch(`/${id}/submit-code/`, {
            method: "POST",
            headers: {
                "Content-Type" : "application/json",
                "X-CSRFToken" : csrftoken
            },
            body: JSON.stringify ({"submission" : textarea.value})
        })

        if (!response.ok) {
            throw new Error(`Response status: ${response.status}`);
        }

        const returned_json = await response.json();
        const status = returned_json.status;
        window.alert(status);

    } catch (error) {
        console.error(error.message);
    }
}

document.addEventListener("DOMContentLoaded", function () {
    const test_button = document.getElementById("test");
    const textarea = document.getElementById('code-input-area');
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
    submit_button.addEventListener("click", function () {
        window.alert("button clicked");
        submitCode(window.sessionID);
    })
})
