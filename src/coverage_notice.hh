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
#ifndef __coverage_notice_hh__
#define __coverage_notice_hh__

#include "coverage_report.hh"
#include "coverage_const.hh"

#include <sys/time.h>
#include <stack>
#include <utility>

class Coverage_notice: public Coverage_report {
public:
  Coverage_notice(Log&l,std::string _cc1,std::string _cc2);
  virtual ~Coverage_notice();

  virtual bool execute(int action);

  virtual void set_model(Model* _model)
  {
    Coverage_report::set_model(_model);
    foo();
  }

  void foo();

  std::string cc1,cc2;
  
  std::list<std::pair<std::pair<Coverage*,Coverage*>,
		      std::pair<
			std::pair<struct timeval,struct timeval>,
			std::vector<std::pair<int,std::vector<int> > > > > > subcovs;

  Coverage_Const const1;
};

#endif
