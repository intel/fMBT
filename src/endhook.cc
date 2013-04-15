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
#include <sstream>
#include <list>

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2 
#undef FACTORY_CREATE_PARAMS

class Conf;

#define FACTORY_CREATOR_PARAMS Conf* _c, std::string params
#define FACTORY_CREATOR_PARAMS2 _c, params
#define FACTORY_CREATE_PARAMS Conf* _c, std::string name, std::string params


FACTORY_CREATE(EndHook)
FACTORY_DEFAULT_CREATOR(EndHook, EndHookExit, "exit")
FACTORY_DEFAULT_CREATOR(EndHook, EndHookInteractive, "interactive")

FACTORY_ATEXIT(EndHook)
FACTORY_CREATORS(EndHook)
FACTORY_ADD_FACTORY(EndHook)

void EndHookExit::run(){
  c->exit_status=exit_status;
}

void EndHookInteractive::run() {
  c->exit_interactive=true;
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
  for(std::list<EndHook*>::const_iterator i=hl.begin();i!=hl.end();i++) {
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


EndHook* new_endhook(Conf* c,const std::string& s)
{
  std::string name,option;
  param_cut(s,name,option);
  EndHook* ret=EndHookFactory::create(c, name, option);
  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret=EndHookFactory::create(c, name, option);

  if (ret) {
    fprintf(stderr,"DEPRECATED END SYNTAX. %s\nNew syntax is %s(%s)\n",
	    s.c_str(),name.c_str(),option.c_str());
  }
  return ret;  
}
