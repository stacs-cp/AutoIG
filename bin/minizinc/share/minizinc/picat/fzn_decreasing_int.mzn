/** @group globals.sort Requires that the array \a x is in decreasing order (duplicates are allowed). */
predicate picat_decreasing_int(array[int] of var int: x);

predicate fzn_decreasing_int(array[int] of var int: x) =
  picat_decreasing_int(x)
