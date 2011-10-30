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

/* Implements adapter_dlopen: an adapter which replaces itself by an
 * adapter that is loaded according to give specs. (reconsider: if
 * this would work as a brige, stringify() would work better.)*/

#include "adapter_dlopen.hh"
#include <cstdio>
#include <sstream>
#include <dlfcn.h>
#include <cstdlib>

Adapter_dlopen::Adapter_dlopen(std::vector<std::string>& _actions,Log&l) : Adapter::Adapter(_actions,l)
{
  abort();
}

std::string Adapter_dlopen::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);
  return t.str();
}

/* adapter can execute.. */
void Adapter_dlopen::execute(std::vector<int>& action)
{
  abort();
}

bool  Adapter_dlopen::readAction(std::vector<int> &action,
				bool block)
{
  abort();
}

namespace {
  Adapter* adapter_creator(std::vector<std::string>& _actions,
			   std::string params,Log&l) {

    /* dlopen params: <sharedlib> "," <adapter_name> ","
       <adapter_params> where sharedlib will be dynamically loaded. It
       should register adapter_name to the adapter
       factory. adapter_params will be passed to the loaded adapter.*/
        
    void *library_handle;
    char library_file[1024];
    char adapter_name[1024];
    char adapter_params[1024];

    std::stringstream s(params);
    s.getline(library_file, 1024, ',');
    s.getline(adapter_name, 1024, ',');
    s.getline(adapter_params, 1024);
    if (library_file[0] == '\0') return NULL;
    if (adapter_name[0] == '\0') return NULL;

    library_handle = dlopen(library_file, RTLD_LAZY);
    if (!library_handle) {
      fprintf(stderr, "opening '%s' failed\n", library_file);
      fprintf(stderr, "%s\n", dlerror());
      return NULL;
    }

    /* dlopening the adapter registers the loaded adapter to
       adapter_factory. Just try fetching it from there.
     */
    Adapter* adapter = Adapter::create(adapter_name,
                                       _actions,
                                       adapter_params, l);
    return adapter;
  }
  static adapter_factory register_me("dlopen", adapter_creator);
};
