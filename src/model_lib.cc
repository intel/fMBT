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

#ifndef __MINGW32__

#include "log.hh"
#include "model.hh"
#include "null.hh"
#include "conf.hh"
#include "helper.hh"
#include <dlfcn.h>
#include <cstring>

namespace {

  std::vector<void*> mods;

  void mods_atexit() {
    for(unsigned i=0;i<mods.size();i++) {
      dlclose(mods[i]);
    }
  }

  Model* lib_creator(Log& l, std::string params,void*) {
    Model* m;
    std::vector<std::string> s;

    commalist(params,s);
    if (s.size()<1) {
      m = new Null(l);
      if (m) {
	m->status   = false;
	m->errormsg = std::string("lib:Can't load model ") + params;
      }
      return m;
    }

    m = new_model(l,s[0]);

    if (!m) {
      void* handle=NULL;

      if (s.size()>1) {
	handle=load_lib("",s[1]);
      } else {
	std::string model_name,model_param;
	param_cut(s[0],model_name,model_param);      
	handle=load_lib(model_name,"");
      }

      if (handle) {
	m = new_model(l,s[0]);
	if (mods.empty()) {
	  atexit(mods_atexit);
	}
	mods.push_back(handle);
      } else {
	m = new Null(l);
	if (m) {
	  m->status   = false;
	  m->errormsg = std::string("lib:Can't load model ") + params;
	}
      }
    }
    return m;
  }
  static ModelFactory::Register me("lib", lib_creator);
}

#endif
