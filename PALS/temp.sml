fun eggCount (number: int): int =
  let
    infix 5 &
    val op& = Word.andb
    fun popCount (0w0, n) = n
      | popCount (w, n) = popCount (w & (w - 0w1), n + 1)
  in
    popCount (Word.fromInt number, 0)
  end