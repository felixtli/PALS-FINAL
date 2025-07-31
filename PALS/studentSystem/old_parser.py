# THIS IS AN OLD PARSER THAT ONLY USES HEURISTICS AND REGEX TO DETECT FEATURES

import re
from typing import List

# Token types
KEYWORDS = {
    "val", "fun", "and", "if", "then", "else", "let", "in", "end",
    "case", "of", "raise", "fn", "andalso", "orelse", "not",
    "local", "structure", "signature", "functor", "ref", "while", "datatype",
    "use"
}

OPERATORS = {
    "+", "-", "*", "/", "^", "=", "<>", "<", ">", "<=", ">=", ":=",
    "::", "@", "=>", "|", "~"
}

SYMBOLS = {
    "(", ")", "[", "]", "{", "}", ",", ".", ";"
}

# Basis library modules
BASIS_MODULES = {"List", "String", "Math", "Char", "Word", "Option", "IntInf", "IntArray"}
# Free-standing basis functions
FREE_BASIS_FUNCS = {"foldl", "foldr", "map", "filter", "explode", "implode"}

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
        # multi-character operators
        if code[i:i+2] in OPERATORS:
            if current:
                tokens.append(classify_token(current)); current = ""
            tokens.append(Token("OPERATOR", code[i:i+2])); i += 2; continue
        # single-character operators/symbols
        if c in OPERATORS or c in SYMBOLS:
            if current:
                tokens.append(classify_token(current)); current = ""
            tok_type = "OPERATOR" if c in OPERATORS else "SYMBOL"
            tokens.append(Token(tok_type, c)); i += 1; continue
        current += c; i += 1
    if current:
        tokens.append(classify_token(current))
    return tokens


def classify_token(s: str) -> Token:
    if s in KEYWORDS:
        return Token("KEYWORD", s)
    elif s.isdigit():
        return Token("INT", s)
    elif s.startswith('"') and s.endswith('"'):
        return Token("STRING", s)
    else:
        return Token("IDENTIFIER", s)


def detect_features(tokens: List[Token]) -> List[str]:
    features = set()
    fun_names = set()
    fun_def_positions = {}
    rec_calls = {}
    skip_next_eq = False
    in_let = False
    in_local = False
    pattern_context = 0
    recent_keyword = None

    for i, token in enumerate(tokens):
        # Keyword-based features
        if token.type == "KEYWORD":
            recent_keyword = token.value
            if token.value == "fun":
                features.add("Function Definition")
                if in_let or in_local:
                    features.add("Local Function Definition")
                # record function name
                if i+1 < len(tokens) and tokens[i+1].type == "IDENTIFIER":
                    fname = tokens[i+1].value
                    fun_names.add(fname)
                    rec_calls[fname] = {'tail': 0, 'non_tail': 0}
                    fun_def_positions[fname] = i+1
                # curried detection: count successive identifiers
                j = i+2; count = 0
                while j < len(tokens) and tokens[j].type == "IDENTIFIER":
                    count += 1; j += 1
                if count >= 2:
                    features.add("Curried Function")
                pattern_context += 1
                skip_next_eq = True

            elif token.value == "val":
                features.add("Variable Assignment")
                skip_next_eq = True

            elif token.value == "datatype":
                features.add("Datatype Definition")
                skip_next_eq = True

            elif token.value == "and":
                # multiple recursive functions only when linking fun clauses
                nxt = tokens[i+1].value if i+1 < len(tokens) else None
                if recent_keyword == "fun" or nxt == "fun":
                    features.add("Multiple Recursive Functions")

            elif token.value == "if":
                features.add("Conditional Statement")

            elif token.value == "let":
                features.add("Let Binding")
                in_let = True
                pattern_context += 1

            elif token.value == "local":
                features.add("Local Binding")
                in_local = True
                pattern_context += 1

            elif token.value == "end":
                in_let = False; in_local = False
                if pattern_context > 0:
                    pattern_context -= 1

            elif token.value == "case":
                features.add("Pattern Matching")
                pattern_context += 1

            elif token.value == "raise":
                features.add("Exception Raising")

            elif token.value == "fn":
                features.add("Lambda Function")

            elif token.value in {"andalso", "orelse", "not"}:
                features.add("Logical Operator")

            elif token.value == "while":
                features.add("Use Of While Loops")

            elif token.value == "ref":
                features.add("Use Of Refs")

            elif token.value in {"structure", "signature", "functor"}:
                features.add("Custom Module Usage")

            elif token.value in {"infix", "infixr", "nonfix"}:
                features.add("Custom Infix Operator")

            elif token.value == "use":
                features.add("Use Directive")

        # Operator-based features
        if token.type == "OPERATOR":
            if token.value in {"+", "-", "*", "/", "mod", "div", "~"}:
                features.add("Arithmetic Operation")
            elif token.value == "^":
                features.add("String Concatenation")
            elif token.value in {"::", "@"}:
                features.add("Basis Library Module Usage")
            elif token.value in {"<>", "<", ">", "<=", ">="}:
                features.add("Comparison Operator")
            elif token.value == "=":
                if skip_next_eq:
                    skip_next_eq = False
                else:
                    # treat as comparison
                    if i>0 and i+1<len(tokens):
                        left, right = tokens[i-1], tokens[i+1]
                        if left.type in {"IDENTIFIER","INT"} and right.type in {"IDENTIFIER","INT"}:
                            features.add("Comparison Operator")
                # don't clear datatype flag
            elif token.value == "|":
                if pattern_context > 0:
                    features.add("Pattern Matching")

        # Identifier-based features
        if token.type == "IDENTIFIER":
            if token.value == "_":
                features.add("Anonymous Variable")
            if token.value.lower() == "option":
                features.add("Option Type")
            # module usage via prefix
            if token.value in BASIS_MODULES and i+1 < len(tokens) and tokens[i+1].value == ".":
                features.add("Basis Library Module Usage")
            elif token.value[0].isupper() and token.value not in BASIS_MODULES and i+1 < len(tokens) and tokens[i+1].value == ".":
                features.add("External Module Usage")
            # free-standing basis functions
            if token.value in FREE_BASIS_FUNCS:
                features.add("Basis Library Module Usage")
            # function composition
            if token.value == "o":
                features.add("Function Composition")
            # recursive calls detection
            if token.value in fun_names and i not in fun_def_positions.values():
                # determine tail vs non-tail
                j = i+1
                # skip parentheses/comma
                while j < len(tokens) and tokens[j].type == "SYMBOL" and tokens[j].value in {'(',')',','}:
                    j += 1
                if j < len(tokens) and ((tokens[j].type == "KEYWORD" and tokens[j].value in {'in','end'}) or
                                        (tokens[j].type == "OPERATOR" and tokens[j].value == '|') or
                                        (tokens[j].type == "SYMBOL" and tokens[j].value == ';')):
                    rec_calls[token.value]['tail'] += 1
                else:
                    rec_calls[token.value]['non_tail'] += 1

    # Polymorphism: presence of type variables in a function
    if any(tok.value.startswith("'") for tok in tokens) and "Function Definition" in features:
        features.add("Polymorphic Function")

    # Recursion-based features
    for fname, counts in rec_calls.items():
        if counts['tail'] > 0:
            features.add("Tail Recursion")
        if counts['non_tail'] > 0:
            features.add("Non Tail Recursion Inefficiency")

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


    
