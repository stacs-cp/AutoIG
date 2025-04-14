predicate picat_sliding_sum(int: low, int: up, int: seq, array[int] of var int: vs);

predicate fzn_sliding_sum(int: low, int: up, int: seq, array[int] of var int: vs) =
	picat_sliding_sum(low, up,seq, vs);
