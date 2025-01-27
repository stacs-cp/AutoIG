%-----------------------------------------------------------------------------%
% Requires that 'y' occurs in the array or set 'x'.
%-----------------------------------------------------------------------------%

predicate picat_member_int(array[int] of var int: x, var int: y);

predicate fzn_member_int(array[int] of var int: x, var int: y) =
  picat_member_int(x, y)
