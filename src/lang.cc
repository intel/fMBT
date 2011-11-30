/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but WITHOUT
 * ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
 * more details.
 *
 * You should have received a copy of the GNU Lesser General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */

#include "dparse.h"
#include "helper.hh"
#include <getopt.h>

extern "C" {
extern D_ParserTables parser_tables_lang;
};

void print_usage()
{
  std::printf(
    "Usage: lang [options] inputfile\n"
    "Options:\n"
    "    -h     print usage\n"
    );
}

int main(int argc,char** argv) {
  int c;
  static struct option long_opts[] = {
    {"help", no_argument, 0, 'h'},
    {0, 0, 0, 0}
  };

  while ((c = getopt_long (argc, argv, "h", long_opts, NULL)) != -1) {
    switch (c)
      {
      case 'h':
	print_usage();
	return 0;
      default:
	return 2;
      }
  }

  if (optind == argc) {
    print_usage();
    return -1;
  }

  char *s;
  D_Parser *p = new_D_Parser(&parser_tables_lang, 512);
  s=readfile(argv[optind]);
  dparse(p,s,std::strlen(s));

  free_D_Parser(p);
  free(s);
  return 0;
}
