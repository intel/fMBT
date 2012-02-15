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
} node;
#define D_ParseNode_User node
#include "of.hh"
OutputFormat* uconf_obj;
}

conf_file: model (usecase|testcase)+;

model: 'model' '=' string { uconf_obj->set_model(*$2.str); } ;

usecase: string '=' string { uconf_obj->add_uc(*$0.str,*$2.str); } ;

testcase: 'testcase' string ':' string opt_drop opt_completed { uconf_obj->add_start(*$1.str,*$3.str); };

opt_drop: | 'drop' ':' string { uconf_obj->add_drop(*$2.str); };

opt_completed: | 'completed' ':' string { uconf_obj->add_completed(*$2.str); };

string: "\"([^\"\\]|\\[^])*\"" { $$.str = new std::string($n0.start_loc.s+1,$n0.end-$n0.start_loc.s-2); } ;
