import subprocess, tempfile, textwrap, os, sys, re

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
    compiler_raw = subprocess.run(
        ["sml"],
        input = feed,
        text  = True,
        capture_output = True,
        check = True,
        shell=True,                     
    )

    return (clean_sml_output(compiler_raw.stdout))

