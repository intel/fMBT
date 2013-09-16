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
#ifndef __endhook_hh__
#define __endhook_hh__

#include "writable.hh"

#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2 
#undef FACTORY_CREATE_PARAMS

class Conf;

#define FACTORY_CREATOR_PARAMS Conf* _c, std::string params
#define FACTORY_CREATOR_PARAMS2 _c, params
#define FACTORY_CREATE_PARAMS Conf* _c, std::string name, std::string params

#include "factory.hh"

class Conf;

class EndHook: public Writable {
public:
  EndHook(Conf* _c,std::string& s): c(_c) {}
  virtual ~EndHook() {}
  virtual void run()=0;
  Conf* c;
};


FACTORY_DECLARATION(EndHook)
EndHook* new_endhook(Conf*, const std::string&);

class EndHookExit: public EndHook {
public:
  EndHookExit(Conf* _c,std::string& s);
  virtual ~EndHookExit();
  virtual void run();
  virtual std::string stringify();

  int exit_status;
  Coverage* cov;
};

class EndHookInteractive: public EndHook {
public:
  EndHookInteractive(Conf* _c,std::string& s): EndHook(_c,s) {
  }
  virtual ~EndHookInteractive() {}
  virtual std::string stringify();
  virtual void run();
};

void stringify_hooks(std::ostringstream& t,
		     const std::list<EndHook*> hl,
		     const std::string name);


#undef FACTORY_CREATOR_PARAMS
#undef FACTORY_CREATOR_PARAMS2 
#undef FACTORY_CREATE_PARAMS
#endif
