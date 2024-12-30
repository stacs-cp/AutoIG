%-----------------------------------------------------------------------------%
% Requires that 'y' occurs in the array or set 'x'.
%-----------------------------------------------------------------------------%

predicate picat_member_bool(array[int] of var bool: x, var bool: y);

predicate fzn_member_bool(array[int] of var bool: x, var bool: y) =
  picat_member_bool(x, y)
