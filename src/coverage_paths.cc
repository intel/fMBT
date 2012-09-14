/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "coverage_paths.hh"

#include "dparse.h"

extern std::vector<std::string*> *paths_ff,*paths_tt,*paths_dd;

extern "C" {
  extern D_ParserTables parser_tables_paths;
}

class Coverage_pathsw: public Coverage_paths {
public:
  Coverage_pathsw(Log& l,std::string params):
    Coverage_paths(l,_f,_t,_d) 
  {

    paths_ff=&_f;
    paths_tt=&_t;
    paths_dd=&_d;

    D_Parser *p = new_D_Parser(&parser_tables_paths, 512);
    bool ret=dparse(p,(char*)params.c_str(),strlen(params.c_str()));
    ret=p->syntax_errors==0 && ret;
    status=ret;
    if (p->syntax_errors>0) {
      errormsg="Syntax error...";
    }
    free_D_Parser(p);
    from=_f;
    to=_t;
    drop=_d;
  }
  virtual ~Coverage_pathsw() {}
private:
  std::vector<std::string*> _f,_t,_d;
};

void Coverage_paths::on_restart() {
  executed.clear();
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_pathsw, "paths")
