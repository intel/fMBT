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
  float f;
} node;
#define D_ParseNode_User node
#include "conf.hh"
Conf* conf_obj;
}

conf_file: conf_entry+;

conf_entry: model         |
            heuristic     |
            coverage      |
            adapter       |
            engine_cov    |
            engine_count  |
            engine_tag    |
            engine_time   |
            adapter_sleep |
            history       |
            on_error      ;

model: 'model' '=' string { conf_obj->set_model(*$2.str); } ;

heuristic: 'heuristic' '=' string { conf_obj->set_heuristic(*$2.str); } ;

coverage: 'coverage' '=' string { conf_obj->set_coverage(*$2.str); } ;

adapter: 'adapter' '=' string { conf_obj->set_adapter(*$2.str); } ;

engine_cov: 'engine.cov' '=' float { conf_obj->set_engine_cov($2.f); } ;

engine_count: 'engine.count' '=' int { conf_obj->set_engine_count($2.val); };

engine_tag: 'engine.tag' '=' string { conf_obj->set_engine_tag(*$2.str); } ;

engine_time: 'engine.endtime' '=' string { conf_obj->set_end_time(*$2.str); } ;

adapter_sleep: 'adapter.observesleep' '=' string { conf_obj->set_observe_sleep(*$2.str); } ;

history: 'history' '=' string { conf_obj->add_history($2.str); };

on_error: 'on_error' '=' string { conf_obj->set_on_error(*$2.str); };

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); };

int: istr { $$.val = atoi($n0.start_loc.s); };

float: "[\-+]?([0-9]+\.[0-9]*|\.[0-9]+)([eE][\-+]?[0-9]+)?" 
        {
            $$.f = atof($n0.start_loc.s);
        } | int { $$.f = $0.val; } ;


istr: "-?[0-9]+";
