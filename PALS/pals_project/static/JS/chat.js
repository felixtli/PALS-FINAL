const userInput = document.getElementById('response');
userInput.addEventListener("input", autoResize);

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
    idle = false;
    lastTick = Date.now();
    if (idleTimer) clearTimeout(idleTimer);
    idleTimer = setTimeout(() => { idle = true; tick(); }, IDLE_MS);
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

function send(durationMs, endedAtMs, heartbeat=false) {
    const payload = {
        duration_ms: Math.max(0, Math.round(durationMs)),
        started_at_ms: startedAt,
        ended_at_ms: endedAtMs,
        path: location.pathname + location.search + location.hash,
        referrer: document.referrer || "",
        visible_only: true,
        idle_threshold_ms: IDLE_MS,
        heartbeat: heartbeat
    };
    const blob = new Blob([JSON.stringify(payload)], {type:"application/json"});
    navigator.sendBeacon(endpoint, blob);
}

// Optional: heartbeat in case the tab crashes or the user closes the laptop.
const HEARTBEAT_MS = 120000; // 2 minutes
const hb = setInterval(() => { tick(); send(visibleAccum, Date.now(), true); }, HEARTBEAT_MS);

// On unload/navigation
window.addEventListener("pagehide", () => {
    tick();
    clearInterval(hb);
    send(visibleAccum, Date.now(), false);
});
// Analytics tracking code ends here

function getAIChat(id, prompt) {
  csrftoken = getCookie("csrftoken");

  fetch(`/${id}/chat/next-response/`, {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
          "X-CSRFToken": csrftoken
      },
      body: JSON.stringify({
          prompt: prompt
      })
    })
    .then(response => response.json())
    .then(data => {
        createNewChat("ai", data.message)
        setTimeout(function() { updateChat(id, data.message); }, 2500)
    })
    .catch(error => {
        window.alert("Error generating new chat.");
  });
}

// Function to create new chat entries
function createNewChat(type, text) {
  if (type === "user")
  {
    newAreaAttribute = "pastResponseArea";
    newTextAttribute = "pastResponse";
  }
  else if (type === "ai")
  {
    newAreaAttribute = "teacherArea";
    newTextAttribute = "teacher";
  }

  const newArea = document.createElement("div");
  newArea.setAttribute("class", newAreaAttribute);
  const newText = document.createElement("p");
  newText.setAttribute("class", newTextAttribute);
  newArea.appendChild(newText);
  const textNode = document.createTextNode(text);
  newText.appendChild(textNode);
  document.getElementById("conversationArea").appendChild(newArea);
}

function loadChat(chatLog) {
  for (let i = 0; i < chatLog.length; i++){
    if (i % 2 == 0)
    {
      createNewChat("user", chatLog[i])
    }
    else
    {
      createNewChat("ai", chatLog[i])
    }
  }
}


function autoResize() { /* Automatically adjusts height of text input field based on the amount of text */
  this.style.height = '30px';
  this.style.height = this.scrollHeight + 'px';
}


function updateChat(id, chat) {
  csrftoken = getCookie("csrftoken");

  fetch(`/${id}/chat/add-chat/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken, // needed when using CSRF protection
    },
    body: JSON.stringify({
        chat: chat
    })
  })
  .then(response => response.json())
  .then(data => {
      if (data.status !== 'success') {
          alert('Error adding chat: ' + data.message);
      }
      else {
        // alert ("Success adding chat!");
      }
  })
  .catch(error => {
      console.error('Error:', error);
  });
}

function update(id) {
  // Creates User Response Text Bubble and updates chatlog
  createNewChat("user", userInput.value)
  updateChat(id, userInput.value)

  // Creates new AI text bubble and updates chatlog
  getAIChat(id, userInput.value)
  document.getElementById("response").style.height = '34px';

  userInput.value = ""; // Resets user input textbox 
}

window.onload = function() {
  window.scrollTo(0, document.body.scrollHeight); // Scroll to bottom of chat on load
}