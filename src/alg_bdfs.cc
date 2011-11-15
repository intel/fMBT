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

/* Implementation of Bounded Depth-First-Search for models with push()
 * and pop() */

#include "alg_bdfs.hh"
#include "model.hh"

int Alg_BDFS::path_to_state_with_action(const int find_me, Model& model, std::vector<int> &path, int depth)
{
    int *actions = NULL;
    int *input_actions = NULL;
    int action_count = 0;
    int input_action_count = 0;

    /* Can we still continue the search? */
    if (depth < 0) return -1;

    /* Is find_me in the current state? */
    action_count = model.getActions(&actions);
    for (int i = 0; i < action_count; i++)
    {
        if (actions[i] == find_me)
        {
            path.resize(0);
            return 0;
        }
    }
    
    /* Recursive search for the shortest path */
    input_action_count = model.getIActions(&input_actions);

    /* input_actions[] cannot be used in push-execute-pop due to
     * Lts_xrules::getIActions() implementation. We'll take a copy of
     * it into action_candidates. TODO: consider making getIActions()
     * safe or documenting a warning! */
    std::vector<int> action_candidates;
    for (int i = 0; i < input_action_count; i++)
        action_candidates.push_back(input_actions[i]);
    
    std::vector<int> shortest_path;
    int shortest_path_length = depth + 1;
    int best_action = -1;
    for (int i = 0; i < input_action_count; i++)
    {
        std::vector<int> a_path;
        int a_path_length;
        /* small optimisation: search only for paths that are shorter than the best path so far */
        int remaining_depth = depth < shortest_path_length ? depth - 1 : shortest_path_length - 1;
        model.push();        
        model.execute(action_candidates[i]);

        a_path_length = path_to_state_with_action(find_me, model, a_path, remaining_depth);
        model.pop();

        if (a_path_length != -1 &&
            a_path_length < shortest_path_length)
        {
            shortest_path_length = a_path_length;
            shortest_path = a_path;
            best_action = action_candidates[i]; // input_actions[i] does not work!
        }        
    }
    
    if (shortest_path_length <= depth)
    {
        path = shortest_path;
        path.push_back(best_action);
        return shortest_path_length + 1;
    }
    else
    {
        return -1;
    }
}
