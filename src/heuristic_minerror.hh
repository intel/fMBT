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

/*
 * This is a prototype heuristic for minimising error traces.
 *
 * Usage: minerror:testlogfile
 *
 * Requirements:
 *
 * - test model that resets the SUT and its test environment when
 *   execution is started from the initial state.
 *
 * Background theory
 *
 * Assume [a_1, ..., a_n, x] is a sequence of input actions. "x" is
 * the action after which fMBT detects an error in the SUT.
 *
 * [a_1, ..., a_n] as an "arming" trace. After executing it the SUT is
 * "armed": all that is needed is to try executing input "x" to
 * trigger the error in the SUT.
 *
 * Arming trace includes "key" input actions. Without executing the
 * key actions the trace would not arm the SUT.
 *
 * Algorithm
 *
 * Minerror algorithm searches for a minimal arming trace by trying to
 * find key actions in already known arming traces. After picking up
 * key action candidates, the algorithm searches for minimal paths in
 * the test model to execute the key actions and finally the
 * triggering action "x".
 *
 * Heuristics
 *
 * The algorithm uses heuristics to estimate probability of a trace
 * being an unseen arming trace. The heuristics gathers information of
 * subtraces (traces starting from any state of the test model)
 * executing which from a state of the test model does not arm the
 * SUT. For instance,
 *
 * - if [a_1, ..., a_n, x] is an error trace, and
 * 
 * - if for some i, 1 <= i <= n there is a_i == x in the trace,
 *
 * then it's already known that
 *
 * - [a_1, ..., a_(i-1)] is not an arming trace,
 *
 * - [a_2, ..., a_(i-1)] is not an arming subtrace,
 *
 * - ...
 *
 * - [a_(i-2), a_(i-1)]  is not an arming subtrace,
 *
 * - [a_(i-1)]           is not an arming subtrace.
 *
 * Heuristics prefer testing potential arming traces bring most of new
 * information to not-arming subtraces.
 *
 */

#ifndef __heuristic_minerror_hh__
#define __heuristic_minerror_hh__

#include <vector>
#include <string>
#include <set>

#include "heuristic.hh"
#include "coverage.hh"

class Heuristic_minerror : public Heuristic {
public:
  Heuristic_minerror(Log& l, std::string params = "");

  virtual bool execute(int action);

  virtual float getCoverage();
  virtual int getAction();
  virtual int getIAction();

  virtual void set_model(Model* _model);

protected:
  void parse_traces(char *log_contents);

  /* parsed_trace is called by parse_traces for every trace found in
   * the input. If test was passed, errortrace == false, otherwise
   * true. If the trace is stored, copy it! */
  virtual void parsed_trace(std::vector<int>& trace, bool is_error_trace);

  virtual void add_not_arming_subtrace(std::vector<int>& trace, int trace_begin, int trace_end);
  virtual void add_arming_subtrace(std::vector<int>& trace, int trace_begin, int trace_end);

  virtual void suggest_new_path();
  
  int m_search_depth;
  int m_key_action;
  std::string m_logfilename;

  std::vector<int> m_current_trace;

  std::map<std::vector<int>, double> m_subtrace2prob;
  std::set<std::vector<int> > m_key_action_candidates;
};

#endif
