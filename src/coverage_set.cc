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
#include <cstring>

#include "dparse.h"
#include "model.hh"

extern std::vector<std::string*> *set_ff,*set_tt,*set_dd;
extern std::vector<std::pair<std::string*,std::pair<int,int> > >* filtervec;
extern std::pair<int,int>* asize;
extern int* mcount;

extern "C" {
  extern D_ParserTables parser_tables_set;
}

class Coverage_setw: public Coverage_set {
public:
  Coverage_setw(Log& l,std::string params):
    Coverage_set(l,_f,_t,_d)
  {
    unescape_string(params);
    set_ff=&_f;
    set_tt=&_t;
    set_dd=&_d;
    filtervec = &_fv;
    asize=&allowed_set_size;
    mcount=&max_count;
    D_Parser *p = new_D_Parser(&parser_tables_set, 512);
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
private:
  std::vector<std::string*> _f,_t,_d;
};

Coverage_set::~Coverage_set()
{
  for(unsigned i=0;i<covs.size();i++) {
    delete covs[i];
  }  
}

void Coverage_set::add_filter()
{
  for(unsigned i=0;i<_fv.size();i++) {
    std::vector<int> r;
    regexpmatch(*_fv[i].first,model->getActionNames(),r);
    regexpmatch(*_fv[i].first,model->getSPNames(),r,false,-1);
    // Free some memory...
    delete _fv[i].first;

    for(unsigned u=0;u<r.size();u++) {
      if (set_filter.find(r[u])==set_filter.end()) {
	int a=r[u];
	action_alphabet[a]=true;
	set_filter[a]=_fv[i].second;
      }
    }
  }
  _fv.clear();
}

float Coverage_set::getCoverage()
{
  return (float)current_count / (float)total_count;
}

bool Coverage_set::execute(int action) {

  Coverage_exec_filter::execute(action);

  if (online) {
    int* props,n;
    if (action_alphabet[action]) {
      current_set[action]++;
    }
    // Iterate stateprops
    n=model->getprops(&props);
    for(int i=0;i<n;i++) {
      int pro=-props[i];
      if (action_alphabet[pro]) {
	current_set[pro]++;
      }
    }
  }

  return true;
}

std::string Coverage_set::stringify()
{
  return std::string("");
}

void Coverage_set::on_drop()
{
  log.debug("on_drop called\n");
  current_set.clear();
}

void Coverage_set::on_start()
{
  log.debug("on_start called\n");
  current_set.clear();
}

bool Coverage_set::range(int count,std::pair<int,int>& requirement)
{
  if (requirement.first<=count && requirement.second>=count) {
    return true;
  }

  return false;
}

bool Coverage_set::filter()
{

  // check max_count
  if (max_count>0 && sets[current_set]==max_count) 
    return false;

  // Check current_set size....

  int set_size=0;
  // Check that everything in the current_set belongs to our filter.
  for(std::map<int,int>::iterator i=current_set.begin();
      i!=current_set.end();i++) {
    int action=i->first;
    int count=i->second;
    set_size+=count;
    if (!range(count,set_filter[action])) {
      return false;
    }
  }

  if (!range(set_size,allowed_set_size)) {
    return false;
  }

  // Check that every rule is covered
  for(std::map<int,std::pair<int, int> >::iterator i=set_filter.begin();
      i!=set_filter.end();i++) {

    if (!range(current_set[i->first],i->second)) {
      return false;
    }    
  }

  // Now we know that there aren't too many current_sets, 
  // current_set belongs to set_filter and set_filter belongs to current_set.
  // So let's return true :)
  return true;
}

void Coverage_set::on_find()
{
  log.debug("on_find called %i %i\n",current_count,(int)sets.size());
  // Check that set_filter match current_set. I'll implement that later :D
  // Just because set_filter structure is not filled.
  if (filter()) {
    sets[current_set]++;
    current_count++;
    if (save_current_count.empty()) {
      log.debug("current_count %i\n",current_count);
    }
    if (current_count!=(int)sets.size()) {
      int tc=0;
      for(std::map<std::map<int,int>,int >::iterator i=
	    sets.begin();i!=sets.end();i++) {
	log.debug("set ");

	for(std::map<int,int>::const_iterator j=
	      i->first.begin();
	    j!=i->first.end();j++) {
	  log.debug("(%i:%i)",j->first,j->second);
	}

	log.debug(": count %i\n",i->second);
	tc+=i->second;
      }
      if (tc!=current_count) {
	abort();
      }
    }
  }
  log.debug("%i/%i\n",current_count,total_count);
  current_set.clear();
}

void Coverage_set::set_model(Model* _model) {

  Coverage_exec_filter::set_model(_model);

  if (status) {
    add_filter();
    if (allowed_set_size.second==-1) {
      // Ok. Let's calc this.
      allowed_set_size.second=set_filter.size();
    }
    total_count=(allowed_set_size.second-allowed_set_size.first+1)*max_count;
    log.debug("total_count %i\n",total_count);
  }
  
}

void Coverage_set::push()
{
  Coverage_exec_filter::push();
  save_sets.push_front(sets);
  save_current.push_front(current_set);
  save_current_count.push_front(current_count);
  log.debug("push sets_size %i %i\n",current_count,(int)sets.size());
}

void Coverage_set::pop()
{
  Coverage_exec_filter::pop();
  sets=save_sets.front();
  save_sets.pop_front();
  current_set=save_current.front();
  save_current.pop_front();

  current_count=save_current_count.front();
  save_current_count.pop_front();

  log.debug("pop sets_size %i %i\n",current_count,sets.size());
}


FACTORY_DEFAULT_CREATOR(Coverage, Coverage_setw, "set")
