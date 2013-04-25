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

void Coverage_report::on_find(int action,std::vector<int>&p) {
  was_online=true;
  count++;
  if (traces_needed)
    traces.push_back(executed);
  if (push_depth!=0 && 
      tcount_save[push_depth-1][executed]==0) {
    tcount_save[push_depth-1][executed]=tcount[executed];
  }
  tcount[executed]++;
  Coverage_exec_filter::on_find(action,p);
}

void Coverage_report::push() {
  push_depth++;
  Coverage_exec_filter::push();
  save.push(count);
  if (traces_needed)
    traces_save_.push(traces.size());
  tcount_save.resize(push_depth);
  //tcount_save.push(tcount);
}

void Coverage_report::pop() {
  Coverage_exec_filter::pop();
  count=save.top(); save.pop();
  // traces=traces_save.top(); traces_save.pop();
  if (traces_needed) {
    traces.resize(traces_save_.top()); traces_save_.pop();
  }
  //tcount=tcount_save.top(); tcount_save.pop();

  push_depth--;
  std::map<std::vector<std::pair<int,std::vector<int> > >, int>::iterator i;
  std::map<std::vector<std::pair<int,std::vector<int> > >, int>::iterator e;
  i=tcount_save[push_depth].begin();
  e=tcount_save[push_depth].end();
  for(;i!=e;i++) {
    if (i->second) {
      tcount[i->first] = i->second;
    } else {
      tcount.erase(i->first);
    }
  }
  tcount_save.resize(push_depth);
}

void Coverage_report::on_online(int action,std::vector<int>&p){
  std::vector<int> pp;
  executed.push_back(std::pair<int,std::vector<int> >(action,pp));
}

void Coverage_report::on_offline(int action,std::vector<int>&p){
  if (was_online) {
    if (traces_needed) {
      struct timeval t1=* etime.begin();
      times.push_back(std::pair<struct timeval,struct timeval>
		      (t1,History::current_time));
    }
    was_online=false;
  }
}
