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

#include "mwrapper.hh"
#include <cstring>

Mwrapper::~Mwrapper()
{
  if (model) {
    model->unref();
  }
}


Mwrapper::Mwrapper(Log&l, std::string params, aal* _model):
  Model(l, params), model(_model)
{
  if (model) {
    model->ref();
    status = model->status;
    errormsg = model->errormsg;
    action_names=model->getActionNames();
    prop_names=model->getSPNames();
    status = model->status;
    precalc_input_output();
  } else {
    status=false;
  }
}

int Mwrapper::getActions(int** actions) {
  if (!status) {
    return 0;
  }
  int ret=model->getActions(actions);
  status = model->status;
  return ret;
}

int Mwrapper::getIActions(int** actions) {
  if (!status) {
    return 0;
  }

  int a=model->getActions(actions);
  int ret=a;
  for(int i=0;i<a;i++) {
    if (is_output((*actions)[i])) {
      ret--;
      memmove(&(*actions)[i],&(*actions)[i+1],sizeof(int)*
              (a-i-1));
      i--;
      a--;
    }
  }
  status = model->status;
  return ret;
}

bool Mwrapper::reset() {
  status = model->reset();
  errormsg = model->errormsg;
  return status;
}

/* No props */
int Mwrapper::getprops(int** props)
{
  int ret= model->getprops(props);
  status = model->status;
  return ret;
}

int Mwrapper::execute(int action)
{
  if (model->model_execute(action)!=-42) {
    status = model->status;
    return action;
  }
  status = model->status;
  return 0;
}

void Mwrapper::push() {
  model->push();
  status = model->status;
}

void Mwrapper::pop() {
  model->pop();
  status = model->status;
}

bool Mwrapper::init()
{
  return true;
}

std::string Mwrapper::stringify()
{
  if (!status) return errormsg;
  return std::string("");
}

