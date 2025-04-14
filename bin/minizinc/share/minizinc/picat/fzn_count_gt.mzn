%-----------------------------------------------------------------------------%
% Constrains 'c' to be strictly greater than the number of occurrences of 'y'
% in 'x'.
%-----------------------------------------------------------------------------%

predicate picat_count_gt(array[int] of var int: x, var int: y, var int: c);

predicate fzn_count_gt(array[int] of var int: x, var int: y, var int: c) =
  picat_count_gt(x, y, c);

%-----------------------------------------------------------------------------%
