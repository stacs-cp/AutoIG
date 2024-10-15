/** @group globals
  Defines a network flow constraint with cost.

@param arc: a directed arc of the flow network. Arc \p i connects node \a arc[\p i,1] to node \a arc[\p i,2].
@param balance: the difference between input and output flow for each node.
@param weight: the unit cost of the flow through the arc.
@param flow: the flow going through each arc.
@param cost: the overall cost of the flow.
*/
predicate picat_network_flow_cost(array[int] of int: arc,
    array[int] of int: balance,
    array[int] of int: weight,
    array[int] of var int: flow, var int: cost);


predicate fzn_network_flow_cost(array[int,1..2] of int: arc,
    array[int] of int: balance,
    array[int] of int: weight,
    array[int] of var int: flow, var int: cost) =
  picat_network_flow_cost(array1d(arc), balance, weight, flow, cost);
