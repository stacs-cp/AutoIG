include "count_fn.mzn";

%-----------------------------------------------------------------------------%
% Requires at most 'n' variables in 'x' to take the value 'v'.
%-----------------------------------------------------------------------------%

predicate picat_at_most(int: n, array[int] of var int: x, int: v);

predicate fzn_at_most_int(int: n, array[int] of var int: x, int: v) =
    picat_at_most(n, x, v)

