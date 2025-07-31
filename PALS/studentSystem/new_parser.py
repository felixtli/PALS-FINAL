import os
import platform
import re
from typing import List, Set
from tree_sitter import Language, Parser, Node

# ─── 1) Load the compiled SML grammar ────────────────────────────────────────────
ext = "dll" if platform.system() == "Windows" else "so"

HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
LIB_PATH = os.path.join(PROJECT_ROOT, "build", f"sml.{ext}")

SML_LANGUAGE = Language(LIB_PATH, "sml")

PARSER = Parser()
PARSER.set_language(SML_LANGUAGE)

# ─── 2) Config lists ────────────────────────────────────────────────────────────
# Added "type" so we can skip its '=' in fallback comparison logic
KEYWORDS = {
    "val", "fun", "and", "if", "then", "else", "let", "in", "end",
    "case", "of", "raise", "fn", "andalso", "orelse", "not",
    "local", "structure", "signature", "functor", "ref", "while", "datatype",
    "use", "type"
}
BASIS_MODULES    = {"List", "String", "Math", "Char", "Word", "Option",
                    "IntInf", "IntArray", "Real"}
FREE_BASIS_FUNCS = {"foldl", "foldr", "map", "filter", "explode",
                    "implode", "length", "ceil"}

OPERATORS = {
    "+", "-", "*", "/", "^", "=", "<>", "<", ">", "<=", ">=",
    ":=", "::", "@", "=>", "|", "~", "mod", "div"
}
SYMBOLS = {"(", ")", "[", "]", "{", "}", ",", ".", ";"}

class Token:
    def __init__(self, type_: str, value: str):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f"{self.type}({self.value})"

def classify_token(s: str) -> Token:
    if s in KEYWORDS:
        return Token("KEYWORD", s)
    elif s.isdigit():
        return Token("INT", s)
    elif s.startswith('"') and s.endswith('"'):
        return Token("STRING", s)
    elif s in OPERATORS:
        return Token("OPERATOR", s)
    elif s in SYMBOLS:
        return Token("SYMBOL", s)
    else:
        return Token("IDENTIFIER", s)

def tokenize(code: str) -> List[Token]:
    tokens, curr, i = [], "", 0
    while i < len(code):
        c = code[i]
        if c.isspace():
            if curr:
                tokens.append(classify_token(curr)); curr=""
            i += 1; continue
        two = code[i:i+2]
        if two in OPERATORS or two in SYMBOLS:
            if curr:
                tokens.append(classify_token(curr)); curr=""
            tokens.append(classify_token(two))
            i += 2; continue
        if c in OPERATORS or c in SYMBOLS:
            if curr:
                tokens.append(classify_token(curr)); curr=""
            tokens.append(classify_token(c))
            i += 1; continue
        curr += c; i += 1
    if curr:
        tokens.append(classify_token(curr))
    return tokens

def detect_token_features(tokens: List[Token]) -> Set[str]:
    feats: Set[str] = set()
    in_let = in_local = False
    pattern_ctx = 0

    skip_next_eq = False
    for i, tok in enumerate(tokens):
        if tok.type == "KEYWORD":
            kw = tok.value
            if kw in ("fun", "val", "datatype", "type"):
                # skip the very next '=' (head) to avoid counting it as comparison
                skip_next_eq = True
            if kw == "fun":
                feats.add("Function Definition")
                if in_let or in_local:
                    feats.add("Local Function Definition")
                # Curried function: ≥2 parameters
                j, cnt = i+2, 0
                while j < len(tokens) and tokens[j].type == "IDENTIFIER":
                    cnt += 1; j += 1
                if cnt >= 2:
                    feats.add("Curried Function")
            elif kw == "val":
                feats.add("Variable Assignment")
            elif kw == "datatype":
                feats.add("Datatype Definition")
            elif kw == "and" and i > 0 and tokens[i-1].value == "fun":
                feats.add("Multiple Recursive Functions")
            elif kw == "if":
                feats.add("Conditional Statement")
            elif kw == "let":
                feats.add("Let Binding"); in_let = True
            elif kw == "local":
                feats.add("Local Binding"); in_local = True
            elif kw == "case":
                feats.add("Pattern Matching"); pattern_ctx += 1
            elif kw == "raise":
                feats.add("Exception Raising")
            elif kw == "fn":
                feats.add("Lambda Function")
            elif kw in {"andalso","orelse","not"}:
                feats.add("Logical Operator")
            elif kw == "use":
                feats.add("Use Directive")

        if tok.type == "OPERATOR":
            # Arithmetic
            if tok.value in {"+","-","*","/","mod","div","~"}:
                feats.add("Arithmetic Operation")
            # String concat
            if tok.value == "^":
                feats.add("String Concatenation")
            # Comparisons (with skip for first '=' after fun/val/datatype/type)
            if tok.value in {"=","<>","<",">","<=",">="}:
                if tok.value == "=" and skip_next_eq:
                    skip_next_eq = False
                else:
                    feats.add("Comparison Operator")

        if tok.type == "SYMBOL" and tok.value == "|" and pattern_ctx > 0:
            feats.add("Pattern Matching")

        if tok.type == "IDENTIFIER":
            if tok.value == "_":
                feats.add("Anonymous Variable")
            if tok.value.lower() == "option":
                feats.add("Option Type")
            if tok.value in FREE_BASIS_FUNCS:
                feats.add("Basis Library Module Usage")
            if tok.value == "o":
                feats.add("Function Composition")

    return feats

# ─── 4) AST helpers ─────────────────────────────────────────────────────────────
def traverse(node: Node):
    yield node
    for c in node.children:
        yield from traverse(c)

def find_nodes(root: Node, typ: str):
    return [n for n in traverse(root) if n.type == typ]

def is_in_let_or_local(fn: Node) -> bool:
    p = fn.parent
    while p:
        if p.type in ("let_exp","local_exp"):
            return True
        p = p.parent
    return False

def is_tail_call(fn_node: Node, fn_name: str) -> bool:
    body = fn_node.child_by_field_name("body")
    if not body: return False
    def check(node: Node) -> bool:
        if node.type == "seq_exp":
            return bool(node.named_children and check(node.named_children[-1]))
        if node.type == "app_exp":
            fnc = node.named_children[0] if node.named_children else None
            return fnc and fnc.text.decode() == fn_name
        if node.type == "if_exp":
            c = node.child_by_field_name("consequence")
            a = node.child_by_field_name("alternative")
            return bool(c and a and check(c) and check(a))
        if node.type == "case_exp":
            rules = [r for r in node.named_children if r.type=="mrule"]
            if not rules: return False
            return all(r.named_children and check(r.named_children[-1]) for r in rules)
        if node.type in ("let_exp","local_exp"):
            inner = node.child_by_field_name("body")
            return bool(inner and check(inner))
        return False
    return check(body)

def contains_call(fn_node: Node, fn_name: str) -> bool:
    return any(
        app.named_children and app.named_children[0].text.decode() == fn_name
        for app in find_nodes(fn_node, "app_exp")
    )

def has_mutual_recursion(root: Node) -> bool:
    funcs = find_nodes(root, "fvalbind")
    parents = [f.parent for f in funcs]
    return len(funcs) >= 2 and any(parents.count(p) > 1 for p in parents)

def detect_features_from_ast(root: Node) -> List[str]:
    feats: Set[str] = set()
    code_str = root.text.decode()

    # Variable Assignment & Constant
    for vb in find_nodes(root, "valbind"):
        feats.add("Variable Assignment")
        v = vb.child_by_field_name("value")
        if v and v.type in ("integer_scon","string_scon"):
            feats.add("Constant Expression")

    # Functions & recursion
    for fn in find_nodes(root, "fvalbind"):
        nm = fn.child_by_field_name("name")
        name = nm.text.decode() if nm else None
        feats.add("Function Definition")
        if is_in_let_or_local(fn):
            feats.add("Local Function Definition")
        if has_mutual_recursion(root):
            feats.add("Multiple Recursive Functions")
        sig = fn.child_by_field_name("type_signature")
        if sig and "'" in sig.text.decode():
            feats.add("Polymorphic Function")
        if name:
            if is_tail_call(fn, name):
                feats.add("Tail Recursion")
            elif contains_call(fn, name):
                feats.add("Non Tail Recursion Inefficiency")

    # Conditionals & nested
    for ifn in find_nodes(root, "if_exp"):
        feats.add("Conditional Statement")
        c = ifn.child_by_field_name("consequence")
        if c and any(x.type=="if_exp" for x in traverse(c)):
            feats.add("Nested Conditional Statement")
    # fallback nested-if
    if ("Nested Conditional Statement" not in feats
        and re.search(r"\belse\s+if\b", code_str)):
        feats.add("Nested Conditional Statement")

    # Let / local
    if any(n.type=="let_exp" for n in traverse(root)):
        feats.add("Let Binding")
    if any(n.type=="local_exp" for n in traverse(root)):
        feats.add("Local Binding")

    # Pattern matching
    if any(n.type=="case_exp" for n in traverse(root)):
        feats.add("Pattern Matching")
    # fallback for multi-clause '|' outside case
    if ("Pattern Matching" not in feats
        and re.search(r"(?m)^\s*\|", code_str)):
        feats.add("Pattern Matching")

    # Exceptions
    if any(n.type=="raise_exp" for n in traverse(root)):
        feats.add("Exception Raising")

    # Lambdas
    if any(n.type=="fn_exp" for n in traverse(root)):
        feats.add("Lambda Function")

    # Infix operations (AST)
    for inf in find_nodes(root, "infix_exp") + find_nodes(root, "infix_binding"):
        op = inf.child_by_field_name("op")
        txt = op.text.decode() if op else ""
        if txt in ("+","-","*","/","mod","div","~"):
            feats.add("Arithmetic Operation")
        if txt == "^":
            feats.add("String Concatenation")
        if txt in ("=","<>","<",">","<=",">="):
            feats.add("Comparison Operator")

    # Logical
    if any(n.text.decode() in ("andalso","orelse","not") for n in traverse(root)):
        feats.add("Logical Operator")

    # Loops & refs
    if any(n.type=="while_exp" for n in traverse(root)):
        feats.add("Use Of While Loops")
    if any(n.type=="ref_exp" for n in traverse(root)):
        feats.add("Use Of Refs")

    # Datatypes
    if any(n.type=="datatype_dec" for n in traverse(root)):
        feats.add("Datatype Definition")

    # Custom infix
    if any(n.type in ("infix_dec","infixr_dec","nonfix_dec")
           for n in traverse(root)):
        feats.add("Custom Infix Operator")
    # fallback op definitions
    if ("Custom Infix Operator" not in feats
        and re.search(r"\bval\s+op[^\s=]+\s*=", code_str)):
        feats.add("Custom Infix Operator")

    # Use-directives
    if any(n.type=="use_dec" for n in traverse(root)):
        feats.add("Use Directive")

    # Module/IO/printing
    for fe in find_nodes(root, "field_exp"):
        recv = fe.child_by_field_name("receiver")
        fld  = fe.child_by_field_name("field")
        if recv and fld:
            rn, fn = recv.text.decode(), fld.text.decode()
            if rn in BASIS_MODULES or fn in FREE_BASIS_FUNCS:
                feats.add("Basis Library Module Usage")
            else:
                feats.add("External Module Usage")
            if rn == "TextIO":
                if fn in ("openIn","inputLine","inputAll"):
                    feats.add("Reading input from a file")
                if fn in ("openOut","output"):
                    feats.add("Writing output to a file")
                if fn == "print":
                    feats.add("Printing")
    if any(n.type=="vid" and n.text.decode()=="print"
           for n in traverse(root)):
        feats.add("Printing")

    # Option types (fallback)
    if "Option Type" not in feats and re.search(r"\boption\b", code_str):
        feats.add("Option Type")

    # Function composition
    if any(n.child_by_field_name("op") and
           n.child_by_field_name("op").text.decode()=="o"
           for n in find_nodes(root, "infix_exp")):
        feats.add("Function Composition")
    elif "Function Composition" not in feats and re.search(r"\bo\b", code_str):
        feats.add("Function Composition")

    # Polymorphic fallback: any 'a, 'b etc anywhere
    if ("Polymorphic Function" not in feats
        and re.search(r"'\w+", code_str)):
        feats.add("Polymorphic Function")

    # Non–tail recursion fallback: name appears >1× and no tail recursion
    for fn in find_nodes(root, "fvalbind"):
        nm = fn.child_by_field_name("name")
        name = nm.text.decode() if nm else None
        if (name and code_str.count(name) > 1
            and "Tail Recursion" not in feats):
            feats.add("Non Tail Recursion Inefficiency")

    # Finally merge in the rest of the token‐based heuristics
    feats |= detect_token_features(tokenize(code_str))

    return sorted(feats)