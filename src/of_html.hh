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
#ifndef __of_html_hh__
#define __of_html_hh__

#include "of.hh"

class OutputFormat_Html: public OutputFormat {
public:
  OutputFormat_Html(std::string params): OutputFormat(params) {}
  virtual ~OutputFormat_Html() {}
  
  virtual std::string header() {
    std::string ret("<table border=\"1\">\n<tr><th>UC</th>\n<th>verdict</th>\n");

    for(unsigned i=0;i<covnames.size();i++) {
      ret=ret+"<th>"+covnames[i]+"</th>\n";
    }
    ret=ret+"</tr>\n";
    return ret;
  }
  virtual std::string footer() {
    return "</table>";
  }
  virtual std::string format_covs();
  virtual std::string report();
private:
};

#endif
