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
#include "adapter.hh"
#include "adapter_dummy.hh"
#include "log.hh"
#include "conf.hh"
#include "helper.hh"
#include <dlfcn.h>
#include <string.h>

namespace {
  std::vector<void*> libs;

  void libs_atexit() {
    for(unsigned i=0;i<libs.size();i++) {
      dlclose(libs[i]);
    }
  }

  Adapter* lib_creator(Log& l, std::string params,void*) {
    Adapter* m;
    std::vector<std::string> s;

    commalist(params,s);
    if (s.size()<1) {
      m = new Adapter_dummy(l,"");
      if (m) {
	m->status   = false;
	m->errormsg = std::string("lib:Can't load adapter ") + params;
      }
      return m;
    }

    m = new_adapter(l,s[0]);

    if (!m) {
      void* handle=NULL;

      if (s.size()>1) {
	handle=load_lib("",s[1]);
      } else {
	std::string adapter_name,adapter_param;
	param_cut(s[0],adapter_name,adapter_param);
	handle=load_lib(adapter_name,"");
      }

      if (handle) {
	m = new_adapter(l,s[0]);
	if (libs.empty()) {
	  atexit(libs_atexit);
	}
	libs.push_back(handle);
      } else {
	m = new Adapter_dummy(l,"");
	if (m) {
	  m->status   = false;
	  m->errormsg = std::string("lib:Can't load adapter ") + params;
	}
      }
    }
    return m;
  }

  static AdapterFactory::Register me("lib", lib_creator);
}
#endif
