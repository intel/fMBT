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

std::string Coverage_Market::stringify()
{
  if (!status) {
    return Writable::stringify();
  }
  std::string ret="usecase(";
  for(size_t i=0;i<Units.size();i++) {
    ret+=" "+Units[i]->stringify(*model);
  }
  ret+=")";
  return ret;
}

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
  if (j) {
    next.assign(p,p+j);
  } else {
    next.clear();
  }

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

#include <set>

void taghelper(const char op,int depth,
	       int start_pos,
	       Coverage_Market::unit_tag*& tu,
	       std::vector<std::pair<Coverage_Market::unit_tag*, bool> >& uset,
	       bool exactly) {

  if (depth==0) {
    Coverage_Market::unit_tag* u=NULL;

    for(unsigned i=0;i<uset.size();i++) {
      if (uset[i].second || exactly) {
	Coverage_Market::unit_tag* u2=(Coverage_Market::unit_tag*)uset[i].first->clone();

	if (!uset[i].second) {
	  u2=new Coverage_Market::unit_tagnot(u2);
	}

	if (u) {
	  u=new Coverage_Market::unit_tagand(u,u2);
	} else {
	  u=u2;
	}
      }
    }
    if (tu) {
      tu=new Coverage_Market::unit_tagelist(op,tu,u);
    } else {
      tu=u;
    }
  } else {
    for(unsigned i=start_pos;i<uset.size();i++) {
      uset[i].second=true;
      taghelper(op,depth-1,i+1,tu,uset,exactly);
      uset[i].second=false;
    }
  }
}

Coverage_Market::unit_tag* Coverage_Market::req_rx_tag(const char m,const std::string &tag,int count,bool exactly)
{
  if (!status) {
    return new Coverage_Market::unit_tagleaf(0);
  }

  char op='&';

  std::vector<int> tags;
  regexpmatch(tag, model->getSPNames(),tags  , false,1,1);

  if (tags.empty()) {
    errormsg = "No tags matching \"" + tag + "\"";
    status = false;
    return new Coverage_Market::unit_tagleaf(0);
  }

  if (m=='e') {
    op='|';
  }

  //std::set<Coverage_Market::unit_tag*> uset;
  std::vector<std::pair<Coverage_Market::unit_tag*, bool> > uset;

  for(unsigned i=0;i<tags.size();i++) {
    Coverage_Market::unit_tag* u2=new Coverage_Market::unit_tagleaf(tags[i]);
    uset.push_back(std::pair<Coverage_Market::unit_tag*, bool>(u2,false));
  }


  Coverage_Market::unit_tag* u=NULL;

  taghelper(op,count,0,u,uset,exactly);

  if (u==NULL) {
    abort();
  }

  return u;

  /*
  for(unsigned i=1;i<tags.size();i++) {
    Coverage_Market::unit_tag* u2=new Coverage_Market::unit_tagleaf(tags[i]);
    u=new Coverage_Market::unit_tagelist(op,u,u2);
  }

  return u;
  */
}

Coverage_Market::unit_tag* Coverage_Market::req_rx_tag(const std::string &tag,char op) {
  if (!status) {
    return new Coverage_Market::unit_tagleaf(0);
  }

  std::vector<int> tags;
  regexpmatch(tag, model->getSPNames(),tags  , false,1,1);

  if (tags.empty()) {
    errormsg = "No tags matching \"" + tag + "\"";
    status = false;
    return NULL;
  }

  Coverage_Market::unit_tag* u=new Coverage_Market::unit_tagleaf(tags[0]);

  for(unsigned i=1;i<tags.size();i++) {
      Coverage_Market::unit_tag* u2=new Coverage_Market::unit_tagleaf(tags[i]);
    switch(op) {
    case 'e':
      u=new Coverage_Market::unit_tagor(u,u2);
      break;
    case 'a':
      u=new Coverage_Market::unit_tagand(u,u2);
      break;
    default:
      abort();
    }
  }

  return u;
}

Coverage_Market::unit* Coverage_Market::req_rx_action(const char m,const std::string &action,
						      unit_tag* prev_tag,
						      unit_tag* next_tag,
						      int persistent) {
  /* m(ode) == a|e|r
     a(ll): cover all matching actions
     e(xists): cover any of matching actions
     r(andom): randomly choose an action from set of actions
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
      next_tag->set_left(false);
      prev_tag->set_left(true);
    }

    if (actions.size()==1) {
      u=new Coverage_Market::unit_leaf(actions[0]);
   } else {
	for(unsigned int i=0; i < actions.size(); i++) {
	  if (!u) {
	    switch (m) {
	    case 'r': // Random
	      u=new Coverage_Market::unit_manyleafrandom();	      
	      break;
	    case 'e': // Exists
	      u=new Coverage_Market::unit_manyleafor();
	      break;
	    case 'a': // All
	      u=new Coverage_Market::unit_manyleafand();
	      break;
	    default:
	      abort();
	    }
	  }
	  ((unit_manyleaf*)u)->my_action.push_back(actions[i]);
	  ((unit_manyleaf*)u)->value    .push_back(0);
	  u->value.second++;
	}
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
    u=new_unit_tagunit(prev_tag,u,next_tag,persistent);
  }

  return u;
}

Coverage_Market::unit* new_unit_tagunit(Coverage_Market::unit_tag* l,
					Coverage_Market::unit* u,
					Coverage_Market::unit_tag* r,
					int persistent) {
  l->set_left(true);
  r->set_left(false);

  Coverage_Market::unit_tagelist* tl=dynamic_cast<Coverage_Market::unit_tagelist*>(l);


  // copy-constructor for unit*. We need to make a deep copy to get this thing working.

  if (tl) {
    // We have operator on the left side. Let's expand it a bit.
    Coverage_Market::unit_tag* nl=tl->left;
    Coverage_Market::unit_tag* nr=tl->right;

    Coverage_Market::unit* ul = new_unit_tagunit(nl,u->clone(),
						 (Coverage_Market::unit_tag*)r->clone(),
						 persistent);
    Coverage_Market::unit* ur = new_unit_tagunit(nr,u,r,persistent);

    if (tl->op=='&') {
      delete tl;
      // and
      return new Coverage_Market::unit_and(ul,ur);
    } else {
      delete tl;
      // or
      return new Coverage_Market::unit_or(ul,ur);
    }
  } else {
    // Ok. Let's check if right hand side needs expanding.
    Coverage_Market::unit_tagelist* tl=dynamic_cast<Coverage_Market::unit_tagelist*>(r);
    if (tl) {
      // We have operator on the right side. Let's expand it a bit.
      Coverage_Market::unit_tag* nl=tl->left;
      Coverage_Market::unit_tag* nr=tl->right;

      Coverage_Market::unit* ul = new_unit_tagunit((Coverage_Market::unit_tag*)l->clone(),
						   u->clone(),nl,persistent);
      Coverage_Market::unit* ur = new_unit_tagunit(l,u,nr,persistent);

      if (tl->op=='&') {
	delete tl;
	// and
	return new Coverage_Market::unit_and(ul,ur);
      } else {
	delete tl;
	// or
	return new Coverage_Market::unit_or(ul,ur);
      }
    } else {
      // No need to expand.
      return new Coverage_Market::unit_tagunit(l,u,r,persistent);
    }
  }
}

Coverage_Market::unit_dual::unit_dual(Coverage_Market::unit_dual const& obj):
  Coverage_Market::unit(obj) {
  if (obj.left)
    left=obj.left->clone();
  else
    left=NULL;

  if (obj.right)
    right=obj.right->clone();
  else
    right=NULL;
}

Coverage_Market::unit_not::unit_not(Coverage_Market::unit_not const& obj):
  Coverage_Market::unit(obj) {
  if (obj.child)
    child=obj.child->clone();
  else
    child=NULL;
}

Coverage_Market::unit_tagelist::unit_tagelist(Coverage_Market::unit_tagelist const& obj):
  Coverage_Market::unit_tag(obj),op(obj.op) {
  if (obj.left)
    left=(unit_tag*)obj.left->clone();
  else
    left=NULL;

  if (obj.right)
    right=(unit_tag*)obj.right->clone();
  else
    right=NULL;
}

Coverage_Market::unit_tagnot::unit_tagnot(Coverage_Market::unit_tagnot const& obj):
  unit_tag(obj) {
  if (obj.child)
    child=(unit_tag*)obj.child->clone();
  else
    child=NULL;
 }

Coverage_Market::unit_tagdual::unit_tagdual(Coverage_Market::unit_tagdual const& obj):
  unit_tag(obj) {
  if (obj.left)
    left=(unit_tag*)obj.left->clone();
  else
    left=NULL;

  if (obj.right)
    right=(unit_tag*)obj.right->clone();
  else
    right=NULL;
}

Coverage_Market::unit_tagunit::unit_tagunit(Coverage_Market::unit_tagunit const& obj):
  unit_tagdual(obj),persistent(obj.persistent) {
  if (obj.child)
    child=obj.child->clone();
  else
    child=NULL;
}

Coverage_Market::unit_mult::unit_mult(Coverage_Market::unit_mult const& obj):
  unit(obj),max(obj.max),count(obj.count) {
  if (obj.child)
    child=obj.child->clone();
  else
    child=NULL;
}

Coverage_Market::unit_many::unit_many(const unit_many &obj):
  unit(obj) {
  for(unsigned i=0;i<obj.units.size();i++) {
    unit* u=obj.units[i];
    if (u)
      u=u->clone();
    units.push_back(u);
  }
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Market, "usecase")
