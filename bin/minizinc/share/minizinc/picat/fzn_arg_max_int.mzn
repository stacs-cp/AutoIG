predicate picat_argmax(array[int] of var int: x, var int: z);

predicate fzn_maximum_arg_int(array[int] of var int: x, var int: z) =
	picat_argmax(x, z);

