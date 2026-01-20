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

  conversationArea = document.getElementById("conversationArea")
  conversationArea.appendChild(newArea);

  conversationArea.scrollTop = conversationArea.scrollHeight;
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


function updateChat(id, chat) { // Update chatlog in database
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

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("response_button");
    const textarea = document.getElementById("response");

    // Trigger update() on button click
    button.addEventListener("click", () => {
        update(sessionID); // THIS IS RAISING AN ERROR
    });

    // Trigger update() when user presses Enter inside textarea
    textarea.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault(); // Prevent newline
            update(sessionID);
        }
    });
});

window.addEventListener('load', function () {
    window.scrollTo(0, document.body.scrollHeight);
});