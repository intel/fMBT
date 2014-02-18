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

#include "coverage_proxy.hh"
#include "helper.hh"

Coverage* Coverage_proxy::old_coverage=NULL;

Coverage* coverage_proxy_creator (Log& log, std::string params = "")
{
  return Coverage_proxy::old_coverage;
}

Coverage_proxy::Coverage_proxy(Log& l,Coverage* _c,const std::string& _n):
  Coverage(l), c(_c),name(_n) {
  callback_proxy.add_call(std::string("coverage"),this,(Proxy::func_ptr_t) & Coverage_proxy::call);
  add_call(std::string("get"),this,(Proxy::func_ptr_t) & Coverage_proxy::get);
  add_call(std::string("set"),this,(Proxy::func_ptr_t) & Coverage_proxy::set);
  add_call(std::string("getValue"),this,(Proxy::func_ptr_t) & Coverage_proxy::get_value);

  status=c->status;errormsg=c->errormsg;

  old_coverage=c;

  CoverageFactory::add_factory("old",coverage_proxy_creator);
}


bool Coverage_proxy::get_value(std::string params,std::string& ret_str) {
  ret_str=to_string(c->getCoverage());
  return true;
}

