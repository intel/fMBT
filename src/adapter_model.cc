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
#include <cstdio>
#include <sstream>
#include <cstdlib>

Adapter_model::Adapter_model(std::vector<std::string>& _actions,Log&l,Model* m) : Adapter::Adapter(_actions,l), model(m)
{
  std::vector<std::string>& mactions=model->getActionNames();
  adapter2model.resize(actions.size());
  for(unsigned i=0;i<actions.size();i++) {
    adapter2model[i]=find(mactions,actions[i]);
  }
  adapter2model.resize(mactions.size());
  for(unsigned i=0;i<mactions.size();i++) {
    model2adapter[i]=find(actions,mactions[i]);
  }
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

bool Adapter_model::readAction(std::vector<int> &action,bool block)
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

namespace {
  Adapter* adapter_creator(std::vector<std::string>& _actions,
			   std::string params, Log& l) {
    Model* m=Model::create(l,filetype(params));
    m->load(params);
    m->reset();

    return new Adapter_model(_actions,l,m);
  }
  static AdapterFactory::Register me("model", adapter_creator);
};
