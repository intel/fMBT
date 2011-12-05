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

#include "coverage_tema_seq.hh"
#include "model.hh"
#include "helper.hh"

#include <iostream>
#include <fstream>
#include <cmath>

extern "C" {
  void abort();
}


Coverage_Tema_seq::Coverage_Tema_seq(Log &l, std::string params)
  : Coverage(l), a_trace_file_name(params), a_trace_ptr(0) {
}


namespace {
  int
  cur_trace_ptr(int tr_ptr, std::vector<int> &stack) {
    int ptr = (stack.size()>0) ? stack.back() : tr_ptr ;
    return ptr;
  }

  void
  advance_trace_ptr(int &tr_ptr, std::vector<int> &stack) {
    if( stack.size() > 0 ) ++(stack.back());
    else ++tr_ptr;
  }
}

void
Coverage_Tema_seq::push() {
  a_stack.push_back(cur_trace_ptr(a_trace_ptr, a_stack));
}

void
Coverage_Tema_seq::pop() {
  a_stack.pop_back();
}

bool
Coverage_Tema_seq::execute(int action) {
  int next_ptr = 1 + cur_trace_ptr(a_trace_ptr, a_stack);
  
  int base=1;
  int N=a_trace.size();
  for( ; base <= next_ptr ; base *= 2 ) { }
  if( base/2 > N ) base = base/2 + N;
  int idx = N+next_ptr-base;
  if( idx >= N ) return false;

  if( action == a_trace[idx] ) {
    advance_trace_ptr( a_trace_ptr, a_stack);
  }
  return true;
}

float
Coverage_Tema_seq::getCoverage() {
  return (a_step_coverage * cur_trace_ptr(a_trace_ptr, a_stack));
}

int
Coverage_Tema_seq::fitness(int* actions,int n, float* fitness) {
  std::cerr << __func__
	    << ": Used heuristic is not supported by tema_seq coverage"
	    << std::endl;
  std::cerr << __func__ << ": Use greedy:Xb, where X>1" << std::endl;
  abort();
  return 0;
}

void
Coverage_Tema_seq::set_model(Model* _model){
  Coverage::set_model(_model);

  typedef std::vector<std::string> alphabet_t;
  alphabet_t &alphabet(_model->getActionNames());

  typedef std::map<std::string,int> conversion_t;
  conversion_t conversion_table;

  int endi(alphabet.size());
  for( int idx = 1 ; idx < endi; ++idx ) {
    conversion_table[alphabet[idx]] = idx;
  }

  a_trace.clear();
  std::string cur_action;
  try {
    for( std::ifstream trace(a_trace_file_name.c_str());
	 std::getline(trace, cur_action) ; ) {
      int action = conversion_table.at(cur_action);
      a_trace.push_back(action);
    }
  } catch( std::out_of_range &) {
    std::cerr << "Alphabet mismatch at action " << cur_action << std::endl;
    abort();
  } catch( ... ) {
    std::cerr << "Trace file read error: " << a_trace_file_name << std::endl;
    abort();
  }
  a_step_coverage = 1.0 / ( 4 * ceil(a_trace.size()/2.0) );
}

FACTORY_DEFAULT_CREATOR(Coverage, Coverage_Tema_seq, "tema_seq");
