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

#include "heuristic_proxy.hh"

Heuristic* Heuristic_proxy::old_heuristic=NULL;

Heuristic* heuristic_proxy_creator (Log& log, std::string params = "")
{
  return Heuristic_proxy::old_heuristic;
}

Heuristic_proxy::Heuristic_proxy(Log& l,Heuristic* _h,const std::string& _n):
  Heuristic(l), h(_h),name(_n) {
  callback_proxy.add_call(std::string("heuristic"),this,(Proxy::func_ptr_t) & Heuristic_proxy::call);
  add_call(std::string("get"),this,(Proxy::func_ptr_t) & Heuristic_proxy::get);
  add_call(std::string("set"),this,(Proxy::func_ptr_t) & Heuristic_proxy::set);
  status=h->status;errormsg=h->errormsg;

  old_heuristic=h;

  HeuristicFactory::add_factory("old",heuristic_proxy_creator);
}

