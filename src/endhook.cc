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
 * You should have received a copy of the GNU Lesser General Public License alongwith
 * this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.
 *
 */

#include "conf.hh"
#include "endhook.hh"
#include "end_condition.hh"
#include <sstream>
#include <list>

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2
#undef FACTORY_CREATE_PARAMS

class Conf;

#define FACTORY_CREATOR_PARAMS Conf* _c,int _lineno, std::string params
#define FACTORY_CREATOR_PARAMS2 _c, _lineno, params
#define FACTORY_CREATE_PARAMS Conf* _c,int _lineno, std::string name, std::string params

FACTORY_CREATE(EndHook)
FACTORY_DEFAULT_CREATOR(EndHook, EndHookExit, "exit")
FACTORY_DEFAULT_CREATOR(EndHook, EndHookInteractive, "interactive")

FACTORY_CREATORS(EndHook)
FACTORY_ADD_FACTORY(EndHook)

EndHookExit::EndHookExit(Conf* _c,int _lineno,std::string& s): EndHook(_c,s) {
  char* endp;
  std::string name,option;
  param_cut(s,name,option);
  lineno=_lineno;
  if (name=="coverage") {
    cov=new_coverage(c->log,option);
    if (cov==NULL) {
      status=false;
      errormsg="Can't create coverage "+s;
    } else if (!cov->status) {
      status=false;
      errormsg="Error on coverage "+s+": "+cov->errormsg;
    } else {
      End_condition_dummy* ec=new End_condition_dummy(c,Verdict::NOTIFY,"");
      c->set_model(cov);
      ec->c=cov;
      c->add_end_condition(ec);
    }
  } else {
    cov=NULL;
    exit_status=strtol(s.c_str(),&endp,10);
    if (*endp) {
      status=false;
      errormsg="Not an integer "+s;
    }
  }
  if (cov) {
    cov->lineno=lineno;
  }
}


EndHookExit::~EndHookExit() {
  if (cov)
    delete cov;
}


void EndHookExit::run(){
  if (cov && cov->status) {
    c->exit_status=cov->getCoverage();
  } else {
    c->exit_status=exit_status;
  }
}

void EndHookInteractive::run() {
  Policy policy;
  c->exit_interactive=true;
  Test_engine engine(*c->heuristic,*c->adapter,c->log,policy,
		     c->end_conditions,c->disabled_tags);
  engine.interactive();
}

void hook_delete(EndHook* e)
{
  if (e) {
    delete e;
  }
}

void stringify_hooks(std::ostringstream& t,
		     const std::list<EndHook*> hl,
		     const std::string name)
{
  std::list<EndHook*>::const_iterator i=hl.begin();
  for(i++;i!=hl.end();i++) {
    std::string val=(*i)->stringify();
    if (val!="") {
      t << name << " = " << val << std::endl;
    }
  }
}


void hook_runner(EndHook* e) {
  if (e)
    e->run();
}

std::string EndHookExit::stringify() {
    if (!status) return Writable::stringify();
    return "exit("+to_string(exit_status)+")";
}

std::string EndHookInteractive::stringify() {
    if (!status) return Writable::stringify();
    return "interactive";
}


EndHook* new_endhook(Conf* c,const std::string& s,int _lineno)
{
  std::string name,option;
  param_cut(s,name,option);
  EndHook* ret=EndHookFactory::create(c, _lineno, name, option);
  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
   ret=EndHookFactory::create(c, _lineno, name, option);

  if (ret) {
    fprintf(stderr,"DEPRECATED END SYNTAX. %s\nNew syntax is %s(%s)\n",
	    s.c_str(),name.c_str(),option.c_str());
  }
  return ret;
}
