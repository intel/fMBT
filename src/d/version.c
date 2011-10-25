/*
 Copyright 2002-2004 John Plevyak, All Rights Reserved
*/
#include "d.h"

void
d_version(char *v) {
  v += sprintf(v, "%d.%d", D_MAJOR_VERSION, D_MINOR_VERSION);
  if (strcmp("",D_BUILD_VERSION))
    v += sprintf(v, ".%s", D_BUILD_VERSION);
}

