#!/usr/bin/env python3
import os
import shutil
import pandas as pd
from collections import Counter
from studentSystem.new_parser import detect_features_from_ast, PARSER

# ─── Test‐wrapper around your AST parser ─────────────────────────────────────────
def test_parser(code: str, index: int):
    """
    Parse the given SML code snippet and return a dict with the list of detected features.
    """
    tree = PARSER.parse(code.encode())
    features = detect_features_from_ast(tree.root_node)
    return {"features": features}

# ─── Simple multi‐label evaluation ───────────────────────────────────────────────
def evaluate_prediction(predicted: list, actual: str) -> dict:
    """
    Compare predicted feature list vs. the comma-separated gold string.
    Returns TP, FP, FN counts plus lists of Correct/Missed/Incorrect labels.
    """
    predicted_set = set(predicted)
    actual_set    = set(f.strip() for f in actual.split(",") if f.strip())

    tp = len(predicted_set & actual_set)
    fp = len(predicted_set - actual_set)
    fn = len(actual_set - predicted_set)

    return {
        "TP": tp,
        "FP": fp,
        "FN": fn,
        "Correct":    sorted(predicted_set & actual_set),
        "Missed":     sorted(actual_set - predicted_set),
        "Incorrect":  sorted(predicted_set - actual_set)
    }

# ─── Main harness ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # 1) Load dataset
    dataset = pd.read_csv("standardml_dataset.csv")

    # 2) Snapshot prior results if they exist
    if os.path.exists("parser_evaluation_output.txt"):
        shutil.copy("parser_evaluation_output.txt", "snapshot.txt")

    TP = FP = FN = 0

    # 3) Open the new output file
    with open("parser_evaluation_output.txt", "w", encoding="utf-8") as out:
        # 4) Evaluate each snippet
        for idx, row in dataset.iterrows():
            code          = row["Code"]
            gold_features = row["Features"]
            result        = test_parser(code, idx)

            eval_res = evaluate_prediction(result["features"], gold_features)
            TP += eval_res["TP"]
            FP += eval_res["FP"]
            FN += eval_res["FN"]

            # 5) Write detailed per‐snippet log
            out.write("=" * 60 + "\n")
            out.write(f"[#{idx+1}] Code:\n{code}\n")
            out.write(f"- Ground Truth: {gold_features}\n")
            out.write(f"- Predicted:    {', '.join(result['features'])}\n")
            out.write(f"- ✅ Correct:    {', '.join(eval_res['Correct'])}\n")
            out.write(f"- ❌ Missed:     {', '.join(eval_res['Missed'])}\n")
            out.write(f"- 🚫 Incorrect:  {', '.join(eval_res['Incorrect'])}\n")
            out.write("=" * 60 + "\n\n")

        # 6) Compute overall metrics
        precision = TP / (TP + FP) if TP + FP else 0.0
        recall    = TP / (TP + FN) if TP + FN else 0.0
        f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

        # 7) Append summary
        out.write("\n" + "#" * 40 + "\n")
        out.write("📊 Overall Evaluation Metrics\n")
        out.write(f"- True Positives:  {TP}\n")
        out.write(f"- False Positives: {FP}\n")
        out.write(f"- False Negatives: {FN}\n")
        out.write(f"- Precision:       {precision:.2f}\n")
        out.write(f"- Recall:          {recall:.2f}\n")
        out.write(f"- F1 Score:        {f1:.2f}\n")
        out.write("#" * 40 + "\n")

    print(f"Done! Results written to parser_evaluation_output.txt (snapshot → snapshot.txt).")