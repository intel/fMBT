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
#include <string.h>

namespace {
  Adapter* creator_func(Log& l, std::string params = "") {
    Adapter* a;
    std::string adapter_name,adapter_param,adapter_filename;
    char* stmp=strdup(params.c_str());
    std::string s(unescape_string(stmp));
    free(stmp);

    split(s, adapter_name, adapter_param);
    split(adapter_name,adapter_name,adapter_filename,",");

    a = AdapterFactory::create(l, adapter_name, adapter_param);

    if (!a) {
      void* handle=load_lib(adapter_name,adapter_filename);

      if (handle) {
	a = AdapterFactory::create(l, adapter_name, adapter_param);
      } else {
	std::string d("dummy");
	std::string em("");
	a = AdapterFactory::create(l, d, em);
	a->status   = false;
	a->errormsg = std::string("lib:Can't load adapter ") + params;
      }
    }
    return a;
  }
  static AdapterFactory::Register me("lib", creator_func);
}
