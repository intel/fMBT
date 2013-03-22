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

#include "coverage_exec_filter.hh"
#include "model.hh"
#include "helper.hh"
#include "history.hh"

std::string Coverage_exec_filter::stringify()
{
  return std::string("");
}

void Coverage_exec_filter::mhandler
(std::vector<std::string>& sp,std::vector<std::string>& n,
 std::vector<std::string*>& from,std::vector<int>& act,
 std::vector<int>& tag)
{
  for(unsigned i=0;i<from.size();i++) {
    // uneascape 
    remove_force(*from[i]);

    int pos=find(sp,*from[i],-1);
    if (pos<0) {
      pos=model->action_number(*(from[i]));
      if (pos>0) {
	act.push_back(pos);
      } else {
	std::vector<int> r;	
	regexpmatch(*(from[i]),sp,r,false);
	if (!r.empty()) {
	  // Let's dump to actions...
	  tag.insert(tag.begin(),r.begin(),r.end());
	} else {
	  regexpmatch(*(from[i]),n,r,false);
	  if (!r.empty()) {
	    act.insert(act.begin(),r.begin(),r.end());
	  } else {
	    status=false;
	    errormsg=errormsg+"No match for "+from[i]->c_str()+"\n";
	  }	  
	}
      }
    } else {
      tag.push_back(pos);
    }
  }
}

void Coverage_exec_filter::set_model(Model* _model)
{
  Coverage::set_model(_model);

  std::vector<std::string>& sp(model->getSPNames());
  std::vector<std::string>& n(model->getActionNames());

  mhandler(sp,n,from,start_action,start_tag);
  mhandler(sp,n,to,end_action,end_tag);
  mhandler(sp,n,drop,rollback_action,rollback_tag);

  // Let's handle initial tags
  execute(0);
}

bool Coverage_exec_filter::prop_set(std::vector<int> p,int npro,
			       int* props)
{
  for(unsigned i=0;i<p.size();i++) {
    for(int j=0;j<npro;j++) {
      if (p[i]==props[j]) {
	return true;
      }
    }
  }
  return false;
}

void Coverage_exec_filter::on_drop(int action,std::vector<int>&p)
{
  online=false;
  executed.clear();
  etime.clear();
}

void Coverage_exec_filter::on_find(int action,std::vector<int>&p)
{
  online=false;
  executed.clear();
  etime.clear();
}

void Coverage_exec_filter::on_start(int action,std::vector<int>&p)
{
  online=true;
  etime.push_back(History::current_time);

  // Let's init....
  if (prop_set(start_action,1,&action)) {
    on_online(action,p);
  }
}

void Coverage_exec_filter::on_online(int action,std::vector<int>&p) {
  executed.push_back(std::pair<int,std::vector<int> >(action,p));
  etime.push_back(History::current_time);
}

bool Coverage_exec_filter::execute(int action)
{
  int* props=NULL;
  int npro;

  npro=model->getprops(&props);
  std::vector<int> p(props,props+npro);

  if (online) {
    on_online(action,p);
  } else {
    on_offline(action,p);
  }

  if (online) {
    /* Ok. Let's search for drop. */
    if (prop_set(rollback_tag,npro,props) || 
	prop_set(rollback_action,1,&action)) {
      on_drop(action,p);
    } else {
      /* No drop? Let's search for to */
      if (prop_set(end_tag,npro,props) || 
	  prop_set(end_action,1,&action)) {
	on_find(action,p);
      }
    }
  }

  /* Let's search for from */
  if (prop_set(start_tag,npro,props) || 
      prop_set(start_action,1,&action)) {
    if (online) {
      on_restart(action,p);
    } else {
      on_start(action,p);
    }
  }

  return true;
}

void Coverage_exec_filter::ds(std::string* s){
  if (s) 
    delete s;
}

Coverage_exec_filter::~Coverage_exec_filter() {
}

#include "dparse.h"

extern "C" {
  extern D_ParserTables parser_tables_filter;
}

extern std::vector<std::string*> *ff,*tt,*dd;

class Coverage_from: public Coverage_exec_filter {
public:
  Coverage_from(Log& l,std::string params):
    Coverage_exec_filter(l,_f,_t,_d), sub(NULL)
  {
    std::vector<std::string> s;
    commalist(params,s);

    if (s.size()!=2) {
      status=false;
      errormsg="coverage from parse error "+params;
      return;
    }

    sub=new_coverage(log,s[1]);

    if (sub==NULL) {
      status=false;
      errormsg="can't create coverage "+s[1];
    }
    
    if (!sub->status) {
      status=false;
      errormsg=sub->errormsg;
    }

    ff=&_f;
    tt=&_t;
    dd=&_d;
    D_Parser *p = new_D_Parser(&parser_tables_filter, 512);
    remove_force(params);
    bool ret=dparse(p,(char*)params.c_str(),strlen(s[0].c_str()));
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
  virtual ~Coverage_from() {
    if (sub)
      delete sub;      
  }
  virtual void push() {
    if (sub)
      sub->push();
    
    return Coverage_exec_filter::push();
  }

  virtual void pop() {
    if (sub)
      sub->pop();
    
    return Coverage_exec_filter::pop();
  }

  virtual float getCoverage()
  {
    if (sub) 
      return sub->getCoverage();

    return Coverage_exec_filter::getCoverage();
  }

  virtual int fitness(int* actions,int n, float* fitness) { 
    if (sub)
      return sub->fitness(actions,n,fitness);

    return Coverage_exec_filter::fitness(actions,n,fitness);
  }

  virtual void on_online(int action,std::vector<int>&p) {
    if (sub) {
      sub->execute(action);
    }
    Coverage_exec_filter::on_online(action,p);
  }

  virtual void on_start(int action,std::vector<int>&p) {
    Coverage_exec_filter::on_start(action,p);
    if (sub) {
      sub->execute(action);
    }    
  }

  virtual void set_model(Model* _model) {
    Coverage_exec_filter::set_model(_model);    

    if (status && sub) {
      sub->set_model(model);
      if (sub->status==false) {
	status=false;
	errormsg=errormsg+"Sub model failed*:"+sub->errormsg;
      }
    }
  }
private:
  std::vector<std::string*> _f,_t,_d;
  Coverage* sub;
};

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_from, "from")
