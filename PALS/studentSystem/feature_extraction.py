import re

def detectSMLFeatures(code):
    features = []

    # Detect conditional statements
    if re.search(r"\bif\s+\w+\s*=\s*\w+\s*then", code):
        features.append('Conditional Statement')

    # Detect function definitions
    if re.search(r"\bfun\s+\w+\s+\w+(\s*:\s*\w+)?\s*=", code):
        features.append('Function Definition')

    # Detect comparison operators
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped.startswith("fun"):
            if re.search(r"\b(=|<>|<=|>=|<|>)\b", stripped):
                features.append('Comparison Operator')
                break  # Avoid duplicates

    # Detect string concatenation (e.g., ... ^ ...)
    if re.search(r"\s*\^\s*", code):
        features.append('String Concatenation')

    return features

code = ""