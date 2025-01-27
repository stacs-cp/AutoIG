predicate picat_nvalue(var int: n, array[int] of var int: x);

predicate fzn_nvalue(var int: n, array[int] of var int: x) =
	picat_nvalue(n, x);
