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

std::string OutputFormat_Html::bodyId=envstr("bodyId","top");
std::string OutputFormat_Html::headerId=envstr("headerId","header");
std::string OutputFormat_Html::contentClass=envstr("contentClass","content");
std::string OutputFormat_Html::summaryClass=envstr("summaryClass","text total_summary");
std::string OutputFormat_Html::reportTableClass=envstr("reportTableClass","matrix");
std::string OutputFormat_Html::tdVerdictClass=envstr("tdVerdictClass","uc_verdict");
std::string OutputFormat_Html::divListingClass=envstr("divListingClass","text uc_listing");
std::string OutputFormat_Html::testNameClass=envstr("testNameClass","uc_name");
std::string OutputFormat_Html::divFiguresClass=envstr("divFiguresClass","text uc_figures");
std::string OutputFormat_Html::trNameClass=envstr("tdNameClass","name");
std::string OutputFormat_Html::tdNameValueClass=envstr("tdNameValueClass","name_value");
std::string OutputFormat_Html::trExecutedClass=envstr("tdExecutedClass","executed");
std::string OutputFormat_Html::tdExecutedValueClass=envstr("tdExecutedValueClass","executed_value");
std::string OutputFormat_Html::trUniqClass=envstr("trUniqClass","uniq");
std::string OutputFormat_Html::tdUniqTotalClass=envstr("tdUniqTotalClass","uc_total_uniq_tests");
std::string OutputFormat_Html::tdUniqValueClass=envstr("tdUniqValueClass","uc_total_uniq_tests_value");
std::string OutputFormat_Html::trTimeClass=envstr("tdTimeClass","time_used");
std::string OutputFormat_Html::tdTimeValueClass=envstr("tdTimeValueClass","time_used_value");
std::string OutputFormat_Html::trAverageClass=envstr("trAverageClass","average");
std::string OutputFormat_Html::tdAverageValueClass=envstr("tdAverageValueClass","average_value");
std::string OutputFormat_Html::trMinClass=envstr("trMinClass","min");
std::string OutputFormat_Html::tdMinValueClass=envstr("tdMinValueClass","min_value");
std::string OutputFormat_Html::trMaxClass=envstr("trMaxClass","max");
std::string OutputFormat_Html::tdMaxValueClass=envstr("trMaxValueClass","max_value");
std::string OutputFormat_Html::divDetailedClass=envstr("divDetailedClass","uc_detailed_results");
std::string OutputFormat_Html::divCountHeadClass=envstr("divCountHeadClass","uc_count_head");
std::string OutputFormat_Html::divStepsClass=envstr("divStepsClass","uc_steps");
std::string OutputFormat_Html::stylefile=envstr("stylefile","");

std::string OutputFormat_Html::header()
{
  std::string script(
    "    <SCRIPT>\n"
    "        <!--\n"
    "        function showHide(elementid){\n"
    "        if (document.getElementById(elementid).style.display != 'inline'){\n"
    "        document.getElementById(elementid).style.display = 'inline';\n"
    "        } else {\n"
    "        document.getElementById(elementid).style.display = 'none';\n"
    "        }\n"
    "        } \n"
    "        //-->\n"
    "    </SCRIPT>\n");
  std::string style("    <style>\n"
                    "        td { vertical-align: top }\n"
                    "        ." + divDetailedClass + " { display: none }\n"
                    "    </style>\n");


  std::string meta("<meta charset=\"utf-8\">\n");
  std::string stf;
  if (stylefile.length()>0) {
    stf=std::string("<LINK href(\"")+stylefile+"\" rel(\"stylesheet\" type(\"text/css>\"";
  }
  std::string ret("<!DOCTYPE html>\n    <head>\n"+meta+script+style+stf+"    \n    <title>Use Case Report</title>\n    </head>\n");
  ret+="    <body id=\"" + bodyId +"\">\n";
  ret+="        <div id=\"" + headerId +"\">\n";
  ret+="            <h1>Use Case Report</h1>\n";
  ret+="        </div>\n";
  ret+="        <div class=\"" + contentClass + "\">\n";
  ret+="            <div class=\"" + summaryClass + "\">\n";
  ret+="                <h2>Report Summary</h2>\n";
  ret+="                <table class=\"" + reportTableClass + "\" border=\"1\">\n";
  ret+="                    <tr><td>UC</td>\n";
  ret+="                        <td>Verdict</td>\n";
  for(unsigned i=0;i<covnames.size();i++) {
    ret=ret+"                        <td>"+covnames[i]+"</td>\n";
  }
  ret+="                    </tr>\n";
  return ret;
}

std::string OutputFormat_Html::footer() {
  return "            </div>\n\n\n";
}


std::string OutputFormat_Html::format_covs()
{
  std::string ret("                    <tr>\n");

  //testname
  ret+="                        <td>"+testnames.back()+"</td>\n";

  //verdict
  ret+="                        <td class=\"" + tdVerdictClass + "\">"+test_verdict+"</td>\n";

  for(unsigned i=0;i<covnames.size();i++) {
    ret+= "                        <td>"+to_string(covs[i]->getCoverage())+
          "</td>\n";
  }
  return ret+"                    </tr>\n                </table>\n";
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

  html << "            <div class=\"" + divListingClass + "\">\n"
       << "                <h2>Use Cases</h2>\n"
       << "                <ul>\n";

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

    html << "                    <li><a href=\"javascript:showHide('ID" << to_string(i) << "')\" class=\"" + trNameClass + "\">" << reportnames[i] << "</a>\n"
         << "                        <div class=\"" + divFiguresClass + "\">\n"
         << "                            <table class=\"" + reportTableClass + "\">\n"
         << "                                <tr class=\"" + trExecutedClass + "\">\n"
         << "                                    <td>Total count:</td>\n"
         << "                                    <td class=\"" + tdExecutedValueClass + "\">" << to_string((unsigned)traces.size()) << "</td>\n"
         << "                                </tr>\n"
         << "                                <tr class=\"" + trUniqClass + "\">\n"
         << "                                    <td class=\"" + tdUniqTotalClass + "\">Unique count:</td>\n"
         << "                                    <td class=\"" + tdUniqValueClass + "\">" << to_string(unsigned(cnt.size())) << "</td>\n"
         << "                                </tr>\n"
         << "                                <tr class=\"" + trTimeClass + "\">\n"
         << "                                    <td>Total time:</td>\n"
         << "                                    <td class=\"" + tdTimeValueClass + "\">" << to_string(time_consumed,true)
         << "</td>\n"
         << "                                </tr>\n"
         << "                                <tr class=\"" + trAverageClass + "\">\n"
         << "                                    <td>Average time:</td>\n"
         << "                                    <td class=\"" + tdAverageValueClass + "\">" << to_string(average_time,true)
         << "</td>\n"
         << "                                </tr>\n";

    if (rcovs[i]->times.size()) {
      html << "                                <tr class=\"" + trMinClass + "\">\n"
           << "                                    <td>Min. time:</td>\n"
           << "                                    <td class=\"" + tdMinValueClass + "\">" << to_string(*min_element(t.begin(),t.end(),mytimercmp),true) << "</td>\n"
           << "                                </tr>\n"
           << "                                <tr class=\"" + trMaxClass + "\">\n"
           << "                                    <td>Max. time:</td>\n"
           << "                                    <td class=\"" + tdMaxValueClass + "\">" << to_string(*max_element(t.begin(),t.end(),mytimercmp),true) << "</td>\n"
           << "                                </tr>\n";
    }

    html << "                             </table>\n"
         << "                        </div>\n";

    html << "                        <div class=\"" + divDetailedClass + "\" id=\"ID"
         << to_string(i)
         << "\">\n";
    if((unsigned)traces.size() > 0)
    {
         html << "                            <table>\n"
              << "                                <tr>\n";
    }

    for(std::map<std::vector<std::pair<int,std::vector<int> > >,int>::iterator j=cnt.begin();
        j!=cnt.end();j++) {

      html << "                                    <td>\n"
           << "                                        <div class=\"" + divCountHeadClass + "\">"
           << "Count: " << "<span class=\"uc_count\">" << to_string((unsigned)j->second) <<"</span></div>\n"
           << "                                        <div class=\"" + divStepsClass + "\">\n"
           << "                                            <ol>\n";

      const std::vector<std::pair<int,std::vector<int> > >& t(j->first);
      for(unsigned k=0; k<t.size();k++) {
        html << "                                              <li>"
             << an[t[k].first]
             << "</li>\n";
      }
      html << "                                            </ol>\n"
           << "                                         </div>\n"
           << "                                     </td>\n";
    }

    if((unsigned)traces.size() > 0)
    {
        html << "                                </tr>\n"
             << "                            </table>\n"
             << "                        </div>\n";
    }
    else
    {
        html << "                        </div>\n";
    }
        html << "                    </li>\n";
  }
  html << "                </ul>\n"
       << "            </div>\n"
       << "        </div>\n"
       << "    </body>\n"
       << "</html>";
  return html.str();
}

FACTORY_DEFAULT_CREATOR(OutputFormat, OutputFormat_Html, "html")
