{
/*
 * fMBT, free Model Based Testing tool
 * Copyright (c) 2012, Intel Corporation.
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
#include <vector>

#include "heuristic_weight.hh"

typedef struct _node {
  int val;
  std::string* str;
  std::vector<std::string*>* strvec;
} node;

int weight_node_size = sizeof(node);

//std::vector<std::string*> *ff,*tt,*dd;

#define D_ParseNode_User node

Heuristic_weight* Hw;

}

specs: spec |
       specs spec ;

spec: osvec ',' strvec operator int {
            Hw->add(*$0.strvec,*$2.strvec,$4.val,$3.val);
            delete $0.strvec;
            delete $2.strvec;
        }
    | '[' osvec ']' strvec operator int {
            Hw->add(*$1.strvec,*$3.strvec,$5.val,$4.val);
            delete $1.strvec;
            delete $3.strvec;
        }
    | strvec operator int {
            std::vector<std::string*>* tmp=new std::vector<std::string*>;
            Hw->add(*tmp,*$0.strvec,$2.val,$1.val);
            delete tmp;
            delete $0.strvec;
        };

operator: ':' { $$.val=0; } |
          '=' { $$.val=1; } ;

osvec: { $$.strvec = new std::vector<std::string*>; }
    | strvec { $$.strvec = $0.strvec; };

strvec: string { $$.strvec = new std::vector<std::string*>;
                 $$.strvec->push_back($0.str);
               }
    | strvec string {
            $$.strvec=$0.strvec;
            $$.strvec->push_back($1.str);
        } ;

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;

int: istr { $$.val = atoi($n0.start_loc.s); };

istr: "-?[0-9]+";
