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

#include "of_csv.hh"
#include "coverage.hh"
#include "helper.hh"

std::string OutputFormat_Csv::CRLF("\x0D\x0A");

std::string OutputFormat_Csv::csv_escape(std::string& s)
{
  return s;
}


std::string OutputFormat_Csv::format_covs()
{
  std::string ret;

  //testname
  ret=csv_escape(testnames.back());

  //verdict
  ret=ret+",";

  for(unsigned i=0;i<covnames.size()-1;i++) {
    ret=ret+","+to_string(covs[i]->getCoverage());
  }
  if (covnames.size()>0) {
    ret=ret+","+to_string(covs[covnames.size()-1]->getCoverage());
  }
  return ret+CRLF;
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Csv, "csv")
