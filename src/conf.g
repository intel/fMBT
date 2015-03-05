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
#include <sstream>
typedef struct _node {
  int val;
  std::string* str;
  float f;
} node;

int conf_node_size = sizeof(node);

#define D_ParseNode_User node
#include "conf.hh"
#include "verdict.hh"
#include "end_condition.hh"
#include "random.hh"
Conf* conf_obj;
}

conf_file: conf_entry+;

conf_entry: model               |
            heuristic           |
            learning            |
            coverage            |
            adapter             |
            engine_cov          |
            engine_count        |
            engine_tag          |
            engine_time         |
            adapter_sleep       |
            end_condition       |
            history             |
            on_error            |
            on_fail             |
            on_pass             |
            on_inconc           |
            default_random      |
            tag_checking        ;

default_random: 'default' '[' 'random' ']' '=' string {
            Random::_default_random = new_random(*$5.str);
            if (!Random::_default_random) {
                printf("Can't create default random %s\n",$5.str->c_str());
            } else {
                if (!Random::_default_random->status) {
                    printf("Error in default random %s: %s\n",$5.str->c_str(),
                           Random::_default_random->errormsg.c_str());
                } else {
                    conf_obj->log.push("default");
                    conf_obj->log.print("<random init=\"%s\"/>\n",Random::_default_random->stringify().c_str());
                    conf_obj->log.pop();
                }
            }
            delete $5.str;
        } ;

tag_checking: 'disable_tag_checking' { conf_obj->disable_tagchecking(); } 
            | 'disable_tag_checking' '=' string { conf_obj->disable_tagchecking(*$2.str); delete $2.str; } ;

model: 'model' '=' string { conf_obj->set_model(*$2.str,$n2.start_loc.line); delete $2.str; } ;

heuristic: 'heuristic' '=' string { conf_obj->set_heuristic(*$2.str,$n2.start_loc.line); delete $2.str; } ;

learning: 'learn' '=' string { conf_obj->add_learning(*$2.str,$n2.start_loc.line); delete $2.str; } ;

coverage: 'coverage' '=' string { conf_obj->set_coverage(*$2.str,$n2.start_loc.line); delete $2.str; } ;

adapter: 'adapter' '=' string { conf_obj->set_adapter(*$2.str,$n2.start_loc.line); delete $2.str; } ;

engine_cov: 'engine.cov' '=' float {
            fprintf(stderr, "Warning: (test configuration) engine.cov is to be DEPRECATED. Use\n");
            fprintf(stderr, "pass = \"coverage:%f\"\n", $2.f);
            fprintf(stderr, "instead.\n");
            {
              std::ostringstream o;
              o << $2.f;
              std::string s(o.str());
              conf_obj->add_end_condition(
                new End_condition_coverage(conf_obj,Verdict::PASS, s));
              }
            } ;

engine_count: 'engine.count' '=' int {
            fprintf(stderr, "Warning: (test configuration) engine.count is to be DEPRECATED. Use\n");
            fprintf(stderr, "pass = \"steps:%d\"\n", $2.val);
            fprintf(stderr, "instead.\n");
            {
              std::ostringstream o;
              o << $2.val;
              std::string s(o.str());
              conf_obj->add_end_condition(
                new End_condition_steps(conf_obj,Verdict::PASS,s));
             }
            } ;

engine_tag: 'engine.tag' '=' string {
            fprintf(stderr, "Warning: (test configuration) engine.tag is to be DEPRECATED. Use\n");
            fprintf(stderr, "pass = \"statetag:%s\"\n", $2.str->c_str());
            fprintf(stderr, "instead.\n");
            conf_obj->add_end_condition(
                new End_condition_tag(conf_obj,Verdict::PASS, *$2.str));
            delete $2.str;
            } ;

engine_time: 'engine.endtime' '=' string {
            fprintf(stderr, "Warning: (test configuration) engine.endtime is to be DEPRECATED. Use\n");
            fprintf(stderr, "pass = \"duration:%s\"\n", $2.str->c_str());
            fprintf(stderr, "instead.\n");
            conf_obj->add_end_condition(
                new End_condition_duration(conf_obj,Verdict::PASS, *$2.str));
            delete $2.str;
            } ;

adapter_sleep: 'adapter.observesleep' '=' string { conf_obj->set_observe_sleep(*$2.str); delete $2.str; } ;

end_condition: verdict '=' string
        { conf_obj->add_end_condition((Verdict::Verdict)$0.val,*$2.str,$n2.start_loc.line); delete $2.str; }
        ;

history: 'history' '=' string { conf_obj->add_history($2.str,$n2.start_loc.line); };

on_fail: 'on_fail' '=' string { conf_obj->set_on_fail(*$2.str,$n2.start_loc.line); delete $2.str; };

on_pass: 'on_pass' '=' string { conf_obj->set_on_pass(*$2.str,$n2.start_loc.line); delete $2.str; };

on_inconc: 'on_inconc' '=' string { conf_obj->set_on_inconc(*$2.str,$n2.start_loc.line); delete $2.str; };

on_error: 'on_error' '=' string { conf_obj->set_on_error(*$2.str,$n2.start_loc.line); delete $2.str; };

verdict: pass {          $$.val=Verdict::PASS; }
        | fail {         $$.val=Verdict::FAIL; }
        | inconclusive { $$.val=Verdict::INCONCLUSIVE; }
        | notify       { $$.val=Verdict::NOTIFY; } ;

pass: 'pass' ;
fail: 'fail' ;
inconclusive: 'inconc' | 'inconclusive' | 'exit' ;
notify: 'notify' ;

string: "\"([^\"\\]|\\[^])*\"" {
            $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2);
            remove_force(*$$.str,'"');
        } |
        "\'([^\'\\]|\\[^])*\'" {
            $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2);
            remove_force(*$$.str,'\'');
        } |
        "[^\"\'][^\n]*\n" {
            $$.str = new std::string($n0.start_loc.s,$n0.end-$n0.start_loc.s-1);
        } ;

int: istr { $$.val = atoi($n0.start_loc.s); };

float: "[\-+]?([0-9]+\.[0-9]*|\.[0-9]+)([eE][\-+]?[0-9]+)?"
        {
            $$.f = atof($n0.start_loc.s);
        } | int { $$.f = $0.val; } ;


istr: "-?[0-9]+";
