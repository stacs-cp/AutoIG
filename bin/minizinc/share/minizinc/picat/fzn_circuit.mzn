%-----------------------------------------------------------------------------%
% Constrains the elements of 'x' to define a circuit where 'x[i] = j' means
% that 'j' is the successor of 'i'.
%-----------------------------------------------------------------------------%

predicate picat_circuit(array[int] of var int: x);

% predicate fzn_circuit(array[int] of var int: x) = picat_circuit(x);
predicate fzn_circuit(array[int] of var int: x) = let {
  array [index_set(x)] of var index_set(x): xx = x;
} in picat_circuit(xx);
%-----------------------------------------------------------------------------%
