import re
import regex

def removeSMlComments(code):
    return re.sub(r"\(\*.*?\*\)", "", code, flags=re.DOTALL)

def detectSMLFeatures(code):
    features = []
    code = removeSMlComments(code)
    code = code.splitlines()

    # Detect variable assignment (e.g., val x = ...)
    for line in code:
        line = line.strip()
        if re.search(r"\bval\s+\w+\s*=", line):
            features.append('Variable Assignment')
            break
    
    # Detect arithmetic operations (e.g: +, -, *, div, mod)
    pattern = r"\b\w+\b\s*(\+|\-|\*|div|mod)\s*\b\w+\b"
    for line in code:
        line = line.strip()
        if regex.search(pattern, line):
            features.append('Arithmetic Operation')
            break
    
    # Detect string concatenation
    pattern = r"\w+\s*\^\s*\w+"
    for line in code:
        line = line.strip()
        if re.search(pattern, line):
            features.append('String Concatenation')
            break
    
    # Detect function definitions (e.g., fun ...)
    pattern = r"\bfun\s+\w+\s+"
    for line in code:
        line = line.strip()
        if re.search(pattern, line):
            features.append('Function Definition')
            break

    # Detect conditional statements with a sliding window
    window_size = 3 # 3 lines are checked together in case of multi-line if-then-else
    pattern = r"\bif\b\s+.+?\s+\bthen\b"
    for i in range(len(code) - window_size + 1):
        snippet = code[i:i + window_size]
        snippet = ' '.join(snippet)
        if re.search(pattern, snippet):
            features.append('Conditional Statement')
            break

    # Detect comparison operators (e.g: =, <>, <, >, <=, >=)
    clause_pattern = r"^(fun|\||val|datatype)" # Excludes = signs that are found in function, datatype, and variable definitions
    pattern = r"if\s+\b\w+\b\s*(<>|<=|>=|=|<|>)\s*\b\w+\b"
    for line in code:
        line = line.strip()
        if not re.match(clause_pattern, line):
            if re.search(pattern, line):
                features.append('Comparison Operator')
                break

    return features

# Example usage
code = """exception notFound;
exception cannotSortEmptyList
fun min (x::[]) = x
  | min [] = raise cannotSortEmptyList
  | min (x::y::rest) = if x>y then (min (y::rest)) else (min (x::rest))
fun removeFirst c [] = raise notFound
    | removeFirst c (x::xs) = if c = x then xs else x::(removeFirst c xs)
fun isort [] = []|
    isort ls = 
    let val m = min ls
    in
      m::(isort (removeFirst m ls ) )
    end
(*See omri kleins sort here: https://stackoverflow.com/questions/14411862/standard-sorting-functions-in-sml*)
fun sort list = foldr (fn (x:char,lst)=> List.filter (fn a => a < x) lst @ [x] @ List.filter (fn a => a >= x) lst ) [] list;
fun toLowerChars word = ((List.map Char.toLower) o String.explode) word
fun sortedChars word = (sort o toLowerChars) word
fun isAnagram w1 w2 =  (sortedChars w1) = (sortedChars w2)
fun toLower s = (String.implode o toLowerChars) s
fun anagramsFor subject candidates =
  case candidates of [] => []
  | x::xs => if (toLowerChars x = toLowerChars subject) 
      then (anagramsFor subject xs) 
      else if (isAnagram subject x) then x::(anagramsFor subject xs) else (anagramsFor subject xs)"""

print(detectSMLFeatures(code))