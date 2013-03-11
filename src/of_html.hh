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
  
  virtual std::string header();

  virtual std::string footer();
  virtual std::string format_covs();
  virtual std::string report();
private:
  static std::string bodyId ;// "top");
  static std::string headerId ;// "header");
  static std::string contentClass ;// "content");
  static std::string summaryClass ;// "text total_summary");
  static std::string reportTableClass ;// "matrix");
  static std::string tdVerdictClass ;// "uc_verdict");
  static std::string divListingClass ;// "text uc_listing");
  static std::string testNameClass ;// "uc_name");
  static std::string divFiguresClass ;// "text uc_figures");
  static std::string trNameClass ;// "name");
  static std::string tdNameValueClass ;// "name_value");
  static std::string trExecutedClass ;// "executed");
  static std::string tdExecutedValueClass ;// "executed_value");
  static std::string trUniqClass ;// "uniq");
  static std::string tdUniqTotalClass ;// "uc_total_uniq_tests");
  static std::string tdUniqValueClass ;// "uc_total_uniq_tests_value");
  static std::string trTimeClass ;// "time_used");
  static std::string tdTimeValueClass ;// "time_used_value");
  static std::string trAverageClass ;// "average");
  static std::string tdAverageValueClass ;// "average_value");
  static std::string trMinClass ;// "min");
  static std::string tdMinValueClass ;// "min_value");
  static std::string trMaxClass ;// "max");
  static std::string tdMaxValueClass ;// "max_value");
  static std::string divDetailedClass ;// "uc_detailed_results");
  static std::string divCountHeadClass ;// "uc_count_head");
  static std::string divStepsClass ;// "uc_steps");
  static std::string stylefile;//"<LINK href(\"fmbt.css\" rel(\"stylesheet\" type(\"text/css>\"");

};

#endif
