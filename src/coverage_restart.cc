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

  push_depth = 0;
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
    break;
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

  csave.push(left);
  csave.push(right);
  psave.push(previous);
  pdsave.push(push_depth);

  left->push();
  right->push();
  push_depth++;
  
  if (!left->status || !right->status) {
    status=false;
  }
}

void Coverage_Restart::pop()
{
  if (!status) return;

  if (push_depth) {
    push_depth--;
    left->pop();
    right->pop();
  }

  push_depth=pdsave.top();
  pdsave.pop();

  previous=psave.top();
  psave.pop();

  if (right!=csave.top()) {
    delete right;
    right=csave.top();
  }

  csave.pop();

  if (left!=csave.top()) {
    delete left;
    left=csave.top();
  }
  csave.pop();

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
    float lc=left->getCoverage();
    float rc=right->getCoverage();
    if (lc>=rc) {
      previous+=lc;
      if (push_depth) {
	left->pop();
	right->pop();
      }

      if (csave.empty() || right!=csave.top()) {
	delete right;
	delete left;
      }

      new_left_right();
      set_model(model);
    }

  }

  return status;
}

Coverage_Noprogress::Coverage_Noprogress(Log&lo, std::string& params): Coverage_Restart(lo,params),noprog(0),lp(-42)
{ 
  {
    std::string tmp=l;
    l=r;
    r=tmp;
    noplimit=atoi(r.c_str());
  }
  {
    Coverage* tmp=left;
    left=right;
    right=tmp;
  }
}

void Coverage_Noprogress::push()
{
  Coverage_Restart::push();
  pdsave.push(noprog);
  psave.push(lp);
}

void Coverage_Noprogress::pop()
{
  lp=psave.top();
  psave.pop();
  noprog=pdsave.top();
  pdsave.pop();
  Coverage_Restart::pop();
}

bool Coverage_Noprogress::execute(int action)
{
  if (!status) return false;

  left->execute(action);
  right->execute(action);

  if (!left->status || !right->status) {
    status=false;
  }

  if (status) {
    float lc=left->getCoverage();
    //float rc=right->getCoverage();

    if(lp!=lc) {
      noprog=0;
      lp=lc;
    } else {
      noprog++;
    }
    
    if (noprog==noplimit) {
      previous+=lc;
      noprog=0;

      if (push_depth>0) {
	left->pop();
	right->pop();
      }

      if (csave.empty() || right!=csave.top()) {
	delete right;
	delete left;
      }

      new_left_right();
      set_model(model);
    }

  }

  return status;
}


FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Restart, "restart")
FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Noprogress, "noprogress")
