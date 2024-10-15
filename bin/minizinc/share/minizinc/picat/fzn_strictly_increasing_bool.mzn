/** @group globals.sort Requires that the array \a x is in strictly_increasing order (duplicates are allowed). */
predicate picat_strictly_increasing_bool(array[int] of var bool: x);

predicate fzn_strictly_increasing_bool(array[int] of var bool: x) =
  picat_strictly_increasing_bool(x);
