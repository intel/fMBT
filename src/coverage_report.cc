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

#include "coverage_report.hh"
#include "model.hh"
#include "helper.hh"
#include "history.hh"

std::string Coverage_report::stringify()
{
  return std::string("");
}

void Coverage_report::on_find() {
  count++;
  traces.push_back(executed);
  tcount[executed]++;
  Coverage_exec_filter::on_find();
}

void Coverage_report::push() {
  Coverage_exec_filter::push();
  save.push(count);
  traces_save.push(traces);
  tcount_save.push(tcount);
}

void Coverage_report::pop() {
  Coverage_exec_filter::pop();
  count=save.top(); save.pop();
  traces=traces_save.top(); traces_save.pop();
  tcount=tcount_save.top(); tcount_save.pop();
}

void Coverage_report::on_online(int action,std::vector<int>&p){
  std::vector<int> pp;
  executed.push_back(std::pair<int,std::vector<int> >(action,pp));
}
