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

extern "C" {
extern D_ParserTables parser_tables_lang;
};

int main(int argc,char** argv) {
  char *s;
  D_Parser *p = new_D_Parser(&parser_tables_lang, 512);
  //std::string name(argv[1]);
  s=readfile(argv[1]);
  dparse(p,s,std::strlen(s));

  free_D_Parser(p);
  return 0;
}
