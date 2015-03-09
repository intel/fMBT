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

extern int paths_node_size;

class Coverage_pathsw: public Coverage_paths_base {
public:
  Coverage_pathsw(Log& l,std::string params):
    Coverage_paths_base(l,_f,_t,_d)
  {
    paths_ff=&_f;
    paths_tt=&_t;
    paths_dd=&_d;

    D_Parser *p = new_D_Parser(&parser_tables_paths, paths_node_size);
    remove_force(params);
    bool ret=dparse(p,(char*)params.c_str(),strlen(params.c_str()));
    ret=p->syntax_errors==0 && ret;
    status=ret;
    if (p->syntax_errors>0) {
      errormsg="Syntax error...";
      status=false;
    }
    free_D_Parser(p);
    /*
    from=_f;
    to=_t;
    drop=_d;
    */
  }
  virtual ~Coverage_pathsw() {
    for_each(from.begin(),from.end(),ds);
    for_each(to.begin(),to.end(),ds);
    for_each(drop.begin(),drop.end(),ds);
  }
private:
  std::vector<std::string*> _f,_t,_d;
};

class Coverage_uinputs: public Coverage_pathsw {
public:
  Coverage_uinputs(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=true;
    pf=true;
    af=false;
  }
  virtual ~Coverage_uinputs() {}
};

class Coverage_uexecs: public Coverage_pathsw {
public:
  Coverage_uexecs(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=true;
    af=false;
  }
  virtual ~Coverage_uexecs() {}
};

class Coverage_upaths: public Coverage_pathsw {
public:
  Coverage_upaths(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=true;
  }
  virtual ~Coverage_upaths() {}
};

class Coverage_uwalks: public Coverage_pathsw {
public:
  Coverage_uwalks(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=false;
  }
  virtual ~Coverage_uwalks() {}
};

class Coverage_uinputswalks: public Coverage_pathsw {
public:
  Coverage_uinputswalks(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=false;
  }
  virtual ~Coverage_uinputswalks() {}
};


class Coverage_inputs: public Coverage_pathsw {
public:
  Coverage_inputs(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=true;
    pf=true;
    af=false;
    unique=false;
  }
  virtual ~Coverage_inputs() {}
};

class Coverage_execs: public Coverage_pathsw {
public:
  Coverage_execs(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=true;
    af=false;
    unique=false;
  }
  virtual ~Coverage_execs() {}
};

class Coverage_paths: public Coverage_pathsw {
public:
  Coverage_paths(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=true;
    unique=false;
  }
  virtual ~Coverage_paths() {}
};

class Coverage_walks: public Coverage_pathsw {
public:
  Coverage_walks(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=false;
    unique=false;
  }
  virtual ~Coverage_walks() {}
};

class Coverage_inputswalks: public Coverage_pathsw {
public:
  Coverage_inputswalks(Log& l,std::string params):
    Coverage_pathsw(l,params) {
    filter_outputs=false;
    pf=false;
    af=false;
    unique=false;
  }
  virtual ~Coverage_inputswalks() {}
};

void Coverage_paths_base::on_restart(int action,std::vector<int>&p) {
  executed.clear();
  if (filter_outputs==false || !model->is_output(action)) {
    if (prop_set(start_action,1,&action)) {
      executed.push_back(std::pair<int,std::vector<int> >(af?0:action,pf?pp:p));
    }
  }
}

void Coverage_paths_base::on_online(int action,std::vector<int>&p){
  if (filter_outputs==false || !model->is_output(action)) {
    executed.push_back(std::pair<int,std::vector<int> >(af?0:action,pf?pp:p));
  }
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_upaths, "upaths" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_uwalks, "uwalks" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_uwalks, "uinputswalks" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_uexecs, "uexecs" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_uinputs,"uinputs")

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_paths, "paths" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_walks, "walks" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_walks, "inputswalks" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_execs, "execs" )
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_inputs,"inputs")
