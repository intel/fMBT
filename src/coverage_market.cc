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

#include "coverage_market.hh"
#include "model.hh"
#include "helper.hh"

Coverage_Market::Coverage_Market(Log& l,const std::string& _params) :
    Coverage(l)
{
  params = _params;
  remove_force(params);
}

void Coverage_Market::history(int action,
			      std::vector<int>& props,
			      Verdict::Verdict verdict)
{
  if (action) {
    execute(action);
  } else {
    // verdict
    // Ok. We'll need to init the system.
  }
}

bool Coverage_Market::execute(int action)
{
  /* Dummy */
  
  int* p;
  int j=model->getprops(&p);
  next.assign(p,p+j);
  
  
  for(size_t i=0;i<Units.size();i++) {
    Units[i]->execute(prev,action,next);
  }
  
  prev.swap(next);
  
  return true;
}

float Coverage_Market::getCoverage()
{
  val v,tmp;

  v.first=0;
  v.second=0;

  for(size_t i=0;i<Units.size();i++) {
    Units[i]->update();
    tmp=Units[i]->get_value();
    v.first+=tmp.first;
    v.second+=tmp.second;
  }

  if (v.second) {
    return ((float)v.first)/((float)v.second);
  }

  return 0;
}

int Coverage_Market::fitness(int* action,int n,float* fitness)
{
  float m=-1;
  int pos=-1;

  for(int i=0;i<n;i++) {
    val b(0,0);
    val e(0,0);
    val tmp;
    log.debug("%s:%i\n",__func__,i);
    for(size_t j=0;j<Units.size();j++) {
      log.debug("%s:%i,%i (%i)\n",__func__,i,j,action[i]);
      Units[j]->update();
      tmp=Units[j]->get_value();
      b.first+=tmp.first;
      b.second+=tmp.second;
      Units[j]->push();
      Units[j]->execute(prev,action[i],next);
      Units[j]->update();
      tmp=Units[j]->get_value();
      e.first+=tmp.first;
      e.second+=tmp.second;
      Units[j]->pop();
      Units[j]->update();
    }
    log.debug("(%i:%i) (%i:%i)\n",b.first,b.second,
	   e.first,e.second);
    if (b.second) {
      fitness[i]=((float)(e.first-b.first))/((float)(b.second));
    } else {
      fitness[i]=0.0;
    }
    if (m<fitness[i]) {
      pos=i;
      m=fitness[i];
    }
  }

  return pos;
}

#include "dparse.h"
extern "C" {
extern D_ParserTables parser_tables_covlang;
}

extern Coverage_Market* cobj;

void Coverage_Market::add_requirement(std::string& req)
{
  cobj=this;
  D_Parser *p = new_D_Parser(&parser_tables_covlang, 32);
  D_ParseNode* ret=dparse(p,(char*)req.c_str(),req.length());
  status&=p->syntax_errors==0;

  if (ret) {
    free_D_ParseNode(p, ret);
  }
  free_D_Parser(p);
}

Coverage_Market::unit_tag* Coverage_Market::req_rx_tag(const std::string &tag) {
  if (!status) {
    return NULL;
  }

  std::vector<int> tags;
  regexpmatch(tag, model->getSPNames(),tags  , false,1,1);  
  
  if (tags.empty()) {
    errormsg = "No actions matching \"" + tag + "\"";
    status = false;
    return NULL;
  }

  //if (tags.size()==1) {
    return new Coverage_Market::unit_tagleaf(tags[0]);
    //  }
  
  errormsg = "Regexp matched to more than one tag which is not supported!";
  status=false;
  return NULL;
}

Coverage_Market::unit* Coverage_Market::req_rx_action(const char m,const std::string &action,
						      unit_tag* prev_tag,
						      unit_tag* next_tag) {
  /* m(ode) == a|e
     a(ll): cover all matching actions
     e(xists): cover any of matching actions
  */
  if (!status) {
    return NULL;
  }
  Coverage_Market::unit* u=NULL;

  if (m) {
    std::vector<int> actions;
    regexpmatch(action, model->getActionNames(), actions  , false,1,1);

    if (actions.empty()) {
      errormsg = "No actions matching \"" + action + "\"";
      status = false;
      return NULL;
    }

    if (next_tag) {
      next_tag->set_left(false);
    }

    if (prev_tag||next_tag) {
      if (!prev_tag) {
	prev_tag=new unit_tag();
	prev_tag->value.first=0;
	prev_tag->value.second=0;
      }
      if (!next_tag) {
	next_tag=new unit_tag();
	next_tag->value.first=0;
	next_tag->value.second=0;
      }
    }

    if (actions.size()==1) {
      u=new Coverage_Market::unit_leaf(actions[0]); 
   } /*else {
      if (actions.size()==2) {
	Coverage_Market::unit *l,*r;
	l=new Coverage_Market::unit_leaf(actions[0]);
	r=new Coverage_Market::unit_leaf(actions[1]);
	if (m=='e') {
	  u=new Coverage_Market::unit_or(l,r);
	} else {
	  u=new Coverage_Market::unit_and(l,r);	  
	}
	} */else {
	for(unsigned int i=0; i < actions.size(); i++) {
	  if (!u) {
	    if (m=='e') {
	      u=new Coverage_Market::unit_manyleafor();
	    } else {
	      u=new Coverage_Market::unit_manyleafand();
	    }
	  }
	  ((unit_manyleaf*)u)->my_action.push_back(actions[i]);
	  ((unit_manyleaf*)u)->value    .push_back(0);
	  u->value.second++;
	}
	/*      }*/
    }
  } else {
    int an = model->action_number(action.c_str());
    if (an<=0) {
      errormsg="No such action \"" + action + "\"";
      status=false;
      u = new Coverage_Market::unit_leaf(0);
    } else {
      u = new Coverage_Market::unit_leaf(an);
    }
  }

  if (u==NULL) {
    errormsg=std::string("parse error");
    status=false;
  }

  if (u && status && prev_tag) {
    u=new Coverage_Market::unit_tagunit(prev_tag,u,next_tag);
  }

  return u;
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Market, "usecase")
