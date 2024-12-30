%-----------------------------------------------------------------------------%
% Requires that the array 'x' is lexicographically less than or equal to
% array 'y'.  Compares them from first to last element, regardless of indices
%-----------------------------------------------------------------------------%

predicate picat_lex_lesseq_bool(array[int] of var bool: x,
                                array[int] of var bool: y);

predicate fzn_lex_lesseq_bool(array[int] of var bool: x,
                              array[int] of var bool: y) =
  picat_lex_lesseq_bool(x, y);
%-----------------------------------------------------------------------------%
