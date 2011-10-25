{
#include "stdio.h"
#include "string.h"
#include "stdlib.h"
char *xdup(char *s, char *e) {
  char *ss = malloc( e - s + 2 );
  memcpy(ss, s, e-s);
  ss[e-s] = 0;
  return ss;
}
}
top: A ( B C { printf("%s\n", xdup($n.start_loc.s, $n.end)); } ) D;
A: 'A';
B: 'B';
C: 'C';
D: 'D';
whitespace: "[\t\n ]";
