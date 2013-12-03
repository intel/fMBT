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

/* Implementations of Bounded Depth-First-Search for models and
 * coverages with push() and pop() */

#include "alg_bdfs.hh"
#include "model.hh"
#include "coverage.hh"
#include <algorithm>
#include <cstdlib>
#include "helper.hh"
extern int _g_simulation_depth_hint;

double AlgPathToBestCoverage::search(Model& model, Coverage& coverage, std::vector<int>& path)
{
    m_coverage = &coverage;
    m_model = &model;
    return path_to_best_evaluation(model, path, m_search_depth);
}

double AlgPathToBestCoverage::evaluate()
{
    return m_coverage->getCoverage();
}

void AlgPathToBestCoverage::doExecute(int action)
{
    if (!status) {
        return;
    }

    m_model->push();
    m_coverage->push();

    if (!m_model->execute(action)) { errormsg="Model execute error"; status=false; return;}
    m_coverage->execute(action);
}

void AlgPathToBestCoverage::undoExecute()
{
    if (!status) {
        return;
    }

    m_model->pop();
    m_coverage->pop();
}

double AlgPathToAction::search(Model& model, int find_this_action, std::vector<int> &path)
{
    m_model = &model;
    m_find_this_action = find_this_action;
    return path_to_best_evaluation(model, path, m_search_depth);
}

double AlgPathToAction::evaluate()
{
    int *actions;
    int action_count;
    /* Is action m_find_this_action available in the current state? */
    action_count = m_model->getActions(&actions);

    if (!status) {
        return 0.0;
    }

    for (int i = 0; i < action_count; i++)
    {
        if (actions[i] == m_find_this_action) return 1.0;
    }
    return 0.0;
}

void AlgPathToAction::doExecute(int action)
{
    m_model->push();
    m_model->execute(action);
}

void AlgPathToAction::undoExecute()
{
    m_model->pop();
}

double AlgBDFS::path_to_best_evaluation(Model& model, std::vector<int>& path, int depth)
{
    volatile double current_score = evaluate();
    volatile double best_score = 0;
    std::vector<int> hinted_path;

    if (!model.status || !status) {
        if (!model.status)
	  errormsg = "Model error:"+model.errormsg;
        status=false;
        return 0.0;
    }

    _g_simulation_depth_hint = depth;
    model.push();
    _g_simulation_depth_hint = 0;

    if (path.size() > 0) {
        // Path includes a hint to look at this path at first before
        // considering others.
        //
        // Evaluating the hinted options first has too effects:
        //
        // - If one path has been chosen earlier, it's preferred to
        //   continue execution that way instead of switching it to
        //   another path that seems to be as good as the
        //   original. This prevents oscillation between equally good
        //   paths.
        //
        // - If maximal growth rate is known, search starting with a
        //   good "so far best score" is able to drop unnecessary
        //   lookups. (Not implemented)

        int invalid_step = -1;
        for (unsigned int pos = 0; pos < path.size() && invalid_step == -1; pos++) {
            doExecute(path[pos]);
            if (status == false) {
                invalid_step = pos;
                status = true;
            }
            if (!model.status) {
                status = false;
		errormsg = "Model:" + model.errormsg;
                return 0.0;
            }
        }

        if (invalid_step > -1) {
            // Hinted path is no more valid, throw it away.
            path.resize(0);
            for (int current_step = invalid_step; current_step > -1; current_step--)
                undoExecute();
        } else {
            std::vector<int> additional_path;

            best_score = _path_to_best_evaluation(model, additional_path, depth - path.size(), current_score);

            if (!model.status || !status) {
	      if (!model.status)
		errormsg = "Model error:"+model.errormsg;
	      status=false;
	      return 0.0;
            }

            for (unsigned int i = 0; i < path.size(); i++) undoExecute();

            if (!model.status || !status) {
	      if (!model.status)
		errormsg = "Model error:"+model.errormsg;
	      status=false;
	      return 0.0;
            }

            if (best_score > current_score) {
                hinted_path = path;
                for (int i = additional_path.size() - 1; i >= 0; i--)
                    hinted_path.push_back(additional_path[i]);
                current_score = best_score;
            }
        }
    }

    best_score = _path_to_best_evaluation(model, path, depth, current_score);
    model.pop();

    if (!model.status || !status) {
      if (!model.status)
	errormsg = "Model error:"+model.errormsg;
      status=false;
      return 0.0;
    }

    if (best_score > current_score || (
            best_score == current_score &&
            path.size() < hinted_path.size())) {
        // The real algorithm constructs the best path in the opposite
        // direction to the path vector, this wrapper reverses it.
        std::reverse(path.begin(), path.end());
    } else if (hinted_path.size() > 0) {
        path = hinted_path;
    } else {
        path.resize(0);
    }
    return best_score;
}

bool AlgBDFS::grows_first(std::vector<int>& first_path, int first_path_start,
                          std::vector<int>& second_path, int second_path_start)
{
    if (first_path.size() != second_path.size()) {
      errormsg="first_path.size() != second_path.size()";
      status=false;
      return false;
    }

    volatile double current_score = evaluate();

    first_path.push_back(first_path_start);
    second_path.push_back(second_path_start);

    int first_difference = first_path.size();
    for (int i = first_path.size() - 1; i >= 0; i--) {
        doExecute(first_path[i]);
        volatile double score = evaluate();

        if (!status) {
          return false;
        }

        if (score > current_score) {
            first_difference = i;
            break;
        }
    }
    if (first_difference == (int)first_path.size()) {
      errormsg = "first_difference == (int)first_path.size() "+to_string(first_difference);
      status=false; return false;
    }

    for (int j = first_path.size() - 1; j >= first_difference; j--) undoExecute();

    int second_difference = second_path.size();
    for (int i = second_path.size() - 1; i >= 0; i--) {
        doExecute(second_path[i]);
        volatile double score = evaluate();
        if (score > current_score) {
            second_difference = i;
            break;
        }
    }
    if (second_difference == (int)second_path.size()) {
      errormsg = "second_difference == (int)second_path.size()";
      status=false; return false;
    }

    for (int j = second_path.size() - 1; j >= second_difference; j--) undoExecute();

    first_path.pop_back();
    second_path.pop_back();

    if (first_difference > second_difference) return true;
    else return false;
}

double AlgBDFS::_path_to_best_evaluation(Model& model, std::vector<int>& path, int depth,
                                         double best_evaluation)
{
    int *input_actions = NULL;
    int input_action_count = 0;

    if (!status) {
        return 0.0;
    }

    volatile double current_state_evaluation = evaluate();

    if (current_state_evaluation > best_evaluation)
        best_evaluation = current_state_evaluation;

    /* Can we still continue the search? */
    if (depth <= 0)
        return current_state_evaluation;

    /* Recursive search for the best path */
    input_action_count = model.getIActions(&input_actions);

    if (!model.status) {
      errormsg = "Model error:"+model.errormsg;
        status=false;
        return 0.0;
    }

    std::vector<int> action_candidates;
    for (int i = 0; i < input_action_count; i++)
        action_candidates.push_back(input_actions[i]);

    std::vector<int> best_path;
    unsigned int best_path_length = 0;
    int best_action = -1;
    for (int i = 0; i < input_action_count; i++)
    {
        std::vector<int> a_path;
        volatile double an_evaluation;

        doExecute(action_candidates[i]);

        a_path.resize(0);
        an_evaluation = _path_to_best_evaluation(model, a_path, depth - 1, best_evaluation);

        undoExecute();

        if (!model.status || !status) {
	  if (!model.status)
	    errormsg = "Model error:"+model.errormsg;
          status=false;
          return 0.0;
        }

        if (an_evaluation > current_state_evaluation &&
            (an_evaluation > best_evaluation ||
             (an_evaluation == best_evaluation &&
              (best_action == -1 ||
               (best_action > -1 &&
                (a_path.size() < best_path_length ||
                 (a_path.size() == best_path_length &&
                  grows_first(a_path, action_candidates[i], best_path, best_action))))))))
        {
            best_path_length = a_path.size();
            best_path = a_path;
            best_action = action_candidates[i];
            best_evaluation = an_evaluation;
        }
    }

    if ((int)best_action > -1) {
        path = best_path;
        path.push_back(best_action);
        return best_evaluation;
    }
    return current_state_evaluation;
}
