/** @group globals.sort Requires that the array \a x is in increasing order (duplicates are allowed). */
predicate picat_increasing_bool(array[int] of var bool: x);

predicate fzn_increasing_bool(array[int] of var bool: x) =
  picat_increasing_bool(x);

