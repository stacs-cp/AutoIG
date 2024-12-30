/** @group globals.packing
  Constrains rectangles \p i, given by their origins (\a x[\p i], \a y[\p i])
  and sizes (\a dx[\p i], \a dy[\p i]), to be non-overlapping. Zero-width
  rectangles can be packed anywhere.
*/
predicate picat_diffn_nonstrict(array[int] of var int: x,
                          array[int] of var int: y,
                          array[int] of var int: dx,
                          array[int] of var int: dy);

predicate fzn_diffn_nonstrict(array[int] of var int: x,
                          array[int] of var int: y,
                          array[int] of var int: dx,
                          array[int] of var int: dy) =
  picat_diffn_nonstrict(x, y, dx, dy);
