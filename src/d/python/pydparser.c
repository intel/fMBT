/* Copyright (c) 2003, 2004 Brian Sabbey */
#include <Python.h>
#include "pydparser.h"
#include "swigpyrun.h"

#define d_interface(_p) ((D_ParserPyInterface*)((Parser*)_p)->pinterface1)
#define d_dpt(_p) (((Parser*)_p)->t)

static int my_final_action(void *new_ps, void **children, int n_children, int pn_offset,
			   struct D_Parser *parser);
static int my_speculative_action(void *new_ps, void **children, int n_children, int pn_offset,
				 struct D_Parser *parser); 
static PyObject *make_pyobject_from_node(D_Parser *parser, D_ParseNode *d, int string);

typedef struct D_ParserPyInterface {
  PyObject *reject;
  PyObject *actions;
  PyObject *initial_white_space_fn;
  PyObject *syntax_error_fn;
  PyObject *ambiguity_fn;
  PyObject *loc_type;
  PyObject *make_token;
  PyObject *node_info_type;
  PyObject *symbol_list;
  PyObject *self;
  int print_debug_info;
  int takes_strings;
  int takes_globals;
  char *buf_start;         /* for converting from char* to string index */
  PyObject *py_buf_start;
  /* for deallocation purposes */ 
  int num_parse_tree_viewers;    
  D_ParseNode *top_node; 
  int parsing;

} D_ParserPyInterface;

static void 
free_node_fn(D_ParseNode *d) {
  Py_XDECREF((PyObject*)d->user.t);
  Py_XDECREF((PyObject*)d->user.s);

  if (d->user.inced_global_state) {
    if (!d->globals) {
      fprintf(stderr, "bug in pydparser.c deallocating d parser global state\n");
    } else {
      Py_DECREF(d->globals);
      d->globals = NULL;
      d->user.inced_global_state = 0;
    }
  }
}

/* swig can't handle these I don't think.*/
void 
my_d_loc_t_s_set(d_loc_t *dlt, D_Parser *dp, int val) {
  D_ParserPyInterface *ppi = d_interface(dp);
  dlt->s = val + ppi->buf_start;
}

int
my_d_loc_t_s_get(d_loc_t *dlt, D_Parser *dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  return dlt->s - ppi->buf_start;
}

void 
my_D_ParseNode_end_set(D_ParseNode *dpn, D_Parser *dp, int val) {
  D_ParserPyInterface *ppi = d_interface(dp);
  dpn->end = val + ppi->buf_start;
}

void 
my_D_ParseNode_end_skip_set(D_ParseNode *dpn, D_Parser *dp, int val) {
  D_ParserPyInterface *ppi = d_interface(dp);
  dpn->end_skip = val + ppi->buf_start;
}

int 
my_D_ParseNode_end_get(D_ParseNode *dpn, D_Parser *dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  return dpn->end - ppi->buf_start;
}

int 
my_D_ParseNode_end_skip_get(D_ParseNode *dpn, D_Parser *dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  return dpn->end_skip - ppi->buf_start;
}

PyObject *
my_D_ParseNode_symbol_get(D_ParseNode *dpn, D_Parser *dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  Parser *p = (Parser*)dp;
  PyObject *str;
  if (ppi->symbol_list == NULL) {
    ppi->symbol_list = PyTuple_New(p->t->nsymbols);
  }
  str = PyTuple_GetItem(ppi->symbol_list, dpn->symbol);
  if (str == NULL) {
    str = Py_BuildValue("s", p->t->symbols[dpn->symbol].name);
    PyTuple_SetItem(ppi->symbol_list, dpn->symbol, str);
  }
  Py_INCREF(str);
  return str;
}

static PyObject * 
new_loc_inst(D_Parser* dp, d_loc_t* dlt) {
  PyObject * buf;
  D_ParserPyInterface *ppi = d_interface(dp);
  PyObject *new_loc_args = PyTuple_New(3);
  PyObject *new_loc_inst;
  buf = SWIG_NewPointerObj((void *)dlt, SWIG_TypeQuery("_p_d_loc_t"),0);
  PyTuple_SetItem(new_loc_args, 0, buf);
  buf = SWIG_NewPointerObj((void *)dp, SWIG_TypeQuery("_p_D_Parser"),0);
  PyTuple_SetItem(new_loc_args, 1, buf);
  Py_INCREF(ppi->py_buf_start);
  PyTuple_SetItem(new_loc_args, 2, ppi->py_buf_start);
  new_loc_inst = PyObject_CallObject(ppi->loc_type, new_loc_args);
  Py_DECREF(new_loc_args);
  return new_loc_inst;
}

static PyObject *
make_py_node(D_Parser *dp, D_ParseNode *dpn) {
  PyObject * buf;
  D_ParserPyInterface *ppi = d_interface(dp);
  PyObject *new_node_arg = PyTuple_New(3);
  PyObject *node_inst;
  buf = SWIG_NewPointerObj((void *)dpn, SWIG_TypeQuery("_p_D_ParseNode"),0);
  PyTuple_SetItem(new_node_arg, 0, buf);
  buf = SWIG_NewPointerObj((void *)dp, SWIG_TypeQuery("_p_D_Parser"),0);
  PyTuple_SetItem(new_node_arg, 1, buf);
  Py_INCREF(ppi->py_buf_start);
  PyTuple_SetItem(new_node_arg, 2, ppi->py_buf_start);
  node_inst = PyObject_CallObject(ppi->node_info_type, new_node_arg);
  Py_DECREF(new_node_arg);
  return node_inst;
}

void 
remove_parse_tree_viewer(D_Parser* dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  ppi->num_parse_tree_viewers--;
  if (ppi->num_parse_tree_viewers < 0) {
    fprintf(stderr, "bug in pydparser.c parse tree deallocation code\n");
  }
  if (ppi->num_parse_tree_viewers == 0 && !ppi->parsing) {
    del_parser(dp);
  }
}

void
add_parse_tree_viewer(D_Parser* dp) {
  D_ParserPyInterface *ppi = d_interface(dp);
  ppi->num_parse_tree_viewers++;
}

static void 
my_syntax_error_fn(struct D_Parser *dp) {
  PyObject *arglist;
  PyObject *result;
  PyObject *loc_inst;
  D_ParserPyInterface *ppi = d_interface(dp);
  if (PyErr_Occurred())
      return;
  loc_inst = new_loc_inst(dp, &dp->loc);
  arglist = Py_BuildValue("(O)", loc_inst);
  result = PyEval_CallObject(ppi->syntax_error_fn, arglist);
  Py_XDECREF(result);
  Py_DECREF(arglist);
  Py_DECREF(loc_inst);
}

static void 
my_initial_white_space_fn(struct D_Parser *dp, 
			 d_loc_t *loc, void **p_globals) {
  PyObject *arglist;
  PyObject *result;
  PyObject *loc_inst;
  D_ParserPyInterface *ppi = d_interface(dp);
  if (PyErr_Occurred()) {
    return;
  }
  loc_inst = new_loc_inst(dp, loc);
  arglist = Py_BuildValue("(O)", loc_inst);
  result = PyEval_CallObject(ppi->initial_white_space_fn, arglist);
  Py_DECREF(loc_inst);
  Py_DECREF(arglist);
  Py_XDECREF(result);
}

static struct D_ParseNode *
my_ambiguity_fn(struct D_Parser *dp,
		int n, struct D_ParseNode **v) {
  int i, idx=0;
  PyObject *arglist;
  PyObject *result, *list;
  if (PyErr_Occurred()) {
    return v[0];
  }
  list = PyList_New(n);
  for (i=0; i<n; i++) {
    PyList_SetItem(list, i, make_py_node(dp, v[i]));
  }
  arglist = Py_BuildValue("(O)", list);
  result = PyEval_CallObject(d_interface(dp)->ambiguity_fn, arglist);
  if(result == Py_None) {
    Py_DECREF(list);
    Py_DECREF(arglist);
    i = 0;
    if (dp->dont_use_greediness_for_disambiguation || dp->dont_use_height_for_disambiguation)
      i = resolve_amb_greedy(dp, n, v);
    return v[i];
  }

  for (i=0; i<n; i++) {
    if (PyList_GetItem(list, i) == result) {
      idx = i;
      break;
    }
  }
  Py_DECREF(list);
  Py_DECREF(arglist);
  Py_DECREF(result);
  return v[idx];
}

D_Parser *
make_parser(long int idpt,
	    PyObject *self,
	    PyObject *reject,
	    PyObject *make_token,
	    PyObject *loc_type,
	    PyObject *node_info_type,
	    PyObject *actions,
	    PyObject *initial_white_space_fn,
	    PyObject *syntax_error_fn,
	    PyObject *ambiguity_fn,
	    int dont_fixup_internal_productions,
            int fixup_EBNF_productions, 
	    int dont_merge_epsilon_trees,
	    int commit_actions_interval,
	    int error_recovery,
	    int print_debug_info,
            int partial_parses,
            int dont_compare_stacks,
            int dont_use_greediness_for_disambiguation,
            int dont_use_height_for_disambiguation,
	    char *start_symbol,
	    int takes_strings,
	    int takes_globals) {
  BinaryTables *dpt = (BinaryTables*) idpt;
  D_ParserPyInterface *ppi;
  D_Parser *p = new_D_Parser(dpt->parser_tables_gram, sizeof(D_ParseNode_User));
  p->fixup_EBNF_productions = fixup_EBNF_productions;
  p->save_parse_tree = 1;
  p->initial_scope = NULL; 
  p->dont_fixup_internal_productions = dont_fixup_internal_productions;
  p->dont_merge_epsilon_trees = dont_merge_epsilon_trees;
  p->commit_actions_interval = commit_actions_interval;
  p->partial_parses = partial_parses;
  p->dont_compare_stacks = dont_compare_stacks;
  p->dont_use_greediness_for_disambiguation = dont_use_greediness_for_disambiguation;
  p->dont_use_height_for_disambiguation = dont_use_height_for_disambiguation;
  p->error_recovery = error_recovery;
  p->free_node_fn = free_node_fn;
  ppi = malloc(sizeof(D_ParserPyInterface)); 
  memset(ppi, 0, sizeof(D_ParserPyInterface));
  ((Parser*)p)->pinterface1 = ppi;
  /* d_interface(p) = ppi; */
  if (initial_white_space_fn != Py_None)
    p->initial_white_space_fn = my_initial_white_space_fn;
  if (syntax_error_fn != Py_None)
    p->syntax_error_fn = my_syntax_error_fn;
  if (ambiguity_fn != Py_None)
    p->ambiguity_fn = my_ambiguity_fn;
  Py_INCREF(Py_None);
  p->initial_globals = Py_None;
  Py_INCREF(self);
  ppi->self = self;
  Py_INCREF(make_token);
  ppi->make_token = make_token;
  Py_INCREF(actions);
  ppi->actions = actions;
  Py_INCREF(initial_white_space_fn);
  ppi->initial_white_space_fn = initial_white_space_fn;
  Py_INCREF(syntax_error_fn);
  ppi->syntax_error_fn = syntax_error_fn;
  Py_INCREF(ambiguity_fn);
  ppi->ambiguity_fn = ambiguity_fn;
  Py_INCREF(loc_type);
  ppi->loc_type = loc_type;
  Py_INCREF(reject);
  ppi->reject = reject;
  Py_INCREF(node_info_type);
  ppi->node_info_type = node_info_type;
  ppi->print_debug_info = print_debug_info;
  ppi->takes_strings = takes_strings;
  ppi->takes_globals = takes_globals;
  ppi->symbol_list = NULL;
  if (start_symbol[0]) {
    int i;
    for (i = 0; i < dpt->parser_tables_gram->nsymbols; i++) {
      if (dpt->parser_tables_gram->symbols[i].kind == D_SYMBOL_NTERM && strcmp(dpt->parser_tables_gram->symbols[i].name, start_symbol) == 0) {
	p->start_state = dpt->parser_tables_gram->symbols[i].start_symbol;
	break;
      }
    }
    if (i == dpt->parser_tables_gram->nsymbols) {
      fprintf(stderr, "invalid start symbol: %s\n", start_symbol);
      i = 0;
    }
  }

  return p;
}

void 
del_parser(D_Parser *dp) {
  D_ParserPyInterface *ppi;
  ppi = d_interface(dp);
  Py_DECREF(ppi->self);
  Py_DECREF(ppi->actions);
  Py_DECREF(ppi->initial_white_space_fn);
  Py_DECREF(ppi->syntax_error_fn);
  Py_DECREF(ppi->ambiguity_fn);
  Py_DECREF(ppi->loc_type);
  Py_DECREF(ppi->make_token);
  Py_DECREF(ppi->reject);
  Py_DECREF(ppi->node_info_type);
  Py_XDECREF(ppi->py_buf_start);
  Py_XDECREF(ppi->symbol_list);
  Py_XDECREF(dp->initial_globals);
  if (ppi->top_node) {
    free_D_ParseTreeBelow(dp, ppi->top_node);
    free_D_ParseNode(dp, ppi->top_node);
  }
  free_D_Parser(dp);
  free(ppi);
}

PyObject *
run_parser(D_Parser *dp, PyObject *string, int buf_idx) {
  PyObject *out = NULL;
  D_ParseNode *pn = NULL;
  D_ParserPyInterface *ppi = d_interface(dp);

  ppi->buf_start = PyString_AsString(string);
  ppi->py_buf_start = string;
  Py_INCREF(string);
  ppi->parsing = 1;
  pn = dparse(dp, ppi->buf_start+buf_idx, PyString_Size(string)-buf_idx);
  ppi->parsing = 0;
  ppi->top_node = pn;

  if (PyErr_Occurred()) {
    if (ppi->num_parse_tree_viewers == 0)
      del_parser(dp);
    return NULL;
  }

  if (!pn || dp->syntax_errors) {
    my_syntax_error_fn(dp);
  }

  if (PyErr_Occurred()) {
    if (ppi->num_parse_tree_viewers == 0)
      del_parser(dp);
    return NULL;
  }

  if (pn && pn->user.t) {
      out = PyList_New(3);
      Py_INCREF(pn->user.t);
      PyList_SetItem(out, 0, pn->user.t);
      PyList_SetItem(out, 1, make_py_node(dp, pn));
      if (pn->user.s) {
	Py_INCREF(pn->user.s);
	PyList_SetItem(out, 2, pn->user.s);
      } else {
	Py_INCREF(Py_None);
	PyList_SetItem(out, 2, Py_None);
    }
  }

  if (ppi->num_parse_tree_viewers == 0)
    del_parser(dp);

  if (out == NULL) {
    Py_INCREF(Py_None);
    return Py_None;
  }
  return out;
}

int has_deeper_nodes(D_Parser *parser, D_ParseNode *d) {
    int kind = d_dpt(parser)->symbols[d->symbol].kind;
    return kind == D_SYMBOL_INTERNAL || kind == D_SYMBOL_EBNF;
}

static PyObject *
pylist_children(D_Parser *parser, D_ParseNode *d, int string) {
  int i, nc = d_get_number_of_children(d);
  PyObject *list = PyList_New(nc);
  for (i=0; i<nc; i++) {
    D_ParseNode *child = d_get_child(d, i);
    PyObject *po = make_pyobject_from_node(parser, child, string);
    if (po == NULL) {
      Py_DECREF(list);
      return NULL;
    }
    PyList_SetItem(list, i, po);
  }
  return list;
}

static PyObject *
make_pyobject_from_node(D_Parser *parser, D_ParseNode *d, int string) {
  PyObject *user = (PyObject *)(string ? d->user.s : d->user.t), *make_token;
  if (user == NULL) {
    if (has_deeper_nodes(parser, d)) {
      user = pylist_children(parser, d, string);
      if (user == NULL) {
	return NULL;
      }
    } else {
      char *end = string ? d_ws_after(parser, d) : d->end;
      user = Py_BuildValue("s#", d->start_loc.s, end - d->start_loc.s);
      if (user == NULL) {
	return NULL;
      }
      make_token = d_interface(parser)->make_token;
      if (make_token != Py_None && !string) {
	PyObject *arglist = Py_BuildValue("(O)", user);
        if (arglist == NULL) {
          Py_DECREF(user);
          return NULL;
        }
	PyObject *result = PyEval_CallObject(make_token, arglist);
	Py_DECREF(user);
	Py_DECREF(arglist);
        if (result == NULL) {
	  return NULL;
	}
	return result;
      }
    }
  } else {
    Py_INCREF(user);
  }
  return user;
}

static void
inc_global_state(D_Parser *dp, D_ParseNode *dpn) {
  /* this global state stuff is ugly.  Does anyone actually use it? */
  int n_children = d_get_number_of_children(dpn);
  int i;
  for (i=0; i<n_children; i++) {
    D_ParseNode *child = d_get_child(dpn, i);
    if (has_deeper_nodes(dp, child)) {
      inc_global_state(dp, child);
    } else if (child->globals != NULL && !child->user.inced_global_state) {
      /* global state gets copied by dparser without increfing, fix */
      Py_INCREF(child->globals);
      child->user.inced_global_state = 1;
    }
  }
}

static void
print_debug_info(D_ParseNode *dd, PyObject *tuple, int speculative, int pdi) {
  char buf[256];
  char *start = dd->start_loc.s;
  char *end = dd->end_skip;
  int len = end - start;
  PyObject *action, *string;
  if (len > 255)
    len = 255;
  strncpy(buf, start, len);
  if (len == 255)
    buf[254] = buf[253] = buf[252] = '.';
  buf[len] = 0;
  action = PyTuple_GetItem(tuple, 0);
  string = PyObject_GetAttrString(action, "__name__");
  if (!speculative || pdi != 2)
    printf("%30s%s:\t%s\n", PyString_AsString(string), speculative ? " ???" : "    ", buf);
  Py_DECREF(string);
}

static PyObject*
take_action(PyObject *arg_types, PyObject *children_list, int speculative, 
	    D_ParseNode *dd, PyObject *string_list, int n_children, 
	    struct D_Parser *parser, void **children, int pn_offset,
	    PyObject *action) {
  int i;
  int arg_count = PyList_Size(arg_types);
  D_ParserPyInterface *ppi = d_interface(parser);
  PyObject *arglist = PyTuple_New(arg_count);
  PyObject *globals_holder = NULL;
  PyObject *result = NULL;

  Py_INCREF(children_list);
  PyTuple_SetItem(arglist, 0, children_list);
  for (i=1; i<arg_count; i++) {
    PyObject *item = PyList_GetItem(arg_types, i);
    int type = PyInt_AsLong(item);
    if (type == 1) {
      PyTuple_SetItem(arglist, i, Py_BuildValue("i", speculative));
    }
    else if (type == 2) {
      if (!dd->user.inced_global_state) {
	dd->user.inced_global_state = 1;
      }
      globals_holder = PyList_New(1);
      Py_INCREF(dd->globals);
      PyList_SetItem(globals_holder, 0, dd->globals);
      PyTuple_SetItem(arglist, i, globals_holder);
    }
    else if (type == 3) {
      Py_INCREF(string_list);
      PyTuple_SetItem(arglist, i, string_list);
    }
    else if (type == 4) {
      PyObject* nodes = PyList_New(n_children);
      int j;
      for (j=0; j<n_children; j++) {
	PyList_SetItem(nodes, j, make_py_node(parser, D_PN(children[j], pn_offset)));
      }
      PyTuple_SetItem(arglist, i, nodes);
    }
    else if (type == 5) {
      PyTuple_SetItem(arglist, i, make_py_node(parser, dd));
    }
    else if (type == 6) {
      Py_INCREF(Py_None);
      PyTuple_SetItem(arglist, i, Py_None);
    }
    else if (type == 7) {
      Py_INCREF(ppi->self);
      PyTuple_SetItem(arglist, i, ppi->self);
    }
  }
  result = PyEval_CallObject(action, arglist);
  if (globals_holder) {
    Py_DECREF(dd->globals);
    dd->globals = PyList_GetItem(globals_holder, 0);
    Py_INCREF(dd->globals);
  }
  Py_DECREF(arglist);
  return result;
}

static int
my_action(void *new_ps, void **children, int n_children, int pn_offset,
	  struct D_Parser *parser, int speculative) {
  D_ParseNode *dd = D_PN(new_ps, pn_offset);
  PyObject *result = NULL;
  PyObject *children_list, *string_list = NULL;
  PNode *pn = (PNode *)new_ps;
  int action_index = pn->reduction->action_index;
  PyObject *tuple = NULL;
  PyObject *arg_types = NULL;
  D_ParserPyInterface *ppi = d_interface(parser);
  int takes_speculative = 0;
  PyObject *action = 0;

  if (PyErr_Occurred()) {
    /* just keep returning until finished parsing.  Need a way to tell dparser to quit */
    return 0;
  }

  if (action_index != -1) {
    tuple = PyList_GetItem(ppi->actions, action_index);
    PyArg_ParseTuple(tuple, "OOi", &action, &arg_types, &takes_speculative);
  }
  
  if (ppi->takes_globals) {
    inc_global_state(parser, dd);
  }

  if (ppi->print_debug_info && tuple) {
    print_debug_info(dd, tuple, speculative, ppi->print_debug_info);
  }

  if (takes_speculative == -1 && !speculative) {
    /* user.t and user.s were already set when this was called speculatively */
    return 0;
  }

  if (ppi->takes_strings) {
    string_list = pylist_children(parser, dd, 1);
    if (string_list == NULL) {
      return -1;
    }
  }
  /* this function owns string_list */

  if (takes_speculative == 0 && speculative) {
    Py_INCREF(Py_None);
    Py_XDECREF(dd->user.t);
    /*    if (dd->user.s)
	  printf("freeing2:%d\n", dd->user.s);*/
    Py_XDECREF(dd->user.s);
    dd->user.t = Py_None;
    //    printf("dd1:%d\n", dd);
    dd->user.s = NULL;
    Py_XDECREF(string_list);
    /*    printf("setting:%d\n", string_list);*/
    //dd->user.s = string_list;

    return 0;
  }

  children_list = pylist_children(parser, dd, 0);
  if (children_list == NULL) {
    /*    if (string_list)
	  printf("freeing3:%d\n", string_list);*/

      Py_XDECREF(string_list);
      return -1;
  }
  /* this function owns children_list */

  if (action_index != -1) {
    result = take_action(arg_types, children_list, speculative, dd, string_list, 
			 n_children, parser, children, pn_offset, action);
    Py_DECREF(children_list);
  } else {
    result = children_list;
  }
  /* function now owns result, string_list */

  if (result == ppi->reject || result == NULL) {
    /*    if (string_list)
	  printf("freeing4:%d\n", string_list);*/

    Py_XDECREF(result);
    Py_XDECREF(string_list);
    return -1;  /* user rejected */
  }

  Py_XDECREF(dd->user.t); /* these may have been set in a speculative pass */
  /*  if(dd->user.s)
      printf("freeing5:%d\n", dd->user.s);*/
  Py_XDECREF(dd->user.s);
  /*  if(dd->user.s)
      printf("setting2:%d\n", string_list);*/
  //  printf("dd2:%d\n", dd);
  dd->user.t = result;
  dd->user.s = string_list;  

  return 0;
}

static int 
my_final_action(void *new_ps, void **children, int n_children, int pn_offset,
		struct D_Parser *parser) {
  return my_action(new_ps, children, n_children, pn_offset, parser, 0);
}

static int 
my_speculative_action(void *new_ps, void **children, int n_children, int pn_offset,
		      struct D_Parser *parser) {
  return my_action(new_ps, children, n_children, pn_offset, parser, 1);
}

void
d_version(char *v) {
  v[0] = 0;
}

long int 
load_parser_tables(char *tables_name) {
  return (long int)read_binary_tables(tables_name, my_speculative_action, my_final_action);
}

void
unload_parser_tables(long int binary_tables) {
  free_BinaryTables( ((BinaryTables * )binary_tables));
}
