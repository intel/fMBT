/*
 * coverage_tema_seq, trace growing error trace minimizer
 * originally implemented in TEMA (tema.cs.tut.fi)
 * Copyright (c) 2011, Heikki Virtanen (heikki.virtanen@tut.fi)
 *
 * as part of
 *
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2011, Intel Corporation.
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms and conditions of the GNU Lesser General Public License,
 * version 2.1, as published by the Free Software Foundation.
 *
 * This program is distributed in the hope it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St - Fifth Floor, Boston,
 * MA 02110-1301 USA.
 *
 */
#ifndef __coverage_tema_seq_hh__
#define __coverage_tema_seq_hh__

/* Coverage module
 * keywords:  error trace minimizer, trace increment method
 *
 * Usage:
 * fmbt -L logfile.log bughunt.conf
 * fmbt-log -f '$as' logfile.log > full_trace.tr
 * fmbt -L minimizer.log minimizer.conf
 *
 * where the file minimizer.conf is same as bughunt.conf except for lines:
 *     heuristic    = "greedy:Xb"

 * where X is integer grater than 1, preferable more than width of the
 * model , and
 *     coverage = "tema_seq:full_trace.tr"
 *
 */

#include "coverage.hh"

class Coverage_Tema_seq: public Coverage {

public:
  Coverage_Tema_seq(Log &l, std::string params);

  virtual void push();
  virtual void pop();

  virtual void history(int action, std::vector<int>& props, 
		       Verdict::Verdict verdict);
  virtual bool execute(int action);
  virtual float getCoverage();

  virtual int fitness(int* actions,int n, float* fitness);

  virtual void set_model(Model* _model);

private:
  std::string a_trace_file_name;
  int a_trace_ptr;
  std::vector<int> a_trace;
  float a_step_coverage;
  std::vector<int> a_stack;
};

#endif
