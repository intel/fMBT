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

#include "adapter_xrules.hh"
#include "lts_xrules.hh"
#include "dparse.h"
#include <cstring>
#include "helper.hh"
#include "adapter_remote.hh"

extern "C" {
extern D_ParserTables parser_tables_xrules_extended;
};

extern Adapter_xrules* axobj;

#define debugprint(...)

bool Adapter_xrules::load(std::string& name)
{
  D_Parser *p = new_D_Parser(&parser_tables_xrules_extended, 16);
  char *s;

  valid=false;

  Adapter_xrules* tmp=axobj;

  _res_actions=NULL;
  _res_iactions=NULL;

  root_par.parent=NULL;
  root_par.root_count=&root_par.count;

  axobj=this;

  cur_par=&root_par;

  s=readfile(name.c_str());

  dparse(p,s,std::strlen(s));

  free(s);

  free_D_Parser(p);

  //Implementme
  //precalc_input_output();  

  axobj=tmp;

  return true;
}

void Adapter_xrules::add_file(unsigned index,std::string& filename, std::string& adaptername)
{

  log.debug("Index %i, filename %s\n",index,filename.c_str());
  log.debug("adaptername %s\n",adaptername.c_str());

  if (lts_filenames.capacity()<=index) {
    lts_filenames.resize(index+2);
    adapter_filenames.resize(index+2);
    lts.resize(index+2);
    adapters.resize(index+2); 
 }

  debugprint("Index %i, size %i, file %s\n",
	 index,lts_filenames.capacity(),filename.c_str());
  
  
  lts_filenames[index]=std::string(filename);

  if (isxrules(filename)) {
    lts[index]=new Lts_xrules();
  } else {
    lts[index]=new Lts();
  }

  adapter_filenames[index]=std::string(adaptername);
  lts[index]->load(filename);

  std::vector<std::string> s;
  log.debug("lts[%i]==%p\n",index,lts[index]);
  Adapter* a=new Adapter_remote(lts[index]->
				getActionNames());
  
  adapters[index]=a;
}

/*
 * Adds result action (We'll assume that there are at lest one
 * component)
 *
 */
void Adapter_xrules::add_result_action(std::string* name)
{
  int action=action_number(*name);

  /* action_number returns negative, if the name is unknown */

  if (action<0) {
    if (action_names.size()==0) {
      /* Yeah.. Let's insert the tau.. */
      std::string n("tau");
      action_names.push_back(n);
    }
    action_names.push_back(*name);
    action=action_number(*name);
  }

  /*
   * Push action to current node result...
   */

  cur_par->actions.push_back(action);
  
  debugprint("%p added result %s (%i)\n",cur_par,name->c_str(),
	 cur_par->actions.size());
  
  //res_nodes.resize(action_names.size()+2);

  cur_par=&root_par;  /* Start from begin.. */
}

void Adapter_xrules::add_component(int index,std::string& name)
{
  /* Validate index */

  if (index>=lts_filenames.size() || lts[index]==NULL) {
    throw((int)420);
  }

  int anum=lts[index]->action_number(name);

  if (anum<0) {
    debugprint("anum %s -> %i\n",name.c_str(),anum);
    throw((int)4200);
  }

  comp pos(index,anum);

  struct par* pa=cur_par->vmap[pos];
  
  if (pa==NULL) {
    debugprint("New combination <%i,%s>\n",
	   index,name.c_str());
    pa = new struct par(cur_par);

    pa->me=pos;
    
    debugprint("%p: vmap size %i:",cur_par,cur_par->vmap.size());
    cur_par->vmap[pos]=pa;
    debugprint("vmap size %i\n",cur_par->vmap.size());

    bob.insert(std::pair<comp,par*>(pos,pa));

  }
  
  cur_par = pa;
}

void Adapter_xrules::print_root_par()
{
  print_par(&root_par);
}

int  Adapter_xrules::execute(int action) 
{
  /* Output Actions for each component */

  for(size_t i=0;i<adapters.size();i++) {
    log.debug("adapters[%i] == %p\n",
	   i,adapters[i]);
    if (adapters[i]) {
      int action=0;
      if (adapters[i]->readAction(action,false)) {
	/* Ok. Let's feed the action to the composer */
	log.debug("got action %i\n",action);
      } else {
	log.debug("No action...\n");
      }
    }
  }

  valid=false;

  /* Ok. Now we need to check which input actions
     (per component) are available for this action */

  

  compose();
  /* For each component, call execute */

  struct par* pa=NULL; // res_nodes[action];

  if (pa==NULL) {
    return false;
  }

  while (pa->parent!=NULL) {
    lts[pa->me.first]->execute(pa->me.second);
  }

  valid=false;
  
  return true; 
}

bool Adapter_xrules::reset()
{
  for(int i=lts.size()-1;i>=0;i--) {
    if (lts[i]) {
      lts[i]->reset();
    }
  }
  
  return true;
}

void Adapter_xrules::print_par(struct par* pa)
{
  debugprint("%p:actions count %i\n"
	 "vmap size %i\n",
	 pa,
	 (int)pa->actions.size(),
	 (int)pa->vmap.size());

  std::map<comp, struct par*>::iterator p;  
  
  for(p = pa->vmap.begin(); p!=pa->vmap.end(); ++p) {
    print_par(p->second);
  }
}

int Adapter_xrules::getActions(int** actions)
{ // vireessä olevat tapahtumat
  compose();

  if (_res_actions) {
    delete [] _res_actions;
  }

  _res_actions = new int[(res_actions.size())];

  *actions=_res_actions;

  for(size_t i=0;i<res_actions.size();i++) {
    _res_actions[i]=res_actions[i];
    debugprint("%i ",res_actions[i]);
  }

  debugprint("Actions.size() %i\n",res_actions.size());
  
  return res_actions.size();
}

int Adapter_xrules::getIActions(int** actions)
{ // Vireessä olevat syöte tapahtumat. NULL ja 0 == DEADLOCK.
  compose();

  if (_res_iactions) {
    delete [] _res_iactions;
  }

  _res_iactions = new int[(res_iactions.size())];

  *actions=_res_iactions;

  for(size_t i=0;i<res_iactions.size();i++) {
    _res_iactions[i]=res_iactions[i];
    debugprint("%i ",res_iactions[i]);
  }

  debugprint("iActions.size %i\n",res_iactions.size());


  return res_iactions.size();
}

void Adapter_xrules::compose()
{

  debugprint("Adapter_xrules::compose()\n");

  if (valid) {
    /* No need to compose again.. */
    return;
  }
  
  root_par.count++;

  active_root=NULL;
  
  /* paint struct par with available actions */

  for(int i=lts.size()-1;i>=0;i--) {
    if (lts[i]!=NULL) {
      /* We have something to do.. */
      int* actions;
      int number_of_actions =
	lts[i]->getActions(&actions);
      
      for(int j=0;j<number_of_actions;j++) {
	comp pos(i,actions[j]);

	std::pair<std::multimap<comp,struct par*>::iterator,
	  std::multimap<comp,struct par*>::iterator> r =
	  bob.equal_range(pos);
	std::multimap<comp,struct par*>::iterator it;
	for (it=r.first; it!=r.second; ++it) {
	  it->second->count=root_par.count; /* We are valid */
	  if (it->second->actions.size()) {
	    it->second->active_next=active_root;
	    active_root=it->second;
	  }
	}
      }
    }
  }

  /* Let's check... */ 

  res_actions.clear();
  res_iactions.clear();
  res_nodes.clear();

  /* results */
  /* Travel through every active node */
  for(struct par* a=active_root;a;a=a->active_next) {
    if (parent_active_par(a)) {
      /* Add actions from par */
      res_actions.insert(res_actions.end(),a->actions.begin(),a->actions.end());
      for(size_t i=0;i<a->actions.size();i++) {
	// res_nodes[a->actions[i]]=a;
	if (!is_output(a->actions[i])) {
	  res_iactions.push_back(a->actions[i]);
	}
      }
    }
  }
  valid=true;
}

bool Adapter_xrules::readAction(int &action,bool block)
{
  // implementme
  return false;
}


bool Adapter_xrules::parent_active_par(struct par* par)
{
  if (par==&root_par) {
    return true;
  }

  if (par->added_count==*root_par.root_count) {
    return true;
  }
  
  if (par->count<root_par.count) {
    return false;
  }
  
  bool ret=parent_active_par(par->parent);
  if (ret) {
    par->added_count=*root_par.root_count;
    
  }
  return ret;
}

namespace {
  Adapter* adapter_creator(std::vector<std::string>& _actions,
			   std::string params) {
    return new Adapter_dummy(_actions);
  }
  static adapter_factory adapter_foo("mapper",adapter_creator);
};
