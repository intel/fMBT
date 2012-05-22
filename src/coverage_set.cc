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

#include "coverage_set.hh"
#include "helper.hh"
#include <string>

#include "dparse.h"

extern std::vector<std::string*> *ff,*tt,*dd;
extern "C" {
  extern D_ParserTables parser_tables_filter;
};

class Coverage_setw: public Coverage_set {
public:
  Coverage_setw(Log& l,std::string params):
    Coverage_set(l,_f,_t,_d) 
  {
    printf("%s\n",params.c_str());
    unescape_string(params);
    printf("%s\n",params.c_str());
    ff=&_f;
    tt=&_t;
    dd=&_d;
    D_Parser *p = new_D_Parser(&parser_tables_filter, 512);
    bool ret=dparse(p,(char*)params.c_str(),std::strlen(params.c_str()));
    ret=p->syntax_errors==0 && ret;
    free_D_Parser(p);

    printf("%i %i %i\n",ff->size(),_f.size(),from.size());

    printf("ret %i\n",ret);
    from=_f;
    to=_t;
    drop=_d;
  }
private:
  std::vector<std::string*> _f,_t,_d;
};

Coverage_set::~Coverage_set()
{
  for(unsigned i=0;i<covs.size();i++) {
    delete covs[i];
  }  
}

bool Coverage_set::execute(int action) {

  Coverage_exec_filter::execute(action);

  if (online) {
    current_set[action]++;
  }

  return true;
}

std::string Coverage_set::stringify()
{
  return std::string("");
}

void Coverage_set::on_drop()
{
  current_set.clear();
}

void Coverage_set::on_start()
{
  current_set.clear();
}

void Coverage_set::on_find()
{
  // Check that set_filter match current_set. I'll implement that later :D
  // Just because set_filter structure is not filled.
  sets[current_set]++;
  current_set.clear();
}

void Coverage_set::set_model(Model* _model) {

  Coverage_exec_filter::set_model(_model);

}

void Coverage_set::push()
{
  Coverage_exec_filter::push();
  save_sets.push_front(sets);
  save_current.push_front(current_set);
}

void Coverage_set::pop()
{
  Coverage_exec_filter::pop();
  sets=save_sets.front();
  save_sets.pop_front();
  current_set=save_current.front();
  save_current.pop_front();
}


FACTORY_DEFAULT_CREATOR(Coverage, Coverage_setw, "set")
