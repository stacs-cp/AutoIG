%-----------------------------------------------------------------------------%
% Constrains 'c' to be strictly less than the number of occurrences of 'y'
% in 'x'.
%-----------------------------------------------------------------------------%

predicate picat_count_lt(array[int] of var int: x, var int: y, var int: c);

predicate fzn_count_lt(array[int] of var int: x, var int: y, var int: c) =
  picat_count_lt(x, y, c);

%-----------------------------------------------------------------------------%
