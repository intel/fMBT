{
#include <stdio.h>
#include <stdlib.h>

typedef struct My_ParseNode {
  int value;
} My_ParseNode;
#define D_ParseNode_User My_ParseNode
}

translation_unit : 
      statement*
   ;
 
statement :
      expr ';' { printf("%d\n", $0.value); }
   ;

expr :  
      integer                    { $$.value = atoi($n0.start_loc.s); } 
   |  expr '+' expr  $right 10   { $$.value = $0.value + $2.value; } 
   |  expr '-' expr  $right 10   { $$.value = $0.value - $2.value; } 
   |  expr '*' expr  $right 20   { $$.value = $0.value * $2.value; }
   |  expr '/' expr  $right 20   { $$.value = $0.value / $2.value; }
   |   '(' expr ')'              { $$.value = $1.value; }
   ;

integer : 
      "-?[0-9]+" 
   ;
