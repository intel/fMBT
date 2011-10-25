/* 
    $URL: http://manta.univ.gda.pl/svn/wb/parsing/dparser/D/dparse_tree.c $
    $Revision: 1.2 $
*/

#include <stdio.h>
#include <string.h>

#include "dparse_tree.h"

char *dup_str(char *s, char *e);  /* defined in util.h */

/* tunables */

#define MAX_LINE_LENGTH 44  /* must be at least 4 */
#define INDENT_SPACES 4

static void 
xprint_parsetree(D_ParserTables pt, D_ParseNode *pn, int depth, print_node_fn_t fn, void *client_data);

static void 
xprint_parsetree(D_ParserTables pt, D_ParseNode *pn, int depth, print_node_fn_t fn, void *client_data) {
  int nch = d_get_number_of_children(pn), i;
  char *name = (char*)pt.symbols[pn->symbol].name;
  //  int len = pn->end_skip - pn->start_loc.s;
  //  char *value = malloc(len+2);
  //  memcpy(value, pn->start_loc.s, len);
  //  value[len] = 0;
  char *value = dup_str(pn->start_loc.s, pn->end);
  fn(depth, name, value, client_data);
  free(value);

  depth++;
  if (nch != 0) {
    for (i = 0; i < nch; i++) {
      D_ParseNode *xpn = d_get_child(pn,i);
      xprint_parsetree(pt, xpn, depth, fn, client_data);
    }
  }
}

void 
print_parsetree(D_ParserTables pt, D_ParseNode *pn, print_node_fn_t fn, void *client_data) {
  xprint_parsetree(pt, pn, 0, (NULL==fn)?print_node_default:fn, client_data);
}

void 
print_node_parenthesised(int depth, char *name, char *value, void *client_data) {
  printf("( %s )", name);
}

static char *
change_newline2space(char *s) {
  char *ss = s;
  while (*ss++) 
    if (*ss == '\n') 
      *ss = ' ';
  if (strlen(s)>MAX_LINE_LENGTH) {
    *(s+MAX_LINE_LENGTH-3) = '.';
    *(s+MAX_LINE_LENGTH-2) = '.';
    *(s+MAX_LINE_LENGTH-1) = '.';
    *(s+MAX_LINE_LENGTH) = '\0';
  }
  return s;
}

void 
print_node_default(int depth, char *name, char *value, void *client_data) {
  printf("%*s", depth*INDENT_SPACES, "");
  printf("%s  %s.\n", name, change_newline2space(value));
}
