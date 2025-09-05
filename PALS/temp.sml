type result = {a: int, c: int, g: int, t: int}
fun nucleotideCounts (strand: string) : result =
  foldl
    (fn (x, {a, c, g, t}) =>
       case x of
         #"A" => {a = a + 1, c = c, g = g, t = t}
       | #"C" => {a = a, c = c + 1, g = g, t = t}
       | #"G" => {a = a, c = c, g = g + 1, t = t}
       | #"T" => {a = a, c = c, g = g, t = t + 1}
       | _ => raise Fail "Invalid nucleotide in strand")
       {a = 0, c = 0, g = 0, t = 0} (String.explode strand)