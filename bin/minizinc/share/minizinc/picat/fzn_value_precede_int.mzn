/** @group globals.lexicographic
  Requires that \a s precede \a t in the array \a x.

  Precedence means that if any element of \a x
  is equal to \a t, then another element of \a x with a  lower index is equal
  to \a s.
*/
predicate picat_value_precede_int(int: s, int: t, array[int] of var int: x);

predicate fzn_value_precede_int(int: s, int: t, array[int] of var int: x) =
  picat_value_precede_int(s, t, x);
