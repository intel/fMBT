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
#include "helper.hh"
#include <cstdio>
#include "log.hh"

struct timeval Adapter::current_time;
int Adapter::sleeptime = 0;
FACTORY_IMPLEMENTATION(Adapter)

Adapter::Adapter(Log& l, std::string params) :
log(l), actions(NULL), tags(NULL), parent(NULL)
{
  log.ref();
}

Adapter::~Adapter()
{
  for(unsigned i=0;i<unames.size();i++) {
    if (unames[i]) {
      escape_free(unames[i]);
      unames[i]=NULL;
    }
  }
  log.unref();
}

void Adapter::set_actions(std::vector<std::string>* _actions)
{
  actions = _actions;
  unames.resize(actions->size()+1);
}

void Adapter::set_tags(std::vector<std::string>* _tags)
{
  tags = _tags;
}

bool Adapter::init()
{
  return true;
}

int Adapter::check_tags(int* tag,int len,std::vector<int>& t)
{
  t.resize(0);
  return 0;
}

Adapter* Adapter::up()
{
  return parent;
}

Adapter* Adapter::down(unsigned int a)
{
  printf("adapter_base %i\n",a);
  return NULL;
}

std::vector<std::string>& Adapter::getAdapterNames()
{
  return adapter_names;
}

std::vector<std::string>& Adapter::getAllActions()
{ 
  return *actions;
}

std::string& Adapter::getActionName(int action) {
  return (*actions)[action];
}

int Adapter::getActionNumber(std::string& name) 
{
  for(size_t i=0;i<actions->size();i++) {
    if ((*actions)[i]==name) {
      return i;
    }
  }
  return -1;
}

int Adapter::getActionNumber(const char *name)
{
  std::string _name(name);
  return getActionNumber(_name);
}


void Adapter::setparent(Adapter* a)
{
  parent = a;
}

const char* Adapter::getUActionName(int action)
{
  switch (action) {
  case -1: return "OUTPUTONLY";
  case -2: return "DEADLOCK";
  case -3: return "SILENCE";
  default:
    if (action<0) {
      return "";
    }
  }
  if (!unames[action]) {
    unames[action]=escape_string((*actions)[action].c_str());
  }
  return unames[action];
}

Adapter* new_adapter(Log& l, std::string& s) {
  std::string name,option;
  param_cut(s,name,option);
  Adapter* ret=AdapterFactory::create(l, name, option);

  if (ret) {
    return ret;
  }

  //Let's try old thing.
  split(s, name, option);
  ret=AdapterFactory::create(l, name, option);

  if (ret) {
    fprintf(stderr,"DEPRECATED ADAPTER SYNTAX. %s\nNew syntax is %s(%s)\n",
	    s.c_str(),name.c_str(),option.c_str());
  }

  return ret;
}
