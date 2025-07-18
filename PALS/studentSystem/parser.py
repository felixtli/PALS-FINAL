import re
import pandas as pd
import ast
from typing import List

# Token types
KEYWORDS = {
    "val", "fun", "if", "then", "else", "let", "in", "end",
    "case", "of", "raise", "fn", "andalso", "orelse", "not",
    "local", "structure", "signature", "functor", "ref", "while"
}

OPERATORS = {
    "+", "-", "*", "/", "^", "=", "<>", "<", ">", "<=", ">=", ":=", "::", "=>", "|"
}

SYMBOLS = {
    "(", ")", "[", "]", "{", "}", ",", ".", ";"
}


class Token:
    def __init__(self, type_: str, value: str):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"{self.type}({self.value})"


def tokenize(code: str) -> List[Token]:
    tokens = []
    current = ""
    i = 0
    while i < len(code):
        c = code[i]

        if c.isspace():
            if current:
                tokens.append(classify_token(current))
                current = ""
            i += 1
            continue

        # Multi-character operators
        if code[i:i+2] in OPERATORS:
            if current:
                tokens.append(classify_token(current))
                current = ""
            tokens.append(Token("OPERATOR", code[i:i+2]))
            i += 2
            continue

        # Single-character operators/symbols
        if c in OPERATORS or c in SYMBOLS:
            if current:
                tokens.append(classify_token(current))
                current = ""
            token_type = "OPERATOR" if c in OPERATORS else "SYMBOL"
            tokens.append(Token(token_type, c))
            i += 1
            continue

        current += c
        i += 1

    if current:
        tokens.append(classify_token(current))

    return tokens


def classify_token(token_str: str) -> Token:
    if token_str in KEYWORDS:
        return Token("KEYWORD", token_str)
    elif token_str.isdigit():
        return Token("INT", token_str)
    elif token_str.startswith('"') and token_str.endswith('"'):
        return Token("STRING", token_str)
    else:
        return Token("IDENTIFIER", token_str)


def detect_features(tokens: List[Token]) -> List[str]:
    features = set()
    i = 0
    recent_context = None
    in_let_block = False
    in_fun_block = False
    if_depth = 0
    last_fun_name = None
    fun_names = set()
    recursive_calls = {}
    while_seen = False
    ref_seen = False

    while i < len(tokens):
        token = tokens[i]

        # --- KEYWORDS ---
        if token.type == "KEYWORD":
            recent_context = token.value

            match token.value:
                case "val":
                    features.add("Variable Assignment")
                    if i + 2 < len(tokens) and tokens[i + 2].type in {"INT", "STRING"}:
                        features.add("Constant Expression")

                case "fun":
                    features.add("Function Definition")
                    in_fun_block = True

                    if (
                        i + 3 < len(tokens)
                        and tokens[i + 1].type == "IDENTIFIER"
                        and tokens[i + 2].type == "IDENTIFIER"
                        and tokens[i + 3].type == "IDENTIFIER"
                    ):
                        features.add("Curried Function")

                    fname = tokens[i + 1].value if i + 1 < len(tokens) else None
                    last_fun_name = fname
                    fun_names.add(fname)
                    recursive_calls[fname] = 0

                case "if":
                    features.add("Conditional Statement")
                    if if_depth >= 1:
                        features.add("Nested Conditional Statement")
                    if_depth += 1

                case "then" | "else":
                    if token.value == "else":
                        if_depth = max(0, if_depth - 1)

                case "let":
                    features.add("Let Binding")
                    in_let_block = True

                case "local":
                    features.add("Local Binding")

                case "end":
                    in_let_block = False
                    in_fun_block = False
                    if_depth = 0

                case "case":
                    features.add("Pattern Matching")

                case "raise":
                    features.add("Exception Raising")

                case "fn":
                    features.add("Lambda Function")

                case "while":
                    features.add("Use Of While Loops")
                    while_seen = True

                case "ref":
                    features.add("Use Of Refs")
                    ref_seen = True

                case "structure" | "signature" | "functor":
                    features.add("Custom Module Usage")
                
                case "datatype":
                    features.add("Datatype Definition")

                case "infix" | "infixr" | "nonfix":
                    features.add("Custom Infix Operator")


        # --- OPERATORS ---
        elif token.type == "OPERATOR":
            match token.value:
                case "+" | "-" | "*" | "/" | "mod" | "div":
                    features.add("Arithmetic Operation")

                case "^":
                    features.add("String Concatenation")

                case "=":
                    is_potential_comparison = False
                    if i > 0 and i + 1 < len(tokens):
                        left = tokens[i - 1]
                        right = tokens[i + 1]

                        # Check for real number equality
                        if (
                            left.type == "INT" and "." in left.value
                            or right.type == "INT" and "." in right.value
                        ):
                            features.add("Real Number Equality")

                        if left.type in {"IDENTIFIER", "INT"} and right.type in {"IDENTIFIER", "INT"}:
                            is_potential_comparison = True

                    if is_potential_comparison:
                        features.add("Comparison Operator")

                case "<>", "<", ">", "<=", ">=":
                    features.add("Comparison Operator")

                case "andalso" | "orelse" | "not":
                    features.add("Logical Operator")

                case "|":
                    if recent_context in {"fun", "case"}:
                        features.add("Pattern Matching")

        # --- IDENTIFIERS ---
        elif token.type == "IDENTIFIER":
            # Check for polymorphic
            if (
                token.value == "="
                and i >= 2
                and tokens[i - 2].type == "IDENTIFIER"
                and tokens[i - 1].type == "IDENTIFIER"
                and i + 1 < len(tokens)
                and tokens[i + 1].type == "IDENTIFIER"
                and tokens[i - 1].value == tokens[i + 1].value
            ):
                features.add("Polymorphic Functions")

            if token.value == "option":
                features.add("Option Type")
            elif token.value in {"SOME", "NONE"}:
                features.add("Option Type")
            elif token.value == "_":
                is_pattern_match = (
                    i > 0 and tokens[i - 1].type == "OPERATOR" and tokens[i - 1].value == "|"
                    and i + 1 < len(tokens) and tokens[i + 1].type == "OPERATOR" and tokens[i + 1].value == "=>"
                )
                if not is_pattern_match:
                    features.add("Anonymous Variable")

            elif token.value in {"List", "String", "Math", "Char", "Word"}:
                if i + 1 < len(tokens) and tokens[i + 1].value == ".":
                    features.add("Basis Library Module Usage")

            elif token.value == "TextIO":
                if i + 2 < len(tokens):
                    method = tokens[i + 2].value
                    if method.startswith("openIn") or method.startswith("input"):
                        features.add("Reading Input From A File")
                    if method.startswith("openOut") or method.startswith("output"):
                        features.add("Writing Output To A File")

            # Track recursive calls
            if token.value in fun_names:
                recursive_calls[token.value] += 1

                # Backward: check if we're in a return-like context
                k = i - 1
                while k >= 0:
                    prev = tokens[k]
                    if prev.value in {"=", "=>", "then", "in"}:
                        break  # Possible tail call position
                    if prev.value in {"val", "fun", "datatype", "structure"}:
                        break  # Decl context, not tail
                    if prev.value in {"|", ";"}:
                        break
                    k -= 1
                else:
                    k = -1

                # Forward: check for disqualifiers like being used in an op
                j = i + 1
                is_disqualified = False
                paren_depth = 0
                while j < len(tokens):
                    tok = tokens[j]
                    if tok.value in {")", "]", "end", ";"}:
                        break
                    if tok.value == "(":
                        paren_depth += 1
                    if tok.value == ")":
                        paren_depth -= 1
                    if tok.value in {"+", "-", "*", "/", "@", "::", "orelse", "andalso", "=", "!="}:
                        is_disqualified = True
                        break
                    if tok.value in {"val", "fun", "let", "handle", "case"}:
                        is_disqualified = True
                        break
                    j += 1

                if not is_disqualified and k >= 0:
                    features.add("Tail Recursion")
                else:
                    if not (
                        i > 0 and tokens[i - 1].value == "fun"
                        or i > 1 and tokens[i - 2].value == "val"
                    ):
                        features.add("Non Tail Recursion Inefficiency")

            # External module usage (non-BasisLibrary)
            if token.value not in {"List", "String", "Math", "Char", "Word", "TextIO"}:
                if i + 1 < len(tokens) and tokens[i + 1].value == ".":
                    features.add("External Module Usage")

        # Detect mod/div as arithmetic ops
        if token.type in {"KEYWORD", "IDENTIFIER"} and token.value in {"mod", "div"}:
            if i > 0 and i + 1 < len(tokens):
                left = tokens[i - 1]
                right = tokens[i + 1]
                if left.type in {"IDENTIFIER", "INT"} and right.type in {"IDENTIFIER", "INT"}:
                    features.add("Arithmetic Operation")

        # Polymorphic Function
        if (
            token.value == "="
            and i >= 2
            and tokens[i - 2].type == "IDENTIFIER"
            and tokens[i - 1].type == "IDENTIFIER"
            and i + 1 < len(tokens)
            and tokens[i + 1].type == "IDENTIFIER"
            and tokens[i - 1].value == tokens[i + 1].value
        ):
            features.add("Polymorphic Function")

        # Local recursive
        if token.type == "KEYWORD" and token.value == "fun":
            if in_let_block or recent_context == "local":
                features.add("Local Function Definition")
                features.add("Local Recursive Function")

        i += 1

    # Multiple recursive functions
    mutuals = [f for f, c in recursive_calls.items() if c > 1]
    if len(mutuals) >= 2:
        features.add("Multiple Recursive Functions")

    # Redundancy heuristic: repeated `if ... else if ... else if ... else` with unreachable last branch
    code_str = " ".join(t.value for t in tokens)
    if "if" in code_str and "else if" in code_str and "else if" in code_str and "else" in code_str:
        features.add("Redundancy")

    return sorted(features)


def test_parser(code, index):
    tokens = tokenize(code)
    features = detect_features(tokens)
    return {"code_segment": code, "index": index, "features": features}

# Example usage
if __name__ == "__main__":
    import pandas as pd
    from sklearn.metrics import precision_score, recall_score, f1_score
    from collections import Counter

    dataset = pd.read_csv("standardml_dataset.csv")

    all_results = []
    TP, FP, FN = 0, 0, 0

    def evaluate_prediction(predicted, actual):
        predicted_set = set(predicted)
        actual_set = set([f.strip() for f in actual.split(",") if f.strip()])

        tp = len(predicted_set & actual_set)
        fp = len(predicted_set - actual_set)
        fn = len(actual_set - predicted_set)

        return {
            "TP": tp,
            "FP": fp,
            "FN": fn,
            "Correct": sorted(predicted_set & actual_set),
            "Missed": sorted(actual_set - predicted_set),
            "Incorrect": sorted(predicted_set - actual_set)
        }

    #  Save a snapshot of the previous evaluation.
    import shutil
    shutil.copy("parser_evaluation_output.txt", "snapshot.txt")

    # Write results to file.
    with open("parser_evaluation_output.txt", "w", encoding="utf-8") as f:
        for index, row in dataset.iterrows():
            code = row['Code']
            gold_features = row['Features']
            result = test_parser(code, index)

            evaluation = evaluate_prediction(result["features"], gold_features)
            TP += evaluation["TP"]
            FP += evaluation["FP"]
            FN += evaluation["FN"]

            f.write("=" * 60 + "\n")
            f.write(f"[#{index + 1}] Code:\n{code}\n")
            f.write(f"- Ground Truth: {gold_features}\n")
            f.write(f"- Predicted:    {', '.join(result['features'])}\n")
            f.write(f"- ✅ Correct:    {', '.join(evaluation['Correct'])}\n")
            f.write(f"- ❌ Missed:     {', '.join(evaluation['Missed'])}\n")
            f.write(f"- 🚫 Incorrect:  {', '.join(evaluation['Incorrect'])}\n")
            f.write("=" * 60 + "\n\n")

            all_results.append({
                "Index": index + 1,
                "Code": code,
                "Ground Truth": gold_features,
                "Predicted": ", ".join(result["features"]),
                "Correct": ", ".join(evaluation["Correct"]),
                "Missed": ", ".join(evaluation["Missed"]),
                "Incorrect": ", ".join(evaluation["Incorrect"])
            })

        # Summary Metrics
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        f.write("\n" + "#" * 40 + "\n")
        f.write("📊 Overall Evaluation Metrics\n")
        f.write(f"- True Positives:  {TP}\n")
        f.write(f"- False Positives: {FP}\n")
        f.write(f"- False Negatives: {FN}\n")
        f.write(f"- Precision:       {precision:.2f}\n")
        f.write(f"- Recall:          {recall:.2f}\n")
        f.write(f"- F1 Score:        {f1:.2f}\n")
        f.write("#" * 40 + "\n")


    
