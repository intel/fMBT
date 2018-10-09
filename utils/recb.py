# Regular expressions with callbacks - a library for building parsers
# Copyright (c) 2018, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms and conditions of the GNU Lesser General Public
# License, version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St - Fifth Floor, Boston, MA
# 02110-1301 USA.
#
# Author: antti.kervinen@intel.com

"""Regular expressions with callbacks

Example:

import recb

def print_groups(pattern, match, lineno):
    print "line:    ", lineno
    print "string:  ", repr(match.string[:match.end()])
    print "pattern: ", pattern
    print "groups:  ", match.groupdict()
    print ""

TAG_OPEN = recb.pattern(
    r"\s*<(?P<open_tag>[a-zA-Z_0-9]+)\b\s*",
    cb=print_groups)
ATTRIB = recb.pattern(
    r'(?P<attr_name>[a-zA-Z_0-9]+)="(?P<attr_value>[^"]+)"\s*',
    cb=print_groups)
TAG_CLOSE_HERE = recb.pattern(r'/>\s*')
TAG_CLOSE_LATER = recb.pattern(r'>\s*')
TAG_CLOSE_NAME = recb.pattern(
    r"</(?P<close_tag>[a-zA-Z_0-9]+)\s*>\s*",
    cb=print_groups)
COMMENT = recb.pattern(
    r"\s*<!--(?P<comment>.*?)-->\s*",
    cb=print_groups)

XML = (COMMENT
       | (TAG_OPEN
          + recb.many(ATTRIB)
          + (TAG_CLOSE_HERE
             | (TAG_CLOSE_LATER
                + recb.many(recb.name("XML"))
                + TAG_CLOSE_NAME)))
       )

# Make recursive grammar rule, replace patterns named "XML"
# with XML rule:
XML.set_patterns({"XML": XML})

x = '''<helo>
<recipient address="world"/>
<!-- this is an example -->
<!-- on parsing xml-like strings -->
<parser name="recb" uses="regexps" and="context-free grammar"/>
</helo>
'''

print "=" * 72
print "Parse without debugging:"
r, unparsed = XML.parse(x)

print "=" * 72
print "Parse with debugging (print only, running interacive=False)"
r, unparsed = XML.debug(interactive=False).parse(x)
"""

import re
import sys

def pattern(obj, **kwargs):
    """returns new pattern instance that matches single regexp or pattern

    Parameters:
      obj (string or a pattern):
              regular expression
      cb (func_obj(p_instance, match_obj, lineno)):
              callback to be called before pattern's children's
              callbacks when a match is found
      ca (func_obj(p_instance, match_obj, lineno)):
              callback to be called after pattern's children's
              callbacks when a match is found
    """
    if isinstance(obj, basestring):
        return P_re(obj, **kwargs)
    elif isinstance(obj, P_Base):
        return P_many(obj, n=1, **kwargs)

def many(obj, **kwargs):
    """returns new pattern instance that matches many patterns in a row

    Parameters:
      obj (a pattern):
              pattern to appear many times
      n (integer):
              exact number of times the pattern is expected to appear.
              The default is -1 (arbitrary number of times).
      cb (func_obj(p_instance, match_obj, lineno)):
              callback to be called before pattern's children's
              callbacks when a match is found
      ca (func_obj(p_instance, match_obj, lineno)):
              callback to be called after pattern's children's
              callbacks when a match is found
    """
    return P_many(obj, **kwargs)

def any(*objs, **kwargs):
    """returns new pattern that matches any of parameter patterns"""
    return P_or_P(children=objs, **kwargs)

def seq(*objs, **kwargs):
    """returns new pattern that matches when all parameter patterns match
    in the given order"""
    return P_then_P(children=objs, **kwargs)

def name(name, **kwargs):
    """returns a placeholder pattern.

    Parameters:
      name (string):
              name for the placeholder.

    Placeholder patterns must be replaced with real ones before
    parsing.

    Example: recursive parser for NUM, -NUM, (NUM), -(NUM), ...
      EXPR = ((pattern(r"\(") + name("EXPR") + pattern(r"\)"))
              | (pattern("-") + name("EXPR"))
              | pattern("0|[1-9][0-9]*")

      EXPR.set_patterns({"EXPR": EXPR})
    """
    return P_name(name, **kwargs)

def fast_forward(text):
    """returns a pattern that matches everything until the next instance of text"""
    return P_ff(text)

def parser_debugger(match=True, nomatch=True, interactive=False, print_func=sys.stdout.write, print_maxlen=80):
    """returns configured parser debugger. Add returned function to any pattern with pattern.set_pa(f).
    Parameters:
      match (bool):
              if True, print/debug if a pattern matches. The default is True.
      nomatch (bool):
              if True, print/debug if a pattern does not match. The
              default is True.
      interactive (bool or function(pattern, string, match) -> bool):
              if True, stop in interactive debugger (pdb prompt) on
              match. The default is False. If function, go interactive
              if the function returns True.
      print_func (function(str)):
             function to handle debug print messages.
             The default is sys.stdout.write.
      print_maxlen (int):
             maximum string length for printing.
    """
    def _parser_debugger(p, s, m):
        if callable(interactive):
            go_interacive = interactive(p, s, m)
        else:
            go_interacive = interactive
        if not match and m:
            # there is a match, but match debugging is set off
            return
        if not nomatch and m is None:
            # there is no match, but nomatch debugging is set off
            return
        print_msg = []
        print_msg.append("\npattern: %s" % (p,))
        if len(s) > print_maxlen:
            show_s = s[:print_maxlen] + "...[%s B]" % (len(s),)
        else:
            show_s = s
        print_msg.append("parsing: %r" % (show_s,))
        if type(m).__name__ == "SRE_Match":
            print_msg.append("          " + ("^" * (len(repr(show_s[:m.end()]))-2)))
            d = m.groupdict()
            for k in sorted(m.groupdict().keys()):
                print_msg.append("         %s = %r" % (k, d[k][:print_maxlen] if d.get(k, None) != None else None))
        print_msg.append("match:   %s" % (m,))
        if print_func:
            print_func("\n".join(print_msg) + "\n")
        if go_interacive:
            import pdb
            pdb.set_trace()
    return _parser_debugger

class P_Base(object):
    def __init__(self, parent=None, ca=None, cb=None, children=None,
                 pb=None, pa=None):
        self._parent = parent
        self._cb = cb # callback for "all parsed", called before children
        self._ca = ca # callback for "all parsed", called after children
        self._pb = pb # (debug) callback during parsing, called before parse
        self._pa = pa # (debug) callback during parsing, called after parse
        self._children = children
        self._parse_stack = []
        if self._children:
            for child in self._children:
                child.set_parent(self)
    def __add__(self, other_p):
        return P_then_P(children=[self, other_p])
    def __or__(self, other_p):
        return P_or_P(children=[self, other_p])
    def __sub__(self, other_p):
        return P_but_not_P(children=[self, other_p])
    def __repr__(self):
        return "%s(%r)" % (
            self.__class__.__name__,
            self._children)
    def many(self, **kwargs):
        return P_many(self, **kwargs)
    def parse(self, s, lineno=1):
        if self._parse_stack and self._parse_stack[-1] == s:
            # never ending recursion, refuse to parse
            return (None, s)
        self._parse_stack.append(s)
        results, unparsed = self._parse(s)
        self._parse_stack.pop()
        if not (results is None) and not self._parent and len(self._parse_stack) == 0:
            # This is the root node, no recursion depth left:
            # s was parsed successfully
            self.parsed(results, lineno)
        return results, unparsed
    def parsed(self, results, lineno):
        if self._cb:
            self._cb(self, results, lineno)
        self._parsed(results, lineno)
        if self._ca:
            self._ca(self, results, lineno)
    def _parsed(self, results, lineno):
        """override on derived classes if they have children. They need to
        call children's parsed() (not _parsed()) for correct children."""
        pass
    def set_ca(self, ca):
        """set callback function f(pattern, result, lineno) to be called
        on full match (everything parsed successfully).
        This is called after callbacks of child nodes in syntax tree."""
        self._ca = ca
        return self
    def set_cb(self, cb):
        """set callback function f(pattern, result, lineno) to be called
        on full match (everything parsed successfully).
        This is called before callbacks of child nodes in syntax tree."""
        self._cb = cb
        return self
    def set_parent(self, parent):
        self._parent = parent
        return self
    def set_patterns(self, name_to_pattern):
        if self._children:
            for child in self._children:
                child.set_patterns(name_to_pattern)
        return self
    def set_pa(self, pa):
        """set callback function f(pattern, s) to be called
        before parsing s"""
        if self._parse_stack:
            # recursive call detected, node already handled
            return self
        if isinstance(self, P_re) or isinstance(self, P_ff):
            self._pa = pa
        self._parse_stack.append(None)
        if self._children:
            for child in self._children:
                child.set_pa(pa)
        self._parse_stack.pop()
        return self
    def set_pb(self, pb):
        """set callback function f(pattern, s, result) to be called
        after parsing s, with parsing result"""
        if isinstance(self, P_re) or isinstance(self, P_ff):
            self._pb = pb
        if self._children:
            for child in self._children:
                child.set_pb(pb)
        return self
    def debug(self, **kwargs):
        """run parser in debug mode. overwrites pa callback.
        see parser_debugger() for parameters."""
        self.set_pa(parser_debugger(**kwargs))
        return self

class P_re(P_Base):
    def __init__(self, regexp, **kwargs):
        P_Base.__init__(self, **kwargs)
        self._r = re.compile(regexp)
    def regexp(self):
        return self._r
    def _parse(self, s):
        if self._pb:
            self._pb(self, s)
        m = self._r.match(s)
        if self._pa:
            self._pa(self, s, m)
        if m:
            return (m, s[m.end():])
        else:
            return (None, s)
    def __repr__(self):
        return "P_re(%r)" % (self._r.pattern,)

class P_then_P(P_Base):
    def __init__(self, **kwargs):
        if not "children" in kwargs:
            raise ValueError('P_then_P needs children')
        P_Base.__init__(self, **kwargs)
    def _parse(self, s):
        results = [] # (child_result, lines_consumed)
        last_successful_unparsed = s
        for child in self._children:
            res, unparsed = child.parse(last_successful_unparsed)
            if res is None:
                return (None, s)
            else:
                lines_consumed = last_successful_unparsed[:-len(unparsed)].count("\n")
                last_successful_unparsed = unparsed
                results.append((res, lines_consumed))
        return (results, last_successful_unparsed)
    def _parsed(self, results, lineno):
        first_lineno = lineno
        for i, (result, lines_consumed) in enumerate(results):
            self._children[i].parsed(result, first_lineno)
            first_lineno += lines_consumed

class P_or_P(P_Base):
    def __init__(self, **kwargs):
        if not "children" in kwargs:
            raise ValueError('P_or_P needs children')
        P_Base.__init__(self, **kwargs)
    def _parse(self, s):
        results = []
        unparsed = s
        for child in self._children:
            res, unparsed = child.parse(s)
            if res:
                return ((child, res), unparsed)
        return (None, s)
    def _parsed(self, results, lineno):
        child, res = results
        child.parsed(res, lineno)

class P_but_not_P(P_Base):
    def __init__(self, **kwargs):
        if not "children" in kwargs:
            raise ValueError('P_but_not_P needs children')
        P_Base.__init__(self, **kwargs)
    def _parse(self, s):
        results = []
        unparsed = s
        # First child is required to match
        first_child = self._children[0]
        first_res, first_unparsed = first_child.parse(s)
        if first_res is None:
            return (None, s)
        # Any of the following children must not match
        for child in self._children[1:]:
            next_res, _ = child.parse(s)
            if next_res:
                return (None, s)
        return ((first_child, first_res), first_unparsed)
    def _parsed(self, results, lineno):
        child, res = results
        child.parsed(res, lineno)

class P_many(P_Base):
    def __init__(self, p_obj, n=-1, **kwargs):
        P_Base.__init__(self, children=[p_obj], **kwargs)
        self._n = n
    def _parse(self, s):
        results = []
        last_successful_unparsed = s
        n = self._n
        m, unparsed = self._children[0].parse(last_successful_unparsed)
        while m and n != 0:
            lines_consumed = last_successful_unparsed[:-len(unparsed)].count("\n")
            results.append((m, lines_consumed))
            last_successful_unparsed = unparsed
            if not unparsed:
                break
            m, unparsed = self._children[0].parse(last_successful_unparsed)
            n -= 1
        if n <= 0:
            return (results, last_successful_unparsed)
        else:
            # not enough matches
            return (None, s)
    def _parsed(self, results, lineno):
        first_lineno = lineno
        child = self._children[0]
        for (result, lines_consumed) in results:
            child.parsed(result, first_lineno)
            first_lineno += lines_consumed

class P_name(P_Base):
    def __init__(self, name, **kwargs):
        P_Base.__init__(self, children=[], **kwargs)
        self._name = name
    def _parse(self, s):
        if not self._children:
            raise ValueError('name %r is only a placeholder, set_patterns({%r: ...}) missing' % (self._name, self._name))
        return self._children[0].parse(s)
    def _parsed(self, results, lineno):
        return self._children[0].parsed(results, lineno)
    def set_patterns(self, name_to_pattern):
        for name in name_to_pattern.keys():
            if self._name == name:
                self._children = [name_to_pattern[name]]

class P_ff(P_Base):
    def __init__(self, text, **kwargs):
        P_Base.__init__(self, **kwargs)
        self._text = text
    def _parse(self, s):
        if self._pb:
            self._pb(self, s)
        text_start = s.find(self._text)
        if self._pa:
            self._pa(self, s, text_start)
        if text_start == 0:
            # Already at text, cannot fast forward, this pattern does not match
            return (None, s)
        elif text_start == -1:
            # Text is not found in parsed string, fast forward until the end
            return (True, "")
        else:
            # Text found somewhere in the middle, fast forward until that point
            return (True, s[text_start:])
    def __repr__(self):
        return "P_ff(%r)" % (self._text,)
