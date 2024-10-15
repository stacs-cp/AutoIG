int: a;  % Input a
var -3..30: x;
var 0..6: y;
var -10..100000: z;

constraint x = a;
constraint pow(x, y) = z;

solve satisfy;