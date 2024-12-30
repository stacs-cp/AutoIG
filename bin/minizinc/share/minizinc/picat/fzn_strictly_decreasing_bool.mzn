/** @group globals.sort Requires that the array \a x is in strictly_decreasing order (duplicates are allowed). */
predicate picat_strictly_decreasing_bool(array[int] of var bool: x);

predicate fzn_strictly_decreasing_bool(array[int] of var bool: x) =
  picat_strictly_decreasing_bool(x);
