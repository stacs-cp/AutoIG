/** @group globals.lexicographic
  Requires that \a c[\p i] precedes \a c[\p i +1] in the array \a x.
  
  Precedence means that if any element of \a x
  is equal to \a c[\p i +1], then another element of \a x with a  lower index is equal
  to \a c[\p i].
*/
predicate picat_value_precede_chain_int(array[int] of int: c, array[int] of var int: x);

predicate fzn_value_precede_chain_int(array[int] of int: c, array[int] of var int: x) = 
  picat_value_precede_chain_int(c, x)
