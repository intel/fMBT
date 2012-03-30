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

#include "coverage_of.hh"

std::string Coverage_of::stringify()
{
  return std::string("");
}

bool Coverage_of::execute(int action)
{
  for(unsigned i=0;i<covs.size();i++) {
    covs[i]->execute(action);
  }
  return true;
}

void Coverage_of::history(int action,std::vector<int>& props,
			  Verdict::Verdict verdict)
{
  for(unsigned i=0;i<covs.size();i++) {
    covs[i]->history(action,props,verdict);
  }
}
