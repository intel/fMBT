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
#ifndef __coverage_paths_hh__
#define __coverage_paths_hh__

#include "coverage_report.hh"
#include "helper.hh"
#include <map>

class Coverage_paths_base: public Coverage_report {
public:
  Coverage_paths_base(Log&l,std::vector<std::string*>& _from,
		 std::vector<std::string*>& _to,
		 std::vector<std::string*>& _drop):
    Coverage_report(l,_from,_to,_drop), filter_outputs(false),af(false),pf(true),unique(true) { traces_needed=false; }
  
  virtual ~Coverage_paths_base() {}

  virtual float getCoverage() { 
    if (unique) {
      return (on_report&&online?0.5:0.0)+tcount.size();
    }
    return (on_report&&online?0.5:0.0)+count;
  }
  bool filter_outputs;
  bool af;
  bool pf;
  bool unique;
protected:
  virtual void on_restart(int action,std::vector<int>&p);
  virtual void on_online(int action,std::vector<int>&p);
private:
  std::vector<int> pp;
};

#endif
