predicate picat_count_eq_reif(array[int] of var int: x, var int: y, var int: c, var bool: b);

predicate fzn_count_eq_reif(array[int] of var int: x, var int: y, var int: c, var bool: b) =
  picat_count_eq_reif(x, y, c, b);

%-----------------------------------------------------------------------------%
