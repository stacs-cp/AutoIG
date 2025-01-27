/** @Group globals.sort Requires that the array \a x is in strictly_increasing order (duplicates are allowed). */
predicate picat_strictly_increasing_int(array[int] of var int: x);

predicate fzn_strictly_increasing_int(array[int] of var int: x) =
  picat_strictly_increasing_int(x)
