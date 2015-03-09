{
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

#include <vector>
#include <stdlib.h>
#include <string>
typedef struct _node {
  int val;
  std::string* str;
} node;
#define D_ParseNode_User node

int lts_node_size = sizeof(node);

std::vector<int> oa;
std::vector<int> ia;
std::vector<int> os;
std::vector<int> is;
std::vector<int> intv;

#ifdef CAPI

#include "dparse.h"
#include "helper.hh"
#include <string.h>

extern D_ParserTables parser_tables_lts;

void (*set_state_cnt_cb)(int)                                 = 0;
void (*set_prop_cnt_cb)(int)                                  = 0;
void (*set_action_cnt_cb)(int)                                = 0;
void (*set_transition_cnt_cb)(int)                            = 0;
void (*set_initial_state_cb)(int)                             = 0;
void (*add_action_cb)(int, const char*)                       = 0;
void (*add_transition_cb)(int sstate, int aindex, int dstate) = 0;

extern "C" {
    int lts_state_cnt(void (*f)(int)) {
        set_state_cnt_cb = f;      return f != NULL; }

    int lts_prop_cnt(void (*f)(int)) {
        set_prop_cnt_cb = f;       return f != NULL; }

    int lts_action_cnt(void (*f)(int)) {
        set_action_cnt_cb = f;     return f != NULL; }

    int lts_transition_cnt(void (*f)(int)) {
        set_transition_cnt_cb = f; return f != NULL; }

    int lts_initial_state(void (*f)(int)) {
        set_initial_state_cb = f;  return f != NULL; }

    int lts_action(void (*f)(int, const char *)) {
        add_action_cb = f;         return f != NULL; }

    int lts_transition(void (*f)(int, int, int)) {
        add_transition_cb = f;     return f != NULL; }

    int lts_load(const char* filename) {
        D_Parser* p = new_D_Parser(&parser_tables_lts, lts_node_size);
        p->loc.pathname = filename;
        char* s = readfile(filename);
        dparse(p, s, strlen(s));
        int ret=p->syntax_errors;
        free(s);
        free_D_Parser(p);
        return ret;
    }
}

namespace lts_local {
    void add_prop(std::string* name,std::vector<int>& pr) {
    }

    void set_state_cnt(int count) {
        if (set_state_cnt_cb) set_state_cnt_cb(count);
    }
    void set_prop_cnt(int count) {
        if (set_prop_cnt_cb) set_prop_cnt_cb(count);
    }
    void set_action_cnt(int count) {
        if (set_action_cnt_cb) set_action_cnt_cb(count);
    }
    void set_transition_cnt(int count) {
        if (set_transition_cnt_cb) set_transition_cnt_cb(count);
    }
    void set_initial_state(int count) {
        if (set_initial_state_cb) set_initial_state_cb(count);
    }
    void add_action(int number, std::string& name) {
        if (add_action_cb) add_action_cb(number, name.c_str());
    }
    void add_transitions(int sstate, 
                        std::vector<int>& oa,
                        std::vector<int>& ia,
                        std::vector<int>& os,
                        std::vector<int>& is) {
        if (add_transition_cb) {
            for (unsigned int i = 0; i < ia.size(); i++) {
                add_transition_cb(sstate, ia[i], is[i]);
            }
        }
    }
    /* C API does not differentiate inputs and outputs */
    bool is_output(int) { return false; }
    void header_done() {}
    void precalc_input_output() {}
}

#define PREFIX lts_local::

#else /* (ifdef CAPI) parser for Lts class */

#include "lts.hh"
Lts* obj;

#define PREFIX obj->

#endif

}

lsts_file: 'Begin' 'Lsts' history header others+ 'End' 'Lsts' strings*;

others: action_names | transitions | state_prop;

history: | 'Begin' 'History' hist 'End' 'History';

hist: hist_lines*;

hist_lines: version strings;

state_prop: 'Begin' 'State_props'
            prop_line*
            'End' 'State_props';

prop_line: string ':' intv ';' { PREFIX add_prop($0.str,intv); intv.clear(); delete $0.str; $0.str=NULL; } ;

intv: ( int { intv.push_back($0.val); } )* ;


header: 'Begin' 'Header' header_variable+ ';' 'End' 'Header' { PREFIX header_done(); } ;

header_variable: 'State_cnt' '=' int { PREFIX set_state_cnt($2.val);      } |
          'State_prop_cnt'   '=' int { PREFIX set_prop_cnt($2.val);       } |
 		  'Action_cnt'       '=' int { PREFIX set_action_cnt($2.val);     } |
 		  'Transition_cnt'   '=' int { PREFIX set_transition_cnt($2.val); } |
 		  'Initial_states'   '=' int { PREFIX set_initial_state($2.val);  };

action_names: 'Begin' 'Action_names'
	      action_name_line*
	      'End' 'Action_names' { PREFIX precalc_input_output(); } ;

action_name_line: int '=' string {
                                   PREFIX add_action($0.val,*$2.str); 
                                   delete $2.str;
                                   $2.str=NULL;
                                 } ;

transitions:
	'Begin' 'Transitions'
	transition_line*
	'End' 'Transitions';

transition_line:
	int ':' pair* ';' { PREFIX add_transitions($0.val,oa,ia,os,is);
                        oa.clear(); ia.clear();os.clear();is.clear(); };

pair: int ',' int {
    if (PREFIX is_output($2.val)) {
      oa.push_back($2.val);
      os.push_back($0.val);
    } else {
      // input...
      ia.push_back($2.val);
      is.push_back($0.val);      
    }
  } ;

version: int | int '.' int;

strings: stringi+;

stringi: "\"([^\"\\]|\\[^])*\"";

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

int: istr { $$.val = atoi($n0.start_loc.s); };

istr: "[0-9]+";
