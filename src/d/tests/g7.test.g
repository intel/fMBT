{
#include "dparse.h"
#include "g7.test.g.d_parser.h"
int myscanner(d_loc_t *loc, unsigned short *symbol, 
      int *term_priority, unsigned char *op_assoc, int *op_priority) 
{
  if (loc->s[0] == 'a') {
    loc->s++;
    *symbol = A;
    return 1;
  } else if (loc->s[0] == 'b') {
    loc->s++;
    *symbol = BB;
    return 1;
  } else if (loc->s[0] == 'c') {
    loc->s++;
    *symbol = CCC;
    return 1;
  } else if (loc->s[0] == 'd') {
    loc->s++;
    *symbol = DDDD;
    return 1;
  } else
    return 0;
}

}
${scanner myscanner}
${token A BB CCC DDDD}

S: A (BB CCC)+ SS;
SS: DDDD;
