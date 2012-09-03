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

#include "coverage.hh"
#include "heuristic.hh"
#include "model.hh"
#include "log.hh"
#include "helper.hh"

FACTORY_IMPLEMENTATION(Heuristic)

Heuristic::Heuristic(Log& l, std::string params) :
model(NULL),none(""), log(l)
{
}

Heuristic::~Heuristic()
{
}

bool Heuristic::execute(int action)
{  
  if (!model->execute(action)) {
    log.debug("Heuristic::execute: executing action %i in model failed\n", action);
    return false;
  }

  if (my_coverage) {
    my_coverage->execute(action);
  }

  for(size_t i=0;i<coverage.size();i++) {
    coverage[i]->execute(action);
  }
  return true;
}

std::string& Heuristic::getActionName(int action) {
  none=std::string("NONE");
  if (action>0) {
    return model->getActionName(action);
  } return none;
}

std::vector<std::string>& Heuristic::getAllActions()
{
  return model->getActionNames();
}

float Heuristic::getCoverage() {
  return my_coverage->getCoverage();  
}

Model* Heuristic::get_model() {
  return model;
}

void Heuristic::set_coverage(Coverage* c) {
  my_coverage=c;
}

Coverage* Heuristic::get_coverage() {
  return my_coverage;
}

void Heuristic::set_model(Model* _model) {
  model=_model;
}

Heuristic* new_heuristic(Log& l, std::string& s) {
  std::string name,option;
  param_cut(s,name,option);
  return HeuristicFactory::create(l, name, option);
}
