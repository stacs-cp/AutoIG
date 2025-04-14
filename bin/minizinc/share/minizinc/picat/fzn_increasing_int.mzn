/** @group globals.sort Requires that the array \a x is in increasing order (duplicates are allowed). */
predicate picat_increasing_int(array[int] of var int: x);

predicate fzn_increasing_int(array[int] of var int: x) =
  picat_increasing_int(x);
