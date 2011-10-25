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
#include <stdlib.h>
#include <string>
typedef struct _node {
  int val;
  std::string* str;
} node;
#define D_ParseNode_User node
#include "lts.hh"
Lts* obj;

std::vector<int> oa;
std::vector<int> ia;
std::vector<int> os;
std::vector<int> is;

}

lsts_file: 'Begin' 'Lsts' history header others+ 'End' 'Lsts' strings*;

others: action_names | transitions | state_prop;

history: | 'Begin' 'History' hist 'End' 'History';

hist: hist_lines*;

hist_lines: version strings;

state_prop: 'Begin' 'State_props'
            prop_line*
            'End' 'State_props';

prop_line: string ':' int* ';' ;

header: 'Begin' 'Header' header_variable+ ';' 'End' 'Header' { obj->header_done(); } ;

header_variable: 'State_cnt' '=' int { obj->set_state_cnt($2.val);      } |
          'State_prop_cnt'   '=' int { obj->set_prop_cnt($2.val);       } |
 		  'Action_cnt'       '=' int { obj->set_action_cnt($2.val);     } |
 		  'Transition_cnt'   '=' int { obj->set_transition_cnt($2.val); } |
 		  'Initial_states'   '=' int { obj->set_initial_state($2.val);  };

action_names: 'Begin' 'Action_names'
	      action_name_line*
	      'End' 'Action_names' { obj->precalc_input_output(); } ;

action_name_line: int '=' string {
                                   obj->add_action($0.val,*$2.str); 
                                   delete $2.str;
                                   $2.str=NULL;
                                 } ;

transitions:
	'Begin' 'Transitions'
	transition_line*
	'End' 'Transitions';

transition_line:
	int ':' pair* ';' { obj->add_transitions($0.val,oa,ia,os,is);
                        oa.clear(); ia.clear();os.clear();is.clear(); };

pair: int ',' int {
    if (obj->is_output($2.val)) {
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
