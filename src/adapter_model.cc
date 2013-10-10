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
#include "adapter_model.hh"
#include "helper.hh"
#include <cstdio>
#include <sstream>
#include <cstdlib>
#include "random.hh"

Adapter_model::Adapter_model(Log& l,const std::string& params) :
  Adapter::Adapter(l)
{
  model = new_model(log,params);
  model->init();
  model->reset();
  r=Random::default_random();
}

bool Adapter_model::init()
{
  std::vector<std::string>& mactions=model->getActionNames();
  adapter2model.resize(actions->size());
  for(unsigned i = 0; i < actions->size(); i++) {
      adapter2model[i]=find(mactions, (*actions)[i]);
  }
  model2adapter.resize(mactions.size());
  for(unsigned i = 0; i < mactions.size(); i++) {
    model2adapter[i]=find(*actions, mactions[i]);
  }
  return true;
}

std::string Adapter_model::stringify()
{
  std::ostringstream t(std::ios::out | std::ios::binary);

  std::string s=model->stringify();

  t << "model:" << capsulate(s) << std::endl;

  return t.str();
}

/* adapter can execute.. */
void Adapter_model::execute(std::vector<int> &action)
{
  log.push("Adapter_model");

  log.print("<action type=\"input\" name=\"%s\"/>",
	    getUActionName(action[0]));

  if (!model->execute(adapter2model[action[0]])) {
    action[0]=0;
  }

  log.pop();
}

Adapter_model::~Adapter_model()
{
  if (r)
    r->unref();
}


int  Adapter_model::observe(std::vector<int> &action,bool block)
{
  int* act,*iact;
  int actions=-model->getIActions(&iact)+model->getActions(&act);
  int i=1+random()%actions;
  int a;
  if (!actions) {
    return false;
  }
  a=-1;
  while (i) {
    a++;
    while (!model->is_output(act[a])) {
      i--;
    }
  }
  action.resize(1);
  action[0]=act[a];
  return true;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_model, "model")
