const userInput = document.getElementById('response');
userInput.addEventListener("input", autoResize);

function getResponse() {

  // Creates User Response Text Bubble 
  const newArea = document.createElement("div");
  newArea.setAttribute("class", "pastResponseArea");
  const newText = document.createElement("p");
  newText.setAttribute("class", "pastResponse");
  newArea.appendChild(newText);
  const textNode = document.createTextNode(userInput.value);
  newText.appendChild(textNode);
  document.getElementById("conversationArea").appendChild(newArea);

  // Creates new teacher text bubble
  const newTeacherArea = document.createElement("div");
  newTeacherArea.setAttribute("class", "teacherArea");
  const newTeacherText = document.createElement("p");
  newTeacherText.setAttribute("class", "teacher");
  newTeacherArea.appendChild(newTeacherText);
  const newTeacherTextNode = "Sample text";
  newTeacherText.append(newTeacherTextNode);
  document.getElementById("conversationArea").appendChild(newTeacherArea);

  document.getElementById("response").style.height = '34px';
  
  userInput.value = ""; // Resets user input textbox 
}


function autoResize() { /* Automatically adjusts height of text input field based on the amount of text */
  this.style.height = '30px';
  this.style.height = this.scrollHeight + 'px';
}


function customAlert() {
  window.alert(userInput.value);
}


/* Gets feedback from hidden feedback element on page and sends it to designated feedback page */
function getFeedback() {
  feedbackText = document.getElementById("feedbackHolder").innerHTML;
  
  let url = `interview/feedback/?feedbackText=${encodeURIComponent(feedbackText)}`;
  window.location.href = url;  

}
