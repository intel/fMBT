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

#include "of_html.hh"
#include "coverage.hh"
#include "helper.hh"

std::string OutputFormat_Html::format_covs()
{
  std::string ret("<tr>\n");

  //testname
  ret=ret+"<td>"+testnames.back()+"</td>";

  //verdict
  ret=ret+"<td></td>\n";

  for(unsigned i=0;i<covnames.size();i++) {
    ret=ret+"<td>"+to_string(covs[i]->getCoverage())+
      "</td>\n";
  }
  return ret+"</tr>\n";
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Html, "html")
