/** @group globals.lexicographic
  Requires that \a i precedes \a i+1 in the array \a x for all positive \a i.
*/
predicate picat_seq_precede_chain_int(array[int] of var int: x);

predicate fzn_seq_precede_chain_int(array[int] of var int: X) =
  picat_seq_precede_chain_int(X);
