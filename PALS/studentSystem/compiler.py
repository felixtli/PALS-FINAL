import subprocess, tempfile, textwrap, os, sys, re, pprint
from .models import Profile, Question, QuestionAttempt, Session
import json
from typing import Any


def clean_sml_output(output: str) -> str:
    """
    Cleans SML/NJ compiler output to only include:
    - The error message (if present)
    - Or, the printed stdout from the executed program
    
    Args:
        output (str): Raw output string from SML/NJ
    
    Returns:
        str: Cleaned output
    """
    # Remove the leading prompt dashes from each line
    output = re.sub(r"^\s*-\s*", "", output, flags=re.MULTILINE)

    # Case 1: Error present
    error_match = re.search(r"(stdIn:\d+\.\d+\s+Error:.*)", output, re.DOTALL)
    if error_match:
        return error_match.group(1).strip()
    
    # Case 2: Regular program output
    # Remove compiler intro line
    cleaned = re.sub(r"^Standard ML of New Jersey.*?\]", "", output, flags=re.DOTALL)
    
    # Remove autoloading/library noise
    cleaned = re.sub(r"\[autoloading.*?\]", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[library.*?\]", "", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"\[autoloading done\]", "", cleaned, flags=re.DOTALL)
    
    # Remove val bindings and type info
    cleaned = re.sub(r"val\s+\w+\s*=\s*fn\s*:\s*.*", "", cleaned)
    cleaned = re.sub(r"val\s+\w+\s*=\s*.*:\s*.*", "", cleaned)
    
    # Strip whitespace and return
    return cleaned.strip()

def compileCode(codeInput):
    codeInput = textwrap.dedent(codeInput)
    feed = codeInput
    compilerRaw = subprocess.run(
        ["sml"],
        input = feed,
        text  = True,
        capture_output = True,
        check = True,
        shell=True,                     
    )

    return (clean_sml_output(compilerRaw.stdout))

def smlEscapeString(s: str) -> str:
    # Escape backslashes and double quotes; make newlines visible
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", "\\n").replace("\t", "\\t").replace("\r", "\\r")
    return s

# TODO: Add support for dictionary conversion
def cleanCases(value: Any) -> str:
    """
    Convert a Python value into an SML literal.
    Supports: int, bool, str, tuple, list, nested combinations of these.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return f"\"{smlEscapeString(value)}\""
    if isinstance(value, tuple):
        items = ", ".join(cleanCases(v) for v in value)
        return f"({items})"
    if isinstance(value, list):
        items = ", ".join(cleanCases(v) for v in value)
        return f"[{items}]"
    # If you need reals/chars/options/etc., add cases here.
    raise TypeError(f"Unsupported value type for SML serialization: {type(value).__name__}")


def runTestCases(codeInput, inputCases, expectedOutputs, targetFunction, inputType, pre_serialized=False):
    with open("temp.sml", "w") as tempFile:
        tempFile.write(codeInput)

    if inputType == 1:

        if pre_serialized and isinstance(inputCases, str):
            sml_input = inputCases                          # Handles Two-Fer special case
        else:
            sml_input = cleanCases(inputCases)  

        sml_output = cleanCases(expectedOutputs)
        print ("SML Input:", sml_input)
        print ("SML Output:", sml_output)

        # This harness is able to do single argument function calls evaluated against single value test cases
        sml_test_code = f""" 
        use "{tempFile.name}";

        val outStream = TextIO.openOut "results.txt";

        val inputCases = {sml_input}
        val expectedOutputs = {sml_output}
        val targetFunction = {targetFunction}

        fun runTest (targetFunction, inputs, output) =
        let
            val result = targetFunction inputs
        in
            if result = output then
                TextIO.output (outStream, "PASS\\n")
            else
                TextIO.output (outStream, "FAIL\\n")
        end

        val _ = ListPair.app (fn (inp, out) => runTest (targetFunction, inp, out))
                     (inputCases, expectedOutputs)

        """
    print (sml_test_code)

    compilerRaw = subprocess.run(
        ["sml"],
        input = sml_test_code,
        text  = True,
        capture_output = True,
        check = True,
        shell=True,                     
    )

    result = compilerRaw.stdout
    print ("Compiler Output:\n", result)

    passCount = 0
    with open("results.txt", "r") as resultsFile:
        for line in resultsFile:
            if line.strip() == "PASS":
                passCount += 1
    
    print (f"{passCount} out of {len(expectedOutputs)} test cases passed.")
    return passCount

def stringToOption(py_s: str) -> str:
    # NONE if blank or whitespace-only, otherwise SOME "..."
    if py_s.strip() == "":
        return "NONE"
    return f'SOME "{smlEscapeString(py_s)}"'

def handler(profile: Profile, questionAttempt: QuestionAttempt, session: Session):
    question = questionAttempt.question
    testCases = question.test_cases

    inputCases = [item["input"] for item in testCases]
    for c in range(len(inputCases)): # This loop is necessary to convert lists -> tuples for SML compatibility.
        if type(inputCases[c]) == list:
            case = tuple(inputCases[c])
            inputCases[c] = case
    print (inputCases)

    if question.question_title == "Two-Fer":
        option_inputs = [stringToOption(s) for s in inputCases]
        inputCases = "[" + ", ".join(option_inputs) + "]"
        expectedOutputs = [item["output"] for item in testCases]

        passedCases = runTestCases(session.codeSubmission, inputCases, expectedOutputs, question.target_function, 1, pre_serialized=True)

        questionAttempt.solved_test_cases = passedCases
        questionAttempt.save()
        return passedCases

    expectedOutputs = [item["output"] for item in testCases]

    print(session.codeSubmission)
    print(question.question_title)
    print (str(testCases) + "data type: " + str(type(testCases)))

    runTestCases(session.codeSubmission, inputCases, expectedOutputs, question.target_function, 1)



