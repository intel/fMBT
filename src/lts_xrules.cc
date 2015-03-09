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

#include "lts_xrules.hh"
#include "dparse.h"
#include <cstring>
#include "helper.hh"
#include "factory.hh"
#include <sstream>

extern "C" {
extern D_ParserTables parser_tables_xrules;
}

extern Lts_xrules* xobj;

std::string Lts_xrules::stringify()
{
  if (!status) {
    return Writable::stringify();
  }
  std::ostringstream t(std::ios::out | std::ios::binary);
  std::string name;
  
  for(unsigned i=1;i<model_names.size();i++) {
    if (lts[i]!=NULL) {
      std::string s=lts[i]->stringify();

      t << i << " = \"" << removehash(model_names[i])
	<< capsulate(s) << std::endl;
      
    }
  }
  print_par(t,std::string(""),&root_par);
  
  return t.str();
}

void Lts_xrules::prop_create()
{
  if (!status) {
    return;
  }
  if (prop_names.empty()) {
    prop_names.push_back("");
  }
  int count=0;
  for(unsigned i=0;i<lts.size();i++) {
    pzero.push_back(count);
    if (lts[i]) {
      std::vector<std::string>&sn=lts[i]->getSPNames();
      count+=sn.size();
      prop_names.insert(prop_names.end(),sn.begin(),sn.end());
    }
  }
}

extern int xrules_node_size;

bool Lts_xrules::init()
{
  D_Parser *p = new_D_Parser(&parser_tables_xrules, xrules_node_size);
  p->loc.pathname = params.c_str();
  char *s;

  valid=false;

  Lts_xrules* tmp=xobj;

  _res_actions=NULL;
  _res_iactions=NULL;

  root_par.parent=NULL;
  root_par.root_count=&root_par.count;

  xobj=this;

  cur_par=&root_par;

  s=readfile(params.c_str());

  bool ret=dparse(p,s,std::strlen(s));

  ret=p->syntax_errors==0 && ret;

  if (!ret) {
    log.debug("Error in parsing %s\n",params.c_str());
    errormsg = "Parse error in xrules \"" + params + "\"";
    status=false;
  }

  free(s);

  free_D_Parser(p);

  precalc_input_output();

  prop_create();

  xobj=tmp;

  return ret && status;
}

void Lts_xrules::add_file(unsigned int index,std::string& filename)
{
  log.debug("%s(%i,%s)",__PRETTY_FUNCTION__,index,filename.c_str());

  if (!status) {
    return;
  }

  if (model_names.size()<=index) {
    model_names.resize(index+2);
    lts.resize(index+2);
  }

  log.debug("Index %i, size %i, file %s",
	 index,model_names.size(),filename.c_str());
  
  
  model_names[index]=std::string(filename);

  lts[index] = new_model(log,model_names[index]);

  if (!lts[index]) {
    status=false;
    errormsg=std::string("Can't load model ")+filename;
    return;
  }

  if (!lts[index]->status) {
    status=false;
    errormsg="Submodel error"+filename+" "+lts[index]->errormsg;
    return;
  }
  
  if (!lts[index]->init()) {
    status=false;
    errormsg="Failed to init submodel "+filename+" "+lts[index]->errormsg;
    return;
  }

  lts[index]->setparent(this);
}

/*
 * Adds result action (We'll assume that there are at lest one
 * component)
 *
 */
void Lts_xrules::add_result_action(std::string* name)
{
  if (!status) {
    return;
  }

  int action=action_number(*name);

  log.debug("%s(,%s)",__PRETTY_FUNCTION__,name->c_str());
  /* action_number returns negative, if the name is unknown */

  if (action<0) {
    if (action_names.empty()) {
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
  
  log.debug("%p added result %s (%i)\n",cur_par,name->c_str(),
	 cur_par->actions.size());
  
  res_nodes.resize(action_names.size()+2);

  cur_par=&root_par;  /* Start from begin.. */
}

void Lts_xrules::add_component(unsigned int index,std::string& name)
{
  if (!status) {
    return;
  }
  /* Validate index */

  log.debug("%s(%i,%s)",__PRETTY_FUNCTION__,index,name.c_str());

  if (index>=model_names.size() || lts[index]==NULL) {
    errormsg=std::string("rule name with invalid number (")+to_string(index)+std::string(")");
    status=false;
    return;
  }

  int anum=lts[index]->action_number(name);

  if (anum<0) {
    errormsg=std::string("xrules name \"")+name+std::string("\" doesn't belong to alphabet");
    status=false;
    return;
  }

  comp pos(index,anum);

  struct par* pa=cur_par->vmap[pos];
  
  if (pa==NULL) {
    log.debug("New combination <%i,%s>\n",
	   index,name.c_str());
    pa = new struct par(cur_par);

    pa->me=pos;
    
    log.debug("%p: vmap size %i:",cur_par,cur_par->vmap.size());
    cur_par->vmap[pos]=pa;
    log.debug("vmap size %i\n",cur_par->vmap.size());

    bob.insert(std::pair<comp,par*>(pos,pa));

  }
  
  cur_par = pa;
}

void Lts_xrules::print_root_par()
{
  if (!status) {
    return;
  }
  print_par(&root_par);
}

int  Lts_xrules::execute(int action) 
{
  compose();
  /* For each component, call execute */

  struct par* pa=res_nodes[action];

  if (pa==NULL) {
    return false;
  }

  while (pa->parent!=NULL) {
    lts[pa->me.first]->execute(pa->me.second);
    pa=pa->parent;
  }

  valid=false;
  
  return true; 
}

int Lts_xrules::getprops(int** props) {
  int count=0;

  for(unsigned i=0;i<lts.size();i++) {
    if (lts[i]) {
      int* tmp;
      int tmp_count=lts[i]->getprops(&tmp);
      if (tmp_count) {
	for(int j=0;j<tmp_count;j++) {
	  tprops.push_back(tmp[j]+pzero[i]);
	}
      }
      count+=tmp_count;
    }
  }

  if (count) {
    *props=&(tprops[0]);
  }
      
  return count;
}

void Lts_xrules::push()
{
  for(unsigned i=0;i<lts.size();i++) {
    if (lts[i]) {
      lts[i]->push();
    }
  }
}

void Lts_xrules::pop()
{
  for(unsigned i=0;i<lts.size();i++) {
    if (lts[i]) {
      lts[i]->pop();
    }
  }
  valid=false;
  compose();
}

bool Lts_xrules::reset()
{
  for(int i=lts.size()-1;i>=0;i--) {
    if (lts[i]) {
      lts[i]->reset();
    }
  }
  
  return true;
}

void Lts_xrules::print_par(std::ostringstream& t,
			   std::string name,
			   struct par* pa)
{
  if (lts[pa->me.first]) {
    std::ostringstream s;
    s << "(" << pa->me.first << ", \"" 
      << lts[pa->me.first]->getActionName(pa->me.second)
      << "\") ";
    name+=s.str();
  }
  
  for(unsigned i=0;i<pa->actions.size();i++) {
    t << name << "-> \"" << getActionName(pa->actions[i])
      << "\"" << std::endl;
  }

  std::map<comp, struct par*>::iterator p;

  for(p = pa->vmap.begin(); p!=pa->vmap.end(); ++p) {
    print_par(t,name,p->second);
  }

}

void Lts_xrules::print_par(struct par* pa)
{
  log.debug("%p:actions count %i\n"
	 "vmap size %i\n",
	 pa,
	 (int)pa->actions.size(),
	 (int)pa->vmap.size());

  std::map<comp, struct par*>::iterator p;  
  
  for(p = pa->vmap.begin(); p!=pa->vmap.end(); ++p) {
    print_par(p->second);
  }
}

int Lts_xrules::getActions(int** actions)
{ // vireessä olevat tapahtumat
  compose();

  if (_res_actions) {
    delete [] _res_actions;
  }

  _res_actions = new int[(res_actions.size())];

  *actions=_res_actions;

  for(size_t i=0;i<res_actions.size();i++) {
    _res_actions[i]=res_actions[i];
    log.debug("%i ",res_actions[i]);
  }

  log.debug("Actions.size() %i\n",res_actions.size());
  
  return res_actions.size();
}

int Lts_xrules::getIActions(int** actions)
{ // Vireessä olevat syöte tapahtumat. NULL ja 0 == DEADLOCK.
  compose();

  if (_res_iactions) {
    delete [] _res_iactions;
  }

  _res_iactions = new int[(res_iactions.size())];

  *actions=_res_iactions;

  for(size_t i=0;i<res_iactions.size();i++) {
    _res_iactions[i]=res_iactions[i];
    log.debug("%i ",res_iactions[i]);
  }

  log.debug("iActions.size %i\n",res_iactions.size());


  return res_iactions.size();
}

void Lts_xrules::compose()
{

  log.debug("Lts_xrules::compose()\n");

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
  res_nodes.assign(res_nodes.size(), NULL);

  /* results */
  /* Travel through every active node */
  for(struct par* a=active_root;a;a=a->active_next) {
    if (parent_active_par(a)) {
      /* Add actions from par */
      res_actions.insert(res_actions.end(),a->actions.begin(),a->actions.end());
      for(size_t i=0;i<a->actions.size();i++) {
	res_nodes[a->actions[i]]=a;
	if (!is_output(a->actions[i])) {
	  res_iactions.push_back(a->actions[i]);
	}
      }
    }
  }
  valid=true;
}

bool Lts_xrules::parent_active_par(struct par* par)
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

FACTORY_DEFAULT_CREATOR(Model, Lts_xrules, "xrules")
FACTORY_DEFAULT_CREATOR(Model, Lts_xrules, "parallel")
