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

/* Declaration of bounded depth-first-search for models with push()
 * and pop() */

#ifndef __alg_bdfs_hh__
#define __alg_bdfs_hh__

class Model;

#include <vector>

class Alg_BDFS {
public:
    /** \brief return path to a state where action can be executed
     * \param action (input) to be executed
     * \param model (input) search starts from its current state
     * \param path (output) actions on the path to the state
     * \return length of the path if found, otherwise -1
     */
    static int path_to_state_with_action(const int find_me, Model& model, std::vector<int>& path, int depth);
};

#endif
