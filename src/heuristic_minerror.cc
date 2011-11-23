#include "heuristic_minerror.hh"
#include "alg_bdfs.hh"
#include "model.hh"

#include <stdio.h>
#include <glib.h>
#include <sstream>
#include <vector>
#include <string.h>

#define debugprint(args ...) fprintf(stderr, args)

Heuristic_minerror::Heuristic_minerror(Log& l, std::string params):
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
            add_arming_trace(trace, 0, key_action_position - 1);
        } else  {
            debugprint("WARNING: different key actions: old: \"%s\", new: \"%s\"\n",
                       getActionName(m_key_action).c_str(),
                       getActionName(key_action).c_str());
            key_action = m_key_action; // look for more info related to the old key_action
        }

        for (int i = 0; i < key_action_position; i++)
        {
            if (trace[i] == key_action)
                add_not_arming_trace(trace, 0, i-1);
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
                add_not_arming_trace(trace, 0, i-1);
        }
    }
}

void Heuristic_minerror::add_not_arming_trace(std::vector<int>& trace, int trace_begin, int trace_end)
{
    
}

void Heuristic_minerror::add_arming_trace(std::vector<int>& trace, int trace_begin, int trace_end)
{
    
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
    return 1;
}

FACTORY_DEFAULT_CREATOR(Heuristic, Heuristic_minerror, "minerror")
