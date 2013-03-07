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
#include "policy.hh"

int Policy::choose(std::vector<int>& actions)
{
  /* This code & AAL has a problem:

     If executing an adapter() block of an action has changed the
     state of the model, we should be able to choose execute following
     action types in addition to obvious actions enabled in both
     states:

     1. actions whose guard() was true *before* the adapter() block,
     but is not after the block.

     2. actions whose guard() became true as a result of executing the
     adapter(), but was not true before.

     Current implementation cannot cope with that. Therefore the
     chooser returns blindly the first action for now, and expects AAL
     model_execute to take care of this.

     Perhaps it is time to throw away Policy::choose.

  int* act=NULL;

  if (!actions.empty()) {
    int c=m->getActions(&act);
    for(unsigned i=0;i<actions.size();i++) {
      for(int j=0;j<c;j++) {
	if (act[j]==actions[i]) {
	  return act[j];
	}
      }
    }
  }
  */
  if (!actions.empty()) {
    return actions[0];
  }
  return 0;
}

void Policy::set_model(Model* _m)
{
  m=_m;
}
