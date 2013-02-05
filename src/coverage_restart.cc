/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2013 Intel Corporation.
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

#include "coverage_restart.hh"
#include "model.hh"
#include "helper.hh"

void Coverage_Restart::new_left_right()
{
  left=new_coverage(log,l);
  right=new_coverage(log,r);

  if (push_depth) {
    left->push();
    right->push();
  }
}

Coverage_Restart::Coverage_Restart(Log& lo, std::string& params): Coverage(lo),left(NULL),right(NULL),previous(0.0),push_depth(0) {
  std::vector<std::string> s;

  commalist(params,s);

  switch(s.size()) {
  case 1:
    l=s[0];
    r="1";
    break;
  case 2:
    l=s[0];
    r=s[1];    
  default:
    status=false;
    return;
  }

  new_left_right();
}

Coverage_Restart::~Coverage_Restart() {

  if (left) {
    delete left;
  }
  if (right) {
    delete right;
  }

}

void Coverage_Restart::push()
{
  if (!status) return;

  push_depth++;

  // Broken!

  csave.push_back(left);
  csave.push_back(right);
  psave.push_back(previous);

  left->push();
  right->push();


  if (!left->status || !right->status) {
    status=false;
  }
}

void Coverage_Restart::pop()
{
  if (!status) return;

  push_depth--;

  // Broken!

  left->pop();
  right->pop();

  previous=psave.back();
  psave.pop_back();

  if (right!=csave.back()) {

    if (push_depth) {
      right->pop();
    }

    delete right;
    right=csave.back();
  }
  csave.pop_back();

  if (left!=csave.back()) {

    if (push_depth) {
      left->pop();
    }
    delete left;
    left=csave.back();
  }
  csave.pop_back();

  if (!left->status || !right->status) {
    status=false;
  }
}

float Coverage_Restart::getCoverage()
{
  if (!status) return 0.0;
  return previous+left->getCoverage();
}

void Coverage_Restart::set_model(Model* _model)
{
  if (!status) return;

  Coverage::set_model(_model);

  left->set_model(model);
  right->set_model(model);

  if (!left->status || !right->status) {
    status=false;
  }
}

bool Coverage_Restart::execute(int action)
{
  if (!status) return false;

  left->execute(action);
  right->execute(action);

  if (!left->status || !right->status) {
    status=false;
  }

  if (status) {
    if (left->getCoverage()>=right->getCoverage()) {
      previous+=right->getCoverage();
      if (csave.empty() || right!=csave.back()) {

	if (push_depth) {
	  left->pop();
	  right->pop();
	}

	delete right;
	delete left;
      }
      new_left_right();      
      if (push_depth) {
	left->push();
	right->push();
      }
      set_model(model);
    }

  }

  return status;
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Restart, "restart")
