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
    print ("CODE HAS BEEN CLEANED")
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
    """
    Escape a Python string for safe inclusion as an SML string literal.
    Handles quotes, backslashes, and common control characters.
    """
    escape_map = {
        "\\": "\\\\",
        "\"": "\\\"",
        "\n": "\\n",
        "\t": "\\t",
        "\r": "\\r",
    }
    return "".join(escape_map.get(c, c) for c in s)

def to_sml_literal(value: Any) -> str:
    """
    Convert a Python value into an SML literal string.
    Supports: int, float, bool, str, char (single-character strings),
    tuple, list, dict (record), None (NONE), and nested combinations of these.
    """

    # Define known SML constructors
    # Allergen Case
    ALLERGENS = {
        "Eggs", "Peanuts", "Shellfish", "Strawberries",
        "Tomatoes", "Chocolate", "Pollen", "Cats"
    }

    LISTS = {
        "Equal", "Sublist", "Superlist", "Unequal"
    }

    # Booleans → true/false
    if isinstance(value, bool):
        return "true" if value else "false"

    # Integers → convert negatives with ~
    if isinstance(value, int):
        return f"~{abs(value)}" if value < 0 else str(value)

    # Floats → use SML real literal format (with decimal point)
    if isinstance(value, float):
        # SML reals must have at least one digit before and after the dot
        return f"~{abs(value)}" if value < 0 else f"{value}" if "." in str(value) else f"{value}.0"

    # Strings -> Use escape string function
    if isinstance(value, str):
        if value in ALLERGENS:
            # Emits the constructor directly without quotes
            return value
        if value in LISTS:
            return value
        if len(value) == 1 and not value.isdigit():
            return f"#\"{smlEscapeString(value)}\""  # Char literal
        return f"\"{smlEscapeString(value)}\""

    # Tuples → (x, y, z)
    if isinstance(value, tuple):
        items = ", ".join(to_sml_literal(v) for v in value)
        return f"({items})"

    # Lists → [x, y, z]
    if isinstance(value, list):
        items = ", ".join(to_sml_literal(v) for v in value)
        return f"[{items}]"

    # None → SML option NONE
    if value is None:
        return "NONE"

    # Options: dict with exactly {"SOME": ...}
    if isinstance(value, dict) and set(value.keys()) == {"SOME"}:
        return f"SOME ({to_sml_literal(value['SOME'])})"
    
    # Arrays: dict with exactly {"ARRAY": [...]}
    if isinstance(value, dict) and set(value.keys()) == {"ARRAY"}:
         inner = to_sml_literal(value["ARRAY"])  # will return [x, y, z]
         return f"Array.fromList {inner}"

    # Generic dict → SML record
    if isinstance(value, dict):
        items = ", ".join(f"{k} = {to_sml_literal(value[k])}" for k in sorted(value.keys()))
        return f"{{{items}}}"
    
    raise TypeError(f"Unsupported value type for SML serialization: {type(value).__name__}")

def forceReal(value):
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, list):
        return [forceReal(v) for v in value]   
    if isinstance(value, tuple):
        return tuple(forceReal(v) for v in value)
    raise TypeError(f"Unsupported type for forceReal: {type(value).__name__}")

def runTestCases(codeInput, inputCases, expectedOutputs, targetFunction, returnType):
    with open("temp.sml", "w") as tempFile:
        tempFile.write(codeInput)

    sml_input = to_sml_literal(inputCases)
    sml_output = to_sml_literal(expectedOutputs)

    testHarness = f""" 
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

    if returnType == "real":
        inputCases = forceReal(inputCases)
        expectedOutputs = forceReal(expectedOutputs)

        sml_input = to_sml_literal(inputCases)
        sml_output = to_sml_literal(expectedOutputs)

        testHarness = f"""
        use "{tempFile.name}";

        val outStream = TextIO.openOut "results.txt";

        val inputCases = {sml_input}
        val expectedOutputs = {sml_output}
        val targetFunction = {targetFunction}

        fun approxEq (a: real, b: real) = Real.abs (a - b) < 1.0E~9

        fun runTest (targetFunction, inputs, output) =
        let
            val result =
                targetFunction inputs
        in
            if approxEq (result, output) then
            TextIO.output (outStream, "PASS\\n")
            else
            TextIO.output (outStream, "FAIL\\n")
        end
        
        val _ = ListPair.app (fn (inp, out) => runTest (targetFunction, inp, out))
                    (inputCases, expectedOutputs)
        """
    print ("TEST HARNESS:" + str(testHarness))

    compilerRaw = subprocess.run(
        ["sml"],
        input = testHarness,
        text  = True,
        capture_output = True,
        check = True,
        shell=True,                     
    )

    result = compilerRaw.stdout
    print ("COMPILER RESULT: " + str(result))

    passCount = 0
    with open("results.txt", "r") as resultsFile:
        for line in resultsFile:
            if line.strip() == "PASS":
                passCount += 1
    
    return passCount

def stringToOption(py_s: str) -> str:
    # NONE if blank or whitespace-only, otherwise SOME "..."
    if py_s.strip() == "":
        return "NONE"
    return f'SOME "{smlEscapeString(py_s)}"'

def handler(profile: Profile, session: Session):

    with open("results.txt", 'w') as file: # Clear results file containing pass/fail information on each run
        pass

    question = session.question
    testCases = question.test_cases
    questionAttempt = session.attempts.first()

    inputCases = [item["input"] for item in testCases]

    for c in range(len(inputCases)): # This loop is necessary to convert lists -> tuples for SML compatibility.
        if type(inputCases[c]) == list:
            case = tuple(inputCases[c])
            inputCases[c] = case

    expectedOutputs = [item["output"] for item in testCases]

    for o in range(len(expectedOutputs)): # This loop is necessary to convert lists -> tuples for SML compatibility.
        if type(expectedOutputs[o]) == list:
            case = tuple(expectedOutputs[o])
            expectedOutputs[o] = case

    returnType = "default"
    realReturnTypes = ["Distance Between Two Points", "Temperature Converter"]
    if question.question_title in realReturnTypes:
        returnType = "real"

    casesSolved = runTestCases(session.codeSubmission, inputCases, expectedOutputs, question.target_function, returnType)
    questionAttempt.solved_test_cases = casesSolved
    questionAttempt.save()

    return casesSolved




