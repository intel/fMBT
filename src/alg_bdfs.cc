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
    m_model->push();
    m_coverage->push();

    m_model->execute(action);
    m_coverage->execute(action);
}

void AlgPathToBestCoverage::undoExecute()
{
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
    double current_score = evaluate();
    double best_score = _path_to_best_evaluation(model, path, depth, current_score);

    if (best_score > current_score) {
        // The real algorithm constructs the best path in the opposite
        // direction to the path vector, this wrapper reverses it.
        reverse(path.begin(), path.end());
    } else {
        path.resize(0);
    }
    return best_score;
}

bool AlgBDFS::grows_first(std::vector<int>& first_path, int first_path_start,
                          std::vector<int>& second_path, int second_path_start)
{
    if (first_path.size() != second_path.size()) abort();
    
    double path1eval;
    double path2eval;

    doExecute(first_path_start);
    path1eval = evaluate();
    undoExecute();

    doExecute(second_path_start);
    path2eval = evaluate();
    undoExecute();

    if (path1eval > path2eval) return true;
    else if (path1eval < path2eval) return false;

    if (first_path.size() == 0) return false;
    else if (second_path.size() == 0) return false;
    else
    {
        std::vector<int> new_first_rest = first_path;
        std::vector<int> new_second_rest = second_path;
        first_path_start = new_first_rest.back();
        second_path_start = new_second_rest.back();
        new_first_rest.pop_back();
        new_second_rest.pop_back();
        return grows_first(new_first_rest, first_path_start,
                           new_second_rest, second_path_start);
    }
}

double AlgBDFS::_path_to_best_evaluation(Model& model, std::vector<int>& path, int depth,
                                         double best_evaluation)
{
    int *input_actions = NULL;
    int input_action_count = 0;

    double current_state_evaluation = evaluate();

    if (current_state_evaluation > best_evaluation)
        best_evaluation = current_state_evaluation;

    /* Can we still continue the search? */
    if (depth <= 0)
        return current_state_evaluation;

    /* If maximum evaluation has been achieved, there is no need to
     * continue. */
    if (current_state_evaluation == 1.0)
        return current_state_evaluation;

    /* Recursive search for the best path */
    input_action_count = model.getIActions(&input_actions);
    std::vector<int> action_candidates;
    for (int i = 0; i < input_action_count; i++)
        action_candidates.push_back(input_actions[i]);
    
    std::vector<int> best_path;
    unsigned int best_path_length = 0;
    int best_action = -1;
    for (int i = 0; i < input_action_count; i++)
    {
        std::vector<int> a_path;
        double an_evaluation;

        doExecute(action_candidates[i]);

        an_evaluation = _path_to_best_evaluation(model, a_path, depth - 1, best_evaluation);

        undoExecute();

        if (an_evaluation > best_evaluation ||
            (an_evaluation == best_evaluation && 
             (best_action == -1 ||
              (best_action > -1 &&
               (a_path.size() < best_path_length ||
                (a_path.size() == best_path_length &&
                 grows_first(a_path, action_candidates[i], best_path, best_action)))))))
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
