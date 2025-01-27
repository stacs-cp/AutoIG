/** @group globals.sort Requires that the array \a x is in strictly_decreasing order (duplicates are allowed). */
predicate picat_strictly_decreasing_int(array[int] of var int: x);

predicate fzn_strictly_decreasing_int(array[int] of var int: x) =
  picat_strictly_decreasing_int(x)
