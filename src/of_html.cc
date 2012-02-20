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
#include "model.hh"

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

std::string OutputFormat_Html::report()
{
  std::string ret("<table><tr>\n");
  std::vector<std::string>& an(model->getActionNames());
  for(unsigned i=0;i<reportnames.size();i++) {
    ret=ret+"<td>"+reportnames[i]+"</td>";
    printf("reportnames %s\n",reportnames[i].c_str());
    std::vector<std::vector<int> >& traces(rcovs[i]->traces);
    printf("vector size %i\n",(int)traces.size());
    for(unsigned j=0;j<traces.size();j++) {
      ret=ret+"<td>";
      ret=ret+"\n<ol>\n";
      std::vector<int>& t(traces[j]);
      for(unsigned k=0; k<t.size();k++) {
	ret=ret+"<li>"+an[t[k]];
      }
      ret=ret+"</ol>\n";
      ret=ret+"</td>";
    }
  }
  ret=ret+"</tr></table>";
  return ret;
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Html, "html")
