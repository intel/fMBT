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
#include "model.hh"
#include <iostream>

FACTORY_IMPLEMENTATION(Model)

Model::Model(Log&l, std::string params):
  log(l), parent(NULL)
{
}

std::vector<std::string>& Model::getActionNames()
{
  return action_names;
}

std::vector<std::string>& Model::getSPNames()
{
  return prop_names;
}

std::string& Model::getActionName(int action)
{
  return action_names[action];
}

bool Model::is_output(int action)
{
  if (outputs.size()<inputs.size()) {
    for(size_t i=0;i<outputs.size();i++) {
      if (outputs[i]==action) {
        return true;
      }
    }
    return false;
  }
  
  for(size_t i=0;i<inputs.size();i++) {
    if (inputs[i]==action) {
      return false;
    }
  }
  
  return true;
}

void Model::precalc_input_output()
{
  for(size_t i=0;i<action_names.size();i++) {
    if (isOutputName(action_names[i])) {
      outputs.push_back(i);
    }
    
    if (isInputName(action_names[i])) {
      inputs.push_back(i);
    }
  }
}

int Model::action_number(std::string& s)
{
  for(size_t i=0;i<action_names.size();i++) {
    if (action_names[i]==s) {
      return i;
    }
  }
  return -1;
}

Model* Model::up()
{
  return parent;
}

Model* Model::down(unsigned int a)
{
  return NULL;
}

std::vector<std::string>& Model::getModelNames()
{
  return model_names;
}

void Model::setparent(Model* m)
{
  parent = m;
}
