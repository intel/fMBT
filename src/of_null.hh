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
#ifndef __of_null_hh__
#define __of_null_hh__

#include "of.hh"

class OutputFormat_Null: public OutputFormat {
public:
  OutputFormat_Null(std::string params): OutputFormat(params) {}
  virtual ~OutputFormat_Null() {}
  virtual void set_prefix(std::string& prefix) {}
  virtual void add_testrun(std::string& name)  {}
  virtual void add_uc(std::string& name,Coverage* c) {}

  virtual std::string format_covs();  
};

#endif
