/* 
    $URL: http://manta.univ.gda.pl/svn/wb/parsing/dparser/D/dparse_tree.h $
    $Revision: 1.1 $

    This interface provides a `print_parsetree' function that can 
    be used to print a parse tree built by Dparser.  The implementation
    of `print_parsetree' calls, on every node of the parse tree,
    a function `fn` that should print the node. Two such functions are 
    provided: `print_node_default' which uses indentation to show the parse 
    tree and `print_node_parenthesised' which uses parens.

    Three additional files provide an example:
      -- `driver_parsetree.c' contains a program illustrating the use of `print_parsetree',
      -- `4calc.g' contains a grammar for a simple calculator,
      -- `4calc.in' an expression to parse. 
    The following commands can be used to compile and try out the example:
      make_dparser 4calc.g
      cc -o 4calc driver_parsetree.c 4calc.g.d_parser.c -I/usr/local/include -L/usr/local/lib -ldparse 
      ./4calc 4calc.in
*/

#ifndef _parsetree_H_
#define _parsetree_H_

#include "dparse.h"


/* `print_node_fn_t' type defines a class of callback functions that
   the `print_parsetree' function uses to print a node   */

typedef void (print_node_fn_t)(int depth, char *token_name, char *token_value, void *client_data);

/*  if `fn' is NULL, then the function `print_node_default' is used  */

void 
print_parsetree(D_ParserTables pt, D_ParseNode *pn, print_node_fn_t fn, void *client_data);


/* `print_node_default' truncates `token_value' to 44 characters 
    and replaces newlines with spaces */

void 
print_node_default(int depth, char *token_name, char *token_value, void *client_data);

void 
print_node_parenthesised(int depth, char *token_name, char *token_value, void *client_data);

#endif
