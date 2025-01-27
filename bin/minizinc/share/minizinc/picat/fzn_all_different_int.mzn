%-----------------------------------------------------------------------------%
% Constrains the array of objects 'x' to be all different.
%-----------------------------------------------------------------------------%

predicate picat_all_different_int(array[int] of var int: x);

predicate fzn_all_different_int(array[int] of var int: x) =
  picat_all_different_int(x);
