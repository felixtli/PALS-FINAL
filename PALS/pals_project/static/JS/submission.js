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

async function submitCode()
{
    const textarea = document.getElementById("code-input-area")
    const compilerArea = document.getElementById("compiler-output");
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

        newOutput.innerHTML = formatted_date + compiled_output;

        document.querySelector(".compiler-container").appendChild(newOutput);
        
    } catch (error) {
        console.error(error.message);
    }
    
}

document.addEventListener("DOMContentLoaded", function () {
    const submit_button = document.getElementById("submit");
    const textarea = document.getElementById('code-input-area');
    submit_button.addEventListener("click", function () {
        submitCode();
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