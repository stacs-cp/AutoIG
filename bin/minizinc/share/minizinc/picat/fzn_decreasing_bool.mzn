/** @group globals.sort Requires that the array \a x is in decreasing order (duplicates are allowed). */
predicate picat_decreasing_bool(array[int] of var bool: x);

predicate fzn_decreasing_bool(array[int] of var bool: x) =
  picat_decreasing_bool(x);
