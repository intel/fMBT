/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2013, Intel Corporation.
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
#ifndef __coverage_report_filter_hh__
#define __coverage_report_filter_hh__

#include "coverage_report.hh"

#include <sys/time.h>
#include <stack>
#include <utility>

class Coverage_report_filter;

static std::vector<std::string*> dummy;

Coverage_report_filter* new_coveragereportfilter(Log& l, std::string& s);

class Coverage_report_filter: public Coverage_report {
public:
  Coverage_report_filter(Log&l,std::string params):Coverage_report(l,dummy,
								   dummy,dummy)
  {
    std::vector<std::string> s;
    commalist(params,s);
    if(s.size()>0) {
      len=atoi(s[0].c_str());
      if (s.size()==2) {
	sub=new_coveragereportfilter(l,s[1]);
      }
    }
  }

  void set_sub(Coverage_report* _s) {
    if (sub) {
      //sub->set_sub(_s);
    } else {
      sub=_s;
    }
  }

  virtual ~Coverage_report_filter() {
    delete sub;
  }

  //bool execute(int action);

protected:
public:
  Coverage_report* sub;
protected:
  bool last;
  int len;
};

FACTORY_DECLARATION(Coverage_report_filter)

#endif
