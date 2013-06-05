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

/* Implements adapter_dlopen: an adapter which dynamically loads an
 * adapter plugin library and creates the wanted adapter from there.
 *
 * adapter_dlopen params: <sharedlib> "," <adapter_name> "," <adapter_params>
 * where sharedlib will be dynamically loaded. It should register
 * adapter_name to the adapter factory. adapter_params will be
 * passed to the loaded adapter.
 */

#ifndef __MINGW32__

#include "adapter_dlopen.hh"
#include <cstdio>
#include <sstream>
#include <dlfcn.h>
#include <cstdlib>
#include "helper.hh"

#define RETURN_ERROR(s) { \
    status = false;       \
    errormsg = s;         \
    return;               \
  }

Adapter_dlopen::Adapter_dlopen(Log& log, std::string params) :
  Adapter::Adapter(log),
  loaded_adapter(NULL),
  library_handle(NULL)
{

  std::vector<std::string> s;
  commalist(params,s);

  std::string library_file;

  if (s.size()!=2) {
    RETURN_ERROR("Incorrect number of elements");
  }

  library_file = s[0];
    
  library_handle = dlopen(library_file.c_str(), RTLD_NOW | RTLD_GLOBAL);
  if (!library_handle) {
    std::ostringstream dlopenerror;
    dlopenerror << "opening \"" << library_file << "\" failed: " << dlerror();
    fprintf(stderr, "%s\n", dlopenerror.str().c_str());
    RETURN_ERROR(dlopenerror.str());
  }
  
  /* dlopening the adapter registers the loaded adapter to
     adapter_factory. Just try fetching it from there.
  */
  
  loaded_adapter = new_adapter(log,s[1]);
  if (!loaded_adapter)
    RETURN_ERROR("creating adapter from successfully opened library failed");
}

Adapter_dlopen::~Adapter_dlopen()
{
  if (loaded_adapter) 
    delete loaded_adapter;
  if (library_handle)
    dlclose(library_handle);
}

int Adapter_dlopen::check_tags(int* tag,int len,std::vector<int>& t)
{
  if (loaded_adapter) 
    return loaded_adapter->check_tags(tag,len,t);
  return 0;
}

void Adapter_dlopen::adapter_exit(Verdict::Verdict verdict,
				  const std::string& reason)
{
  if (loaded_adapter)   
    loaded_adapter->adapter_exit(verdict,reason);
}

void Adapter_dlopen::set_actions(std::vector<std::string>* _actions)
{
  Adapter::set_actions(_actions);
  if (loaded_adapter) loaded_adapter->set_actions(_actions);
}

bool Adapter_dlopen::init()
{
  return loaded_adapter->init();
}

std::string Adapter_dlopen::stringify()
{
  if (!status) return errormsg;
  return "dlopen:" + loaded_adapter->stringify();
}

void Adapter_dlopen::execute(std::vector<int>& action)
{
  if (!loaded_adapter) action.resize(0);
  else loaded_adapter->execute(action);
}

int  Adapter_dlopen::observe(std::vector<int> &action,
				bool block)
{
  return loaded_adapter->observe(action, block);
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_dlopen, "dlopen")

#endif
