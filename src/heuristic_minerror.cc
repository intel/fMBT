#include "heuristic_minerror.hh"
#include "alg_bdfs.hh"
#include "model.hh"

#include <stdio.h>
#include <glib.h>
#include <sstream>
#include <vector>
#include <string.h>

#define debugprint(args ...) fprintf(stderr, args)

Heuristic_minerror::Heuristic_minerror(Log& l,const std::string& params):
    Heuristic::Heuristic(l, params),
    m_search_depth(6),
    m_key_action(-1)

{
    m_logfilename = params;
}

void Heuristic_minerror::set_model(Model* _model)
{
    Heuristic::set_model(_model);

    gchar* _stdout=NULL;
    gchar* _stderr=NULL;
    gint   exit_status=0;
    GError *ger=NULL;
    std::string cmd("fmbt-log -f $sn$tv:$as ");
    cmd += m_logfilename;
    g_spawn_command_line_sync(cmd.c_str(),&_stdout,&_stderr,
                              &exit_status,&ger);
    if (!_stdout) {
        errormsg = std::string("Heuristic_minerror cannot execute \"") + cmd + "\"";
        status = false;
    } else {
        parse_traces(_stdout);
        g_free(_stdout);
        g_free(_stderr);
        g_free(ger);
    }

}

void Heuristic_minerror::parse_traces(char* log_contents)
{
    std::stringstream ss(log_contents);
    std::vector<int> trace;
    char parsed_action_name[1024];
    char parsed_step[16];
    
    while (!ss.eof())
    {
        ss.getline(parsed_step, 16, ':');
        ss.getline(parsed_action_name, 1024);

        if (strncmp(parsed_step, "fail", 4) == 0) {
            parsed_trace(trace, true);
            trace.resize(0);
        } else if (strncmp(parsed_step, "pass", 4) == 0) {
            parsed_trace(trace, false);
            trace.resize(0);
        } else {
            std::string name(parsed_action_name);
            int n = model->action_number(name);
            if (n == -1) {
                debugprint("Action \"%s\" not found in the model.\n", parsed_action_name);
                errormsg = std::string("Action \"") + parsed_action_name + "\" in "
                    + m_logfilename + "not found in the model.";
                status = -1;
            } else {
                trace.push_back(n);
            }
        }
    }
}

void Heuristic_minerror::parsed_trace(std::vector<int>& trace, bool is_error_trace)
{
    if (is_error_trace && trace.size() > 0)
    {
        int key_action_position = trace.size() - 1;
        int key_action = trace[key_action_position];

        if (m_key_action == -1) m_key_action = key_action;

        /* This prototype works efficiently with only one key_action,
           something to be enhanced later. */
        if (m_key_action == key_action) {
            add_arming_subtrace(trace, 0, key_action_position - 1);
        } else  {
            debugprint("WARNING: different key actions: old: \"%s\", new: \"%s\"\n",
                       getActionName(m_key_action).c_str(),
                       getActionName(key_action).c_str());
            key_action = m_key_action; // look for more info related to the old key_action
        }

        for (int i = 0; i < key_action_position; i++)
        {
            if (trace[i] == key_action)
                add_not_arming_subtrace(trace, 0, i-1);
        }
    }
    else if (!is_error_trace)
    {
        if (m_key_action == -1) {
            debugprint("WARNING: key action not defined, skipping a passing trace.");
        }
        for (unsigned int i = 0; i < trace.size(); i++)
        {
            if (trace[i] == m_key_action)
                add_not_arming_subtrace(trace, 0, i-1);
        }
    }
}

void Heuristic_minerror::add_not_arming_subtrace(std::vector<int>& trace, int trace_begin, int trace_end)
{
    for (int i = trace_end; i >= trace_begin; i--)
    {
        std::vector<int> subtrace;
        std::map<std::vector<int>, double>::iterator it;
        subtrace.assign(trace.begin() + i, trace.begin() + trace_end);
        it = m_subtrace2prob.find(subtrace);

        if (it == m_subtrace2prob.end()) {
            m_subtrace2prob[subtrace] = 0;
            
            debugprint("added: 0 == "); for (unsigned int j = 0; j < subtrace.size(); j++) debugprint("%d ", subtrace[j]); debugprint("\n");
        }
        else
        {
            debugprint("subtrace already exists");
        }
    }
}

void Heuristic_minerror::add_arming_subtrace(std::vector<int>& trace, int trace_begin, int trace_end)
{
    debugprint("arming trace: "); for (int j = 0; j <= trace_end; j++) debugprint("%d ", trace[j]); debugprint("\n");
    const int max_key_actions = 2;
    std::vector<int> candidate_indexes;
    
    for (int num_of_key_actions = 1; // don't include zero-length - though it should be there!
         num_of_key_actions <= max_key_actions; num_of_key_actions++)
    {
        if (trace_begin > trace_end - num_of_key_actions) break;

        candidate_indexes.resize(num_of_key_actions);

        for (int i = 0; i < num_of_key_actions; i++)
            candidate_indexes[i] = trace_end - i;
        
        while (1) {
            std::vector<int> candidates;
            candidates.resize(num_of_key_actions);
            for (unsigned int i = 0; i < candidate_indexes.size(); i++)
                candidates[num_of_key_actions-i-1] = trace[candidate_indexes[i]];

            if (m_key_action_candidates.find(candidates) == m_key_action_candidates.end())
            {
                m_key_action_candidates.insert(candidates);
                debugprint("candidates: "); for (unsigned int j = 0; j < candidates.size(); j++) debugprint("%d ", candidates[j]); debugprint("\n");
            }

            // pick next candidate_indexes
            int dec_this_index = num_of_key_actions - 1;
            while (dec_this_index >= 0) {
                if (candidate_indexes[dec_this_index] >= trace_begin + num_of_key_actions - 1) {
                    candidate_indexes[dec_this_index]--;
                    for (int i = dec_this_index + 1; i < num_of_key_actions; i++)
                        candidate_indexes[i] = candidate_indexes[i-1] - 1;
                    break;
                }
                dec_this_index --;
            }
            if (dec_this_index < 0 || candidate_indexes[num_of_key_actions-1] < trace_begin)
                break;
        }
    }
}


bool Heuristic_minerror::execute(int action)
{
    return false;
}

float Heuristic_minerror::getCoverage()
{
    return 0.0;
}

int Heuristic_minerror::getAction()
{
    return 1;
}

int Heuristic_minerror::getIAction()
{
    if (m_current_trace.empty())
    {
        suggest_new_path();
    }
    return 1;
}

void Heuristic_minerror::suggest_new_path()
{
    /* clean up bad key action candidates */
    for (std::set<std::vector<int> >::iterator cand_iter = m_key_action_candidates.begin();
         cand_iter != m_key_action_candidates.end();
         cand_iter++)
    {
        if ((*cand_iter).empty()) continue;
        for (std::map<std::vector<int>, double>::iterator subtrace_iter = m_subtrace2prob.begin();
             subtrace_iter != m_subtrace2prob.end();
             subtrace_iter++)
        {
            // If all key action candidates exist in the same
            // non-arming trace in the same order, remove they can't
            // be key actions. (This assumption does not take into
            // account possibility of disarming traces, so it might
            // be removing key action candidates too eagerly.)
            unsigned int cand_pos = 0;
            for (unsigned int trace_pos = 0; trace_pos < subtrace_iter->first.size(); trace_pos++) {
                if (subtrace_iter->first[trace_pos] == (*cand_iter)[cand_pos]) {
                    cand_pos++;
                    if (cand_pos >= (*cand_iter).size()) {
                        m_key_action_candidates.erase(cand_iter);
                        break;
                    }
                }
            }
        }
    }

    // DEBUG print remaining candidates
    for (std::set<std::vector<int> >::iterator cand_iter = m_key_action_candidates.begin();
         cand_iter != m_key_action_candidates.end();
         cand_iter++)
    {
        debugprint("remaining candidate: "); for (unsigned int j = 0; j < (*cand_iter).size(); j++) debugprint("%d ", (*cand_iter)[j]); debugprint("\n");

        int step = 1;
        model->push();
        for (unsigned int actnum = 0; actnum < (*cand_iter).size(); actnum++) {
            std::vector<int> path;
            AlgPathToAction alg(4);
            alg.search(*model, (*cand_iter)[actnum], path);
            debugprint("path:\n");
            for (unsigned int i=0; i < path.size(); i++) {
                debugprint("    %d %s\n", step++, getActionName(path[i]).c_str());
                model->execute(path[i]);
            }
            debugprint("    %d %s\n", step++, getActionName( (*cand_iter)[actnum]).c_str());
            model->execute((*cand_iter)[actnum]);
        }
        model->pop();
    }

    if (m_key_action_candidates.empty()) return;
    
    std::vector<int> chosen = *(++m_key_action_candidates.begin());
    
    debugprint("chosen candidate: ");
    for (unsigned int i=0; i < chosen.size(); i++)
        debugprint("%s ", getActionName(chosen[i]).c_str());
    debugprint("\n");
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_minerror, "minerror")
