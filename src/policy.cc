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
  int* act=NULL;

  if (actions.size()>0) {
    int c=m->getActions(&act);
    for(unsigned i=0;i<actions.size();i++) {
      for(unsigned j=0;j<c;j++) {
	if (act[j]==actions[i]) {
	  return act[j];
	}
      }
    }
  }
  return 0;
}

void Policy::set_model(Model* _m)
{
  m=_m;
}
