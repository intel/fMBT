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

/* Implementation of Bounded Depth-First-Search for models and
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
    m_model->execute(action);

    m_coverage->push();
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
    /* Is find_me in the current state? */
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
    // The real algorithm constructs the best path in the opposite
    // direction to the path vector, this wrapper just reverses it.
    double score = _path_to_best_evaluation(model, path, depth);
    if (score != -1)
        reverse(path.begin(), path.end());
    return score;
}

double AlgBDFS::_path_to_best_evaluation(Model& model, std::vector<int>& path, int depth)
{
    int *input_actions = NULL;
    int input_action_count = 0;

    /* Can we still continue the search? */
    if (depth < 0) return evaluate();

    /* If maximum evaluation has been achieved, there is no need to
     * continue. */
    if (evaluate() == 1.0) return 1.0;

    /* Recursive search for the shortest path */
    input_action_count = model.getIActions(&input_actions);
    std::vector<int> action_candidates;
    for (int i = 0; i < input_action_count; i++)
        action_candidates.push_back(input_actions[i]);
    
    std::vector<int> best_path;
    unsigned int best_path_length = depth + 1;
    int best_action = -1;
    double best_evaluation = -1;
    for (int i = 0; i < input_action_count; i++)
    {
        std::vector<int> a_path;
        double an_evaluation;
        int remaining_depth;

        if (best_evaluation == 1.0) {
            /* small optimisation: if the best possible evaluation has
             * been found, search only paths that are strictly shorter
             * than the best path so far */
            remaining_depth = depth < (int)best_path_length ? depth - 1 : best_path_length - 1;
        } else {
            remaining_depth = depth - 1;
        }

        doExecute(action_candidates[i]);

        an_evaluation = _path_to_best_evaluation(model, a_path, remaining_depth);

        undoExecute();

        if (an_evaluation > best_evaluation ||
            (an_evaluation == best_evaluation
             && a_path.size() < best_path_length))
        {
            best_path_length = a_path.size();
            best_path = a_path;
            best_action = action_candidates[i];
            best_evaluation = an_evaluation;
        }
    }
    
    if (best_evaluation > -1) {
        path = best_path;
        path.push_back(best_action);
        return best_evaluation;
    } else {
        return -1;
    }
}
