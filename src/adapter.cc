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
#include <cstdio>
#include "log.hh"

Adapter::Adapter(std::vector<std::string>& _actions,Log&l) :parent(NULL), actions(_actions), log(l)
{
  unames.resize(actions.size()+1);
}

std::map<std::string,Adapter::creator>* Adapter::factory = 0;

void Adapter::add_factory(std::string name,creator c)
{
  if (!factory) factory = new std::map<std::string,Adapter::creator>;
  (*factory)[name]=c;
}

Adapter* Adapter::create(std::string name,std::vector<std::string>& actions,std::string params,Log&l)
{
  creator c=(*factory)[name];
  
  l.debug("trying to load adapter %s",name.c_str());

  if (c) {
    return c(actions,params,l);
  }

  throw (int)42429;

  return NULL;
}

Adapter* Adapter::up() { 
  return parent;
}

Adapter* Adapter::down(unsigned int a)
{
  printf("adapter_base %i\n",a);
  return NULL;
}

/*
int Adapter::action_number(std::string& name) 
{
  for(size_t i=0;i<actions.size();i++) {
    if (actions[i]==name) {
      return i;
    }
  }
  return -1;
}
*/
