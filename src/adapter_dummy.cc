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
#include "adapter_dummy.hh"
#include "log.hh"
#include <cstdio>
#include <sstream>


Adapter_dummy::Adapter_dummy(Log& l, std::string params) :
  Adapter::Adapter(l)
{
}

void Adapter_dummy::execute(std::vector<int>& action)
{
  log.push("Adapter_dummy");

  log.print("<action type=\"input\" name=\"%s\"/>\n",
	    getUActionName(action[0]));

  log.pop();
}

bool  Adapter_dummy::observe(std::vector<int> &action,
				bool block)
{
  return false;
}

FACTORY_DEFAULT_CREATOR(Adapter, Adapter_dummy, "dummy");
