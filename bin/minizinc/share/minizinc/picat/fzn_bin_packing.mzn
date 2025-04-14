/**  @group globals.packing
  Requires that each item \p i with weight \a w[\p i], be put into \a bin[\p i] such 
  that the sum of the weights of the items in each bin does not exceed the 
  capacity \a c.

  Assumptions:
  - forall \p i, \a w[\p i] >=0
  - \a c >=0
*/

predicate picat_bin_packing(int: c,
                      array[int] of var int: bin,
                      array[int] of int: w);

predicate fzn_bin_packing(int: c,
                      array[int] of var int: bin,
                      array[int] of int: w) =
  picat_bin_packing(c, bin, w);

%-----------------------------------------------------------------------------%
