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

#include "coverage_prop.hh"
#include "model.hh"

Coverage_Prop::Coverage_Prop(Log& l, std::string& params) :
    Coverage(l)
{

}

bool Coverage_Prop::execute(int action)
{
  return true;
}


float Coverage_Prop::getCoverage()
{
  if (props_total) {
    return (1.0*model->getprops(NULL))/(1.0*props_total);
  }

  return 1.0;
}


int Coverage_Prop::fitness(int* action,int n,float* fitness)
{
  float m=-1;
  int pos=-1;

  if (props_total==0) {
    for(int i=0;i<n;i++) {
      fitness[i]=0.0;
    }
    return 0;
  }
  
  for(int i=0;i<n;i++) {
    model->push();
    model->execute(action[i]);
    fitness[i]=getCoverage();
    model->pop();

    if (m<fitness[i]) {
      pos=i;
      m=fitness[i];
    }
  }
  
  return pos;
}

void Coverage_Prop::set_model(Model* _model) {
  Coverage::set_model(_model);
  props_total=model->getSPNames().size()-1; // let's ignore 0
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Prop, "tag");
