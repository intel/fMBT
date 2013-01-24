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
#include <sstream>
#include <algorithm>

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

bool vcmp (const std::vector<std::pair<int,std::vector<int> > >& lhs,
           const std::vector<std::pair<int,std::vector<int> > >& rhs)
{
  if (lhs.size()==rhs.size()) {
    return lhs<rhs;
  }
  return lhs.size()<rhs.size();
}

bool mytimercmp(struct timeval t1,
		struct timeval t2)
{
  return timercmp(&t1,&t2,<);
}

std::string OutputFormat_Html::report()
{
  std::ostringstream html;


  /*
   * The code is ugly. Sorry.
   */

  html << "<table border=\"2\">"
       << "<tr><th>Name</th><th>trace</th></tr>\n";

  std::vector<std::string>& an(model->getActionNames());

  for(unsigned i=0;i<reportnames.size();i++) {

    bool(*cmprp)(const std::vector<std::pair<int,std::vector<int> > >&,
                 const std::vector<std::pair<int,std::vector<int> > >&) = vcmp;

    std::vector<std::vector<std::pair<int,std::vector<int> > > >& traces(rcovs[i]->traces);
    std::map<std::vector<std::pair<int,std::vector<int> > > , int, bool(*)(const std::vector<std::pair<int,std::vector<int> > >&,const std::vector<std::pair<int,std::vector<int> > >&) > cnt(cmprp);

    for(unsigned j=0;j<traces.size();j++) {
      cnt[traces[j]]++;
    }

    struct timeval time_tmp;
    struct timeval time_consumed={0,0};

    struct timeval average_time={0,0};

    std::vector<struct timeval> t;

    for(unsigned j=0;j<rcovs[i]->times.size();j++) {
      struct timeval t1=rcovs[i]->times[j].second;
      struct timeval t2=rcovs[i]->times[j].first;
      timersub(&t1,&t2,
	       &time_tmp);
      t.push_back(time_tmp);
      timeradd(&time_consumed,&time_tmp,&time_consumed);
    }

    if (rcovs[i]->times.size()) {
      average_time.tv_sec=time_consumed.tv_sec/rcovs[i]->times.size();
      average_time.tv_usec=(((time_consumed.tv_sec%rcovs[i]->times.size())*1000000)+time_consumed.tv_usec)/rcovs[i]->times.size();
    }

    float variance=0;

    for(unsigned j=0;j<rcovs[i]->times.size();j++) {
      timersub(&t[j],&average_time,&time_tmp);

      float tmp=time_tmp.tv_sec+(1.0*time_tmp.tv_usec)/1000000.0;
      variance+=tmp*tmp;
    }

    if (rcovs[i]->times.size()) {
      variance=variance/rcovs[i]->times.size();
    }

    html << "<tr><td><a href=\"javascript:showHide('ID"
         << to_string(i)
         << "')\"><table><tr><td>"
         << reportnames[i]
         << "</td></tr><tr><td>Number of executed tests:"
         << to_string((unsigned)traces.size())
         << "</td></tr><tr><td>unique tests:"
         << to_string(unsigned(cnt.size()))

         << "</td></tr><tr><td>time used:"
	 << to_string(time_consumed,true) << " Variance:" << to_string(variance) << " Average:" << to_string(average_time,true);

    if (rcovs[i]->times.size()) {
      html << " Min:" << to_string(*min_element(t.begin(),t.end(),mytimercmp),true)
	   << " Max:" << to_string(*max_element(t.begin(),t.end(),mytimercmp),true);
    }

    html << "</td></tr></table></a></td>"
            "<td>\n<div id=\"ID"
         << to_string(i)
         << "\">\n"
         << "<table border=\"4\">";

    for(std::map<std::vector<std::pair<int,std::vector<int> > >,int>::iterator j=cnt.begin();
        j!=cnt.end();j++) {

      html << "<td valign=\"top\">\n"
           << "<table border=\"0\">\n"
           << "<caption>Count:"
           << to_string((unsigned)j->second)
           << "</caption><td>"
           << "\n<ol>\n";

      const std::vector<std::pair<int,std::vector<int> > >& t(j->first);
      for(unsigned k=0; k<t.size();k++) {
        html << "<li>"
             << an[t[k].first];
      }
      html << "</ol>\n"
           << "</td></tr></table></td>";
    }

    html << "</table>\n"
         << "</div>\n</tr>";

  }
  html << "</table>";
  return html.str();
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Html, "html")
