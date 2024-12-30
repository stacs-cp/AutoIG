/**  @group globals.packing
  Requires that each item \p i with weight \a w[\p i], be put into \a bin[\p i] such 
  that the sum of the weights of the items in each bin \p b is equal to
  \a load[\p b].

  Assumptions:
  - forall \p i, \a w[\p i] >=0
*/
predicate picat_bin_packing_load(array[int] of var int: load,
                           array[int] of var int: bin,
                           array[int] of int: w);

predicate fzn_bin_packing_load(array[int] of var int: load,
                           array[int] of var int: bin,
                           array[int] of int: w) =
  picat_bin_packing_load(load, bin, w);
%-----------------------------------------------------------------------------%
