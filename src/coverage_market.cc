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

Coverage_Market::Coverage_Market(Log& l, std::string& params) :
    Coverage(l)
{
    add_requirement(params);
}

bool Coverage_Market::execute(int action)
{
  /* Dummy */

  for(size_t i=0;i<Units.size();i++) {
    Units[i]->execute(action);
  }

  return true;
}


float Coverage_Market::getCoverage()
{
  val v,tmp;
  
  v.first=0;
  v.second=0;

  for(size_t i=0;i<Units.size();i++) {
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
      Units[j]->execute(action[i]);
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
};

extern Coverage_Market* cobj;

void Coverage_Market::add_requirement(std::string& req)
{  
  cobj=this;
  D_Parser *p = new_D_Parser(&parser_tables_covlang, 32);
  dparse(p,(char*)req.c_str(),req.length());
  free_D_Parser(p);
}

Coverage_Market::unit* Coverage_Market::req_rx_action(const char m,const char* action) {
  /* m(ode) == a|e */
  std::vector<std::string> &names(model->getActionNames());
  regex_t rx;

  Coverage_Market::unit* u=NULL;

  if (m) {
    if (regcomp(&rx,action,0)) {
      log.debug("Something went wrong with RexExp\n");
      abort();
    }
    
    for(size_t i=0;i<names.size();i++) {
      
      if (regexec(&rx,names[i].c_str(),0,0,0)==0) {
	/* Match */
	/*
	log.debug("RegExp \"%s\" matched to str \"%s\"\n",
	       action,names[i].c_str());
	*/
	if (u) {
	  if (m=='e') {
	    u=new Coverage_Market::unit_or(u,new Coverage_Market::unit_leaf(i));
	  } else {
	    u=new Coverage_Market::unit_and(u,new Coverage_Market::unit_leaf(i));	  
	  }
	} else {
	  u=new Coverage_Market::unit_leaf(i);
	}
      }
    }
    regfree(&rx);
  } else {
    std::string s(action);
    int an = model->action_number(s);
    if (an<=0) {
      throw((int)42000);
    }
    u = new Coverage_Market::unit_leaf(an);
  }

  if (u==NULL) {
    throw((int)42001);
  }

  return u;  
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Market, "covlang");
