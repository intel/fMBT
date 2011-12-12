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
#include "adapter.hh"
#include "log.hh"
#include "conf.hh"
#include "helper.hh"
#include <dlfcn.h>

namespace { 
  Adapter* creator_func(Log& log, std::string params = "") {
    Adapter* a;
    std::string adapter_name,adapter_param;
    std::string s(unescape_string(strdup(params.c_str())));

    Conf::split(s, adapter_name, adapter_param);
   
    a = AdapterFactory::create(log, adapter_name, adapter_param);
    if (!a) {
      std::string lib("lib"+adapter_name+".so");
      void* handle=dlopen(lib.c_str(),RTLD_NOW);
      if (handle) {
	a = AdapterFactory::create(log, adapter_name, adapter_param);
      }
    }
    return a;
  } 
  static AdapterFactory::Register me("lib", creator_func);
};
