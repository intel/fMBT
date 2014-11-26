/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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

#include "learning.hh"

FACTORY_IMPLEMENTATION(Learning)

#include "log.hh"
#include "params.hh"

Learning::Learning(Log& l):suggested(false), alphabet(NULL), log(l)
{
  log.ref();
}

Learning* new_learning(Log& l, std::string& s) {
  std::string name,option;
  param_cut(s,name,option);
  Learning* ret=LearningFactory::create(l, name, option);

  return ret;
}
