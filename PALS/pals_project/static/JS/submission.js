const userInput = document.getElementById('response');
const elements = document.getElementsByClassName('submittedCode');

function submitCode() {
  const submissionCount = elements.length;

  if (submissionCount < 1) {

    // Creates User Response Text Bubble 
    // Create div
    const newArea = document.createElement("div");
    newArea.setAttribute("class", "submittedCode");

    // Creates p element
    const newText = document.createElement("p");
    newText.setAttribute("class", "codeContent");
    newArea.appendChild(newText);

    // Creates text value to attach to p element
    newText.innerHTML = userInput.value;

    document.getElementById("conversationArea").appendChild(newArea);
  }
  else {
    window.alert("here 2!");
    document.getElementsByClassName("submittedCode")[0].innerHTML = userInput.value;
  }
}

document.getElementById('response').addEventListener('keydown', function(e) {
  if (e.key == 'Tab') {
    e.preventDefault();
    var start = this.selectionStart;
    var end = this.selectionEnd;

    // set textarea value to: text before caret + tab + text after caret
    this.value = this.value.substring(0, start) +
      "\t" + this.value.substring(end);

    // put caret at right position again
    this.selectionStart =
      this.selectionEnd = start + 1;
  }
});

function customAlert() {
  window.alert(userInput.value);
}


