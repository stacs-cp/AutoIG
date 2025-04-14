%-----------------------------------------------------------------------------%
% Constrains 'c' to be greater than or equal to the number of occurrences of
% 'y' in 'x'.
%-----------------------------------------------------------------------------%

predicate picat_count_geq(array[int] of var int: x, var int: y, var int: c);

predicate fzn_count_geq(array[int] of var int: x, var int: y, var int: c) =
  picat_count_geq(x, y, c);
%-----------------------------------------------------------------------------%
