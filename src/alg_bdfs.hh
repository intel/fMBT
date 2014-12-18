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

class Coverage;
class Learning;
class Model;
class Function;

#include <vector>
#include "writable.hh"

class AlgBDFS: public Writable
{
public:
    AlgBDFS(int searchDepth, Learning* learn,Function* function);
    virtual ~AlgBDFS() {};

    /** \brief returns the shortest path that results in  the best evaluation
     * \param model (input parameter) search starts from model's current state
     * \param path (output parameter) the best path if one was found, otherwise empty
     * \return the evaluation value for the path
     */
    double path_to_best_evaluation(Model& model, std::vector<int>& path, int depth);

protected:
    virtual double evaluate() = 0;
    virtual void doExecute(int action) = 0;
    virtual void undoExecute() = 0;
    int m_search_depth;
    bool m_learn_exec_times;
    Learning*  m_learn;
    Function* m_function;
    double _path_to_best_evaluation(Model& model, std::vector<int>& path, int depth, double best_evaluation);
    bool grows_first(std::vector<int>&, int, std::vector<int>&, int);
    bool grows_faster(std::vector<int>&, int, std::vector<int>&, int);
};


class AlgPathToBestCoverage: public AlgBDFS
{
public:
    AlgPathToBestCoverage(int searchDepth = 3, Learning* learn = NULL, Function* function = NULL):
      AlgBDFS(searchDepth, learn,function) {}
    virtual ~AlgPathToBestCoverage() {};

    double search(Model& model, Coverage& coverage, std::vector<int>& path);
protected:
    virtual double evaluate();
    virtual void doExecute(int action);
    virtual void undoExecute();
    Coverage* m_coverage;
    Model*    m_model;
};


class AlgPathToAdaptiveCoverage: public AlgPathToBestCoverage
{
public:
    AlgPathToAdaptiveCoverage(int searchDepth = 3, Learning* learn = NULL, Function* function = NULL):
      AlgPathToBestCoverage(searchDepth, learn) {}
    virtual ~AlgPathToAdaptiveCoverage() {};
protected:
    double _path_to_best_evaluation(Model& model, std::vector<int>& path, int depth, double best_evaluation);
};


class AlgPathToAction: public AlgBDFS
{
public:
    AlgPathToAction(int searchDepth = 3, Learning* learn = NULL, 
		    Function* function = NULL):
      AlgBDFS(searchDepth, learn,function) {}
    virtual ~AlgPathToAction() {}

    double search(Model& model, int find_this_action, std::vector<int>& path);
protected:
    virtual double evaluate();
    virtual void doExecute(int action);
    virtual void undoExecute();
    Model* m_model;
    int    m_find_this_action;
};

#endif
