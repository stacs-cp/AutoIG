%-----------------------------------------------------------------------------%
% Constrains the array of objects 'x' to be all equal.
%-----------------------------------------------------------------------------%

predicate picat_all_equal(array[int] of var int: x);

predicate fzn_all_equal_int(array[int] of var int: x) =
	picat_all_equal(x);
