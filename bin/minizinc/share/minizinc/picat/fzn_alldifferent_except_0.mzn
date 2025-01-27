/**  @group globals.alldifferent
  Constrain the array of integers \a vs to be all different except those
  elements that are assigned the value 0.
*/

predicate picat_alldifferent_except_0(array[int] of var int: vs);

predicate fzn_alldifferent_except_0(array[int] of var int: vs) =
  picat_alldifferent_except_0(vs)
