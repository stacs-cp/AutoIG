%-----------------------------------------------------------------------------%
% Constrains 'c' to be the number of occurrences of 'y' in 'x'. 
%-----------------------------------------------------------------------------%

predicate picat_count_eq(array[int] of var int: x, var int: y, var int: c);

predicate fzn_count_eq(array[int] of var int: x, var int: y, var int: c) =
  picat_count_eq(x, y, c);
%-----------------------------------------------------------------------------%
