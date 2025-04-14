/** @group globals.channeling
  Constrains two arrays of int variables, \a f and \a invf, to represent
  inverse functions.  All the values in each array must be within the index
  set of the other array.
*/
predicate picat_inverse(array[int] of var int: f,
                  array[int] of var int: invf);

% predicate fzn_inverse(array[int] of var int: f,
%                       array[int] of var int: invf) =
%   picat_inverse(f, invf);
predicate fzn_inverse(array[int] of var int: f,
                      array[int] of var int: invf) = let {
  int: ox = if length(f) = 0 then 0 else min(index_set(f)) - 1 endif;
  int: oy = if length(invf) = 0 then 0 else min(index_set(invf)) - 1 endif;
  array [int] of var int: fo = [y - oy | y in f];
  array [int] of var int: invfo = [x - ox | x in invf];
} in picat_inverse(fo, invfo);
