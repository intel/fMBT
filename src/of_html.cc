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

#include <map>

std::string OutputFormat_Html::header()
{
  std::string script(
    "<SCRIPT LANGUAGE=\"JavaScript\">\n"
    "<!--\n"
    "function showHide(elementid){\n"
    "if (document.getElementById(elementid).style.display == 'none'){\n"
    "document.getElementById(elementid).style.display = '';\n"
    "} else {\n"
    "document.getElementById(elementid).style.display = 'none';\n"
    "}\n"
    "} \n"
    "//-->\n"
    "</SCRIPT>\n");
  std::string ret("<html><header>"+script+"</header>");
  ret+="<body>";
  ret+="<table border=\"1\">\n<tr><th>UC</th>\n<th>verdict</th>\n";
  for(unsigned i=0;i<covnames.size();i++) {
    ret=ret+"<th>"+covnames[i]+"</th>\n";
  }
  ret=ret+"</tr>\n";
  return ret;
}

std::string OutputFormat_Html::footer() {
  return "</table>";
}
  

std::string OutputFormat_Html::format_covs()
{
  std::string ret("<tr>\n");

  //testname
  ret=ret+"<td>"+testnames.back()+"</td>";

  //verdict
  ret=ret+"<td>"+test_verdict+"</td>\n";

  for(unsigned i=0;i<covnames.size();i++) {
    ret=ret+"<td>"+to_string(covs[i]->getCoverage())+
      "</td>\n";
  }
  return ret+"</tr>\n";
}


/* We might want to have more than one comparator for
   different orders */

bool vcmp (const std::vector<int>& lhs,
	   const std::vector<int>& rhs)
{
  if (lhs.size()==rhs.size()) {
    return lhs<rhs;
  }
  return lhs.size()<rhs.size();
}


std::string OutputFormat_Html::report()
{
  std::string ret("<table border=\"2\"><tr><th>Name</th><th>trace</th></tr>\n");
  std::vector<std::string>& an(model->getActionNames());
  
  for(unsigned i=0;i<reportnames.size();i++) {

    bool(*cmprp)(const std::vector<int>&,
		 const std::vector<int>&) = vcmp;

    std::vector<std::vector<int> >& traces(rcovs[i]->traces);
    std::map<std::vector<int> , int, bool(*)(const std::vector<int>&,const std::vector<int>&) > cnt(cmprp);

    for(unsigned j=0;j<traces.size();j++) {
      printf("size %i:",traces[j].size());
      for(unsigned k=0;k<traces[j].size();k++) {
	printf("%i,",traces[j][k]);
      }
      printf("\n");
      cnt[traces[j]]++;
    }

    ret=ret+"<tr><td><a href=\"javascript:showHide('"+reportnames[i]+"')\"><table><tr><td>" + reportnames[i]+"</td></tr><tr><td>Number of executed tests:"+to_string((unsigned)traces.size())+"</td></tr><tr><td>unique tests:"+to_string(unsigned(cnt.size()))+"</td></tr></table></a></td>";
    ret=ret+"<td>\n<div id=\""+reportnames[i]+"\">\n"+
      "<table border=\"4\">";
    
    printf("reportnames %s\n",reportnames[i].c_str());
    printf("vector size %i\n",(int)traces.size());
    printf("Unique traces %i\n",(int)cnt.size());

    for(std::map<std::vector<int>,int>::iterator j=cnt.begin();
	j!=cnt.end();j++) {

      ret=ret+"<td valign=\"top\">\n"
	"<table border=\"0\">\n"
	"<caption>Count:"+to_string((unsigned)j->second)+"</caption><td>";
      ret=ret+"\n<ol>\n";
      const std::vector<int>& t(j->first);
      for(unsigned k=0; k<t.size();k++) {
	ret=ret+"<li>"+an[t[k]];
      }
      ret=ret+"</ol>\n";
      ret=ret+"</td></tr></table></td>";
    }

    /*
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
    */
    ret=ret+"</table>\n"
      "</div>\n</tr>";
    
  }
  ret=ret+"</table>";
  return ret;
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Html, "html")
