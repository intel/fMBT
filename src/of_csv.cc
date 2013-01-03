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

#include <sstream>

std::string OutputFormat_Csv::CRLF("\x0D\x0A");

std::string OutputFormat_Csv::csv_escape(std::string& s)
{
  return s;
}


std::string OutputFormat_Csv::format_covs()
{
  std::ostringstream csv;
  std::string pre;

  //testname
  csv << csv_escape(testnames.back());

  //verdict
  csv << ",";

  pre = csv.str();

  if (!covnames.empty()) {
    for(unsigned i=0;i<covnames.size()-1;i++) {
      if (covs[i])
        csv << "," << to_string(covs[i]->getCoverage());
    }
    if (covnames.size()>0) {
      csv << "," << to_string(covs[covnames.size()-1]->getCoverage());
    }
  }

  csv << CRLF;

  if (!reportnames.empty()) {
    for(unsigned i=0;i<reportnames.size();i++) {
      if (rcovs[i]->times.empty()) {
        printf("No end time for %i???\n",i);
      } else {
        for(unsigned j=0;j<rcovs[i]->times.size();j++) {
          csv << pre << "\"" << reportnames[i]
              << "\"," << to_string(rcovs[i]->times[j].first)
              << "," << to_string(rcovs[i]->times[j].second) << CRLF;
        }
      }
    }
  }
  return csv.str();
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Csv, "csv")
