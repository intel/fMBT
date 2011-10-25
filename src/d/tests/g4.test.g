{
extern char *ops;
extern void *ops_cache;
#include "d.h"
int ops_scan(char *ops, void *ops_cache, d_loc_t *loc,
	     unsigned char *op_assoc, int *op_priority);

}

X: '1' (${scan ops_scan(ops, ops_cache)} '2')*;
