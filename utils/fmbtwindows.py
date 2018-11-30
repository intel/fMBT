# fMBT, free Model Based Testing tool
# Copyright (c) 2014, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This is library implements fMBT GUITestInterface for Windows

How to setup Windows device under test

1. Install Python 2.X. (For example 2.7.)

2. Add Python to PATH, so that command "python" starts the interpreter.

3. Copy fMBT's pythonshare directory to Windows.

4. In the pythonshare directory, run "python setup.py install"

5. Run:
   cd \\python27\\scripts
   python pythonshare-server --interface=all --password=xxxxxxxx


How to connect to the device

import fmbtwindows
d = fmbtwindows.Device("IP-ADDRESS-OF-THE-DEVICE", password="xxxxxxxx")
"""

import ast
import base64
import fmbt
import fmbt_config
import fmbtgti
import inspect
import math
import os
import pythonshare
import shutil
import subprocess
import time
import zlib

try:
    import pycosh
except ImportError:
    pycosh = None

try:
    import fmbtpng
except ImportError:
    fmbtpng = None

if os.name == "nt":
    _g_closeFds = False
else:
    _g_closeFds = True

def _adapterLog(msg):
    fmbt.adapterlog("fmbtwindows %s" % (msg,))

def _run(command, expectedExitStatus=None):
    """
    Execute command in child process, return status, stdout, stderr.
    """
    if type(command) == str:
        shell = True
    else:
        shell = False

    try:
        p = subprocess.Popen(command, shell=shell,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             close_fds=_g_closeFds)
        if expectedExitStatus != None:
            out, err = p.communicate()
        else:
            out, err = ('', None)
    except Exception, e:
        class fakeProcess(object): pass
        p = fakeProcess
        p.returncode = 127
        out, err = ('', e)

    exitStatus = p.returncode

    if (expectedExitStatus != None and
        exitStatus != expectedExitStatus and
        exitStatus not in expectedExitStatus):
        msg = "Executing %s failed. Exit status: %s, expected %s" % (
            command, exitStatus, expectedExitStatus)
        _adapterLog("%s\n    stdout: %s\n    stderr: %s\n" % (msg, out, err))
        raise FMBTWindowsError(msg)

    return exitStatus, out, err

_g_keyNames = [
    "VK_LBUTTON", "VK_RBUTTON", "VK_CANCEL", "VK_MBUTTON",
    "VK_XBUTTON1", "VK_XBUTTON2", "VK_BACK", "VK_TAB", "VK_CLEAR",
    "VK_RETURN", "VK_SHIFT", "VK_CONTROL", "VK_MENU", "VK_PAUSE",
    "VK_CAPITAL", "VK_KANA", "VK_HANGUL", "VK_JUNJA", "VK_FINAL",
    "VK_HANJA", "VK_KANJI", "VK_ESCAPE", "VK_CONVERT", "VK_NONCONVERT",
    "VK_ACCEPT", "VK_MODECHANGE", "VK_SPACE", "VK_PRIOR", "VK_NEXT",
    "VK_END", "VK_HOME", "VK_LEFT", "VK_UP", "VK_RIGHT", "VK_DOWN",
    "VK_SELECT", "VK_PRINT", "VK_EXECUTE", "VK_SNAPSHOT", "VK_INSERT",
    "VK_DELETE", "VK_HELP", "VK_LWIN", "VK_RWIN", "VK_APPS", "VK_SLEEP",
    "VK_NUMPAD0", "VK_NUMPAD1", "VK_NUMPAD2", "VK_NUMPAD3", "VK_NUMPAD4",
    "VK_NUMPAD5", "VK_NUMPAD6", "VK_NUMPAD7", "VK_NUMPAD8", "VK_NUMPAD9",
    "VK_MULTIPLY", "VK_ADD", "VK_SEPARATOR", "VK_SUBTRACT", "VK_DECIMAL",
    "VK_DIVIDE", "VK_F1", "VK_F2", "VK_F3", "VK_F4", "VK_F5", "VK_F6",
    "VK_F7", "VK_F8", "VK_F9", "VK_F10", "VK_F11", "VK_F12", "VK_F13",
    "VK_F14", "VK_F15", "VK_F16", "VK_F17", "VK_F18", "VK_F19", "VK_F20",
    "VK_F21", "VK_F22", "VK_F23", "VK_F24", "VK_NUMLOCK", "VK_SCROLL",
    "VK_LSHIFT", "VK_RSHIFT", "VK_LCONTROL", "VK_RCONTROL", "VK_LMENU",
    "VK_RMENU", "VK_BROWSER_BACK", "VK_BROWSER_FORWARD",
    "VK_BROWSER_REFRESH", "VK_BROWSER_STOP", "VK_BROWSER_SEARCH",
    "VK_BROWSER_FAVORITES", "VK_BROWSER_HOME", "VK_VOLUME_MUTE",
    "VK_VOLUME_DOWN", "VK_VOLUME_UP", "VK_MEDIA_NEXT_TRACK",
    "VK_MEDIA_PREV_TRACK", "VK_MEDIA_STOP", "VK_MEDIA_PLAY_PAUSE",
    "VK_LAUNCH_MAIL", "VK_LAUNCH_MEDIA_SELECT", "VK_LAUNCH_APP1",
    "VK_LAUNCH_APP2", "VK_OEM_1", "VK_OEM_PLUS", "VK_OEM_COMMA",
    "VK_OEM_MINUS", "VK_OEM_PERIOD", "VK_OEM_2", "VK_OEM_3", "VK_OEM_4",
    "VK_OEM_5", "VK_OEM_6", "VK_OEM_7", "VK_OEM_8", "VK_OEM_102",
    "VK_PROCESSKEY", "VK_PACKET", "VK_ATTN", "VK_CRSEL", "VK_EXSEL",
    "VK_EREOF", "VK_PLAY", "VK_ZOOM", "VK_PA1", "VK_OEM_CLEAR", "0", "1",
    "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F",
    "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z"]

_g_viewSources = ["enumchildwindows", "uiautomation",
                  "uiautomation/raw", "uiautomation/control",
                  "uiautomation/content"]

# ShowWindow showCmd
SW_HIDE          = 0
SW_NORMAL        = 1
SW_MINIMIZED     = 2
SW_MAXIMIZE      = 3
SW_NOACTIVATE    = 4
SW_SHOW          = 5
SW_MINIMIZE      = 6
SW_MINNOACTIVE   = 7
SW_SHOWNA        = 8
SW_RESTORE       = 9
SW_DEFAULT       = 10
SW_FORCEMINIMIZE = 11

sortItems = fmbtgti.sortItems

class Timeout(object):
    """Process status may be a Timeout instead of an integer

    Prevent < > <= >= comparisons between numeric status
    and Timeout because they might otherwise return True and
    cause nasty bugs."""
    def __init__(self, command=None, pid=None):
        self._command = command
        self._pid = pid
    def __gt__(self, other):
        raise TypeError("cannot compare %s '>' %s" % (Timeout, type(other),))
    def __lt__(self, other):
        raise TypeError("cannot compare %s '<' %s" % (Timeout, type(other),))
    def __ge__(self, other):
        raise TypeError("cannot compare %s '>=' %s" % (Timeout, type(other),))
    def __le__(self, other):
        raise TypeError("cannot compare %s '<=' %s" % (Timeout, type(other),))
    def __repr__(self):
        return "Timeout(%s, %s)" % (repr(self._command), repr(self._pid))
    def command(self):
        """Returns command that was timed out"""
        return self._command
    def pid(self):
        """Return process id of timed out process"""
        return self._pid

class ViewItem(fmbtgti.GUIItem):
    def __init__(self, view, itemId, parentId, className, text, bbox, dumpFilename,
                 rawProperties=None):
        self._view = view
        self._itemId = itemId
        self._parentId = parentId
        self._className = className
        self._text = text
        if rawProperties:
            self._properties = rawProperties
        else:
            self._properties = {}
        self._patterns = frozenset()
        fmbtgti.GUIItem.__init__(self, self._className, bbox, dumpFilename)

    def __getattr__(self, attr):
        """Allows to access a item's property as a normal attribute.
        It also tries to guess the type, converting the value to it."""
        value = self._properties.get(attr, None)
        if value is None:
            raise AttributeError, attr
        lowered_value = value.lower()
        if lowered_value in ('false', 'true'):
            return lowered_value == 'true'
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if ';' in value or ',' in value:
            try:
                return [int(item) for item in value.split(';' if ';' in value else ',')]
            except ValueError:
                pass
        return value

    def __setattr__(self, attr, value):
        """Allows to set an item's property as a normal attribute.
        Currently only the Value property is handled."""
        if attr == 'Value':
            self.setValue(value)
        object.__setattr__(self, attr, value)

    def _checkUIautomation(self):
        self._view._checkUIautomation()

    def branch(self):
        """Returns list of view items from the root down to this item

        Note: works only for UIAutomation backend"""
        self._checkUIautomation()
        rv = []
        itemId = self._itemId
        while itemId:
            rv.append(self._view._viewItems[itemId])
            if itemId in self._view._viewItems:
                itemId = self._view._viewItems[itemId]._parentId
            else:
                itemId = None
        rv.reverse()
        return rv

    def children(self):
        if self._view._viewSource.startswith("enumchildwindows"):
            return [self._view._viewItems[winfo[0]]
                    for winfo in self._view._itemTree[self._itemId]]
        else:
            items = self._view._viewItems
            return [items[itemHash]
                    for itemHash in items
                    if items[itemHash]._parentId == self._itemId]

    def dump(self):
        """Dumps the most important attributes"""
        return "id=%s autid=%s cls=%s text=%r bbox=%s" % (
            self._itemId, self._properties.get('AutomationId', None),
            self._className, self._text, self._bbox)

    def parent(self):
        return self._parentId

    def parentItem(self):
        try:
            return self._view._viewItems[self._parentId]
        except KeyError:
            return None

    def id(self):
        return self._itemId

    def properties(self):
        return self._properties

    def text(self):
        return self._text

    def dumpProperties(self):
        """Dumps the properties"""
        return "\n".join("%s=%s" % (key, self._properties[key])
                         for key in sorted(self._properties))

    def __str__(self):
        return "ViewItem(%s)" % self.dump()

    def cachedParentItem(self):
        """
        Returns the parent's viewitem which is cached by the server.
        """
        return self._view.cachedItem(self._parentId)

    def refresh(self):
        """Updates the properties taking their current values.
        It returns self, so other operations can chained together.
        For example, to wait until a widget is enabled:
            while not widget.refresh().IsEnabled:
                time.sleep(0.1)"""
        self._checkUIautomation()
        data = self._view._device._conn.recvViewItemProperties(self.id())
        if data:
            self._properties.update(data[0])
        return self

    def patterns(self):
        """
        Returns a frozenset of the supported patterns.
        """
        self._checkUIautomation()
        if not self._patterns:
            data = self._view._device._conn.recvViewItemPatterns(self.id())
            if data:
                self._patterns = frozenset(data[0])
        return self._patterns

    def setFocus(self):
        """
        Sets the focus to the widget.
        """
        self._checkUIautomation()
        self._view._device._conn.sendSetFocus(self.id())

    def items(self, propertyName, separator="\n", filterSubChildClassName="", maxSubChildren=0):
        """
        Returns a list of the given property from all widget's direct children.
        Only the rendered / shown / displayed widgets will be considered.
        If, for example, a ListView widget has thousands of ListViewItems, but only 50 are
        displayed, this methods retrieves only the properties values (of the sub-children which
        compose the ListViewItems) from such 50 widgets will be reported as a string list of
        exactly 50 elements.

        Parameters:

          propertyName (string):
                  the property name to be retrieved.

          separator (string, optional):
                  the separator to be used for all values, when a child is composed of
                  other (sub-)children. All properties values will be collected from the
                  sub-children, and joined using this separator.

          filterSubChildClassName (string, optional):
                  Only the sub-children of this class will be dumped. All sub-children will
                  be collected, if it's not defined.

          maxSubChildren (int, optional):
                  How many sub-children values will be collected (and joined), at maximum.
                  If a child has many sub-children, but only the first ones are wanted,
                  using this parameter limits the properties collection.
                  By default (0), all sub-children's properties values will be collected.
        """
        self._checkUIautomation()
        data = self._view._device._conn.recvViewItemItems(
            self.id(), propertyName, separator, filterSubChildClassName, maxSubChildren)
        return data[0]

    def collapse(self):
        """
        Collapses a widget which supports this kind of operation, like a TreeView.
        """
        self._checkUIautomation()
        self._view._device._conn.sendCollapse(self.id())

    def expand(self):
        """
        Expands a widget which supports this kind of operation, like a TreeView.
        """
        self._checkUIautomation()
        self._view._device._conn.sendExpand(self.id())

    def containerItems(self, propertyName, separator="\n", filterSubChildClassName="", maxSubChildren="0", scroll=False):
        """
        Returns a list of the given property from all widget's direct
        children.

        Like the items() method, but all children, even the currently
        not displayed ones, will be reported.

        If a child isn't displayed when it's evaluated, it will
        have no sub-children, so no information about them will be
        reported. To fully render/display a child, the new scroll
        parameter should be used, so the item display area will be
        scrolled until the child is finally rendered. After that, all
        information about its sub-children are available and will be
        retrieved.

        Parameters:

          propertyName, separator, filterSubChildClassName, maxSubChildren:
                  refer to ViewItem.items() documentation.

          scroll (bool, optional):
                  Allows children scrolling, to make them visible.
                  By default (false), no children scrolling is made.

        Note: If a widget has many children, scrolling all of them will be slow.
        """

        self._checkUIautomation()
        data = self._view._device._conn.recvViewItemContainerItems(
            self.id(), propertyName, separator, filterSubChildClassName, maxSubChildren, scroll)
        return data[0]

    def selectedItems(self, propertyName, separator="\n", filterSubChildClassName="", maxSubChildren="0", scroll=False):
        """
        Returns a list of the given property from all widget's direct
        children which are selected.

        Like containerItems(), but only selected children will be
        reported.
        """
        self._checkUIautomation()
        data = self._view._device._conn.recvViewItemSelectedItems(
            self.id(), propertyName, separator, filterSubChildClassName, maxSubChildren, scroll)
        return data[0]

    def longText(self, maxLength=65536):
        """
        Returns the text from widgets like a RichTextEdit or a Document,
        that normally don't allow to report the text using the usual text() method.

        Parameters:

          maxLength (integer, optional):
                  The maximum number of characters to be reported, to
                  limit the transferred data.  The default is 64K characters.
        """
        self._checkUIautomation()
        data = self._view._device._conn.recvViewItemText(self.id(), maxLength)
        return data[0].popitem()[1] if data else None

    def setValue(self, value):
        """
        Sets the value of a widget. For example the text for a TextBlock,
        or the text of a ComboBox.
        It doesn't work for more complex widgets like a RichTextEdit or a Document.

        Parameters:

          value (string):
                  The value to be set.
        """

        self._checkUIautomation()
        self._view._device._conn.recvViewItemSetValue(self.id(), value)
        self._properties['Value'] = str(value)

class View(object):
    def __init__(self, dumpFilename, itemTree, itemOnScreen=None, device=None, freeDumps=False):
        self._dumpFilename = dumpFilename
        self._itemTree = itemTree
        self._rootItem = None
        self._rootItems = []
        self._viewItems = {}
        self._device = device
        self._freeDumps = freeDumps
        if itemOnScreen == None:
            self._itemOnScreen = lambda item: True
        else:
            self._itemOnScreen = itemOnScreen
        if isinstance(itemTree, dict):
            # data from enumchildwindows:
            self._viewSource = "enumchildwindows"
            for itemId, winfoList in itemTree.iteritems():
                for winfo in winfoList:
                    itemId, parentId, className, text, bbox = winfo
                    self._viewItems[itemId] = ViewItem(
                        self, itemId, parentId, className, text, bbox, dumpFilename)
            self._rootItem = self._viewItems[self._itemTree["root"][0][0]]
            self._rootItems.append(self._rootItem)
        elif isinstance(itemTree, list):
            # data from uiautomation
            # list of dictionaries, each of which contains properties of an item
            self._viewSource = "uiautomation"
            for elt in itemTree:
                self._insertItem(elt)
            if not self._rootItem and not freeDumps:
                raise ValueError("no root item in view data")

    def _insertItem(self, elt):
        bboxString = elt.get("BoundingRectangle", "0;0;0;0")
        bboxSeparator = ";" if ";" in bboxString else ","
        try:
            bbox = [int(coord) for coord in bboxString.split(bboxSeparator)]
            bbox[2] = bbox[0] + bbox[2] # width to right
            bbox[3] = bbox[1] + bbox[3] # height to bottom
            bbox = tuple(bbox)
        except Exception, e:
            bbox = 0, 0, 0, 0
        text = elt.get("Value") or elt.get("Name", "")
        vi = ViewItem(
            self, int(elt["hash"]), int(elt["parent"]),
            elt.get("ClassName", ""),
            text,
            bbox,
            self._dumpFilename,
            elt)
        self._viewItems[int(elt["hash"])] = vi
        if not vi.parent():
            self._rootItem = vi
            self._rootItems.append(vi)
        return vi

    def _checkUIautomation(self):
        if not self._viewSource.startswith("uiautomation"):
            raise NotImplementedError(
                "This method works only for uiautomation at the moment")

    def cachedItem(self, id_):
        """
        Retrieves an automation element from the server cache, passing its id.
        If the item was already into the view, it's updated.
        """
        self._checkUIautomation()
        data = self._device._conn.recvViewCachedItem(id_)
        if data:
            return self._insertItem(data[0])

    def _intCoords(self, *args):
        # TODO: relative coordinates like (0.5, 0.9)
        return [int(c) for c in args[0]]

    def filename(self):
        return self._dumpFilename

    def rootItem(self):
        return self._rootItem

    def _dumpTree(self, rootItem, indentation=''):
        yield "%s|-- %s" % (indentation, rootItem.dump())
        indentation += '|   '
        for child in rootItem.children():
            for dump in self._dumpTree(child, indentation):
                yield dump

    def dumpTree(self, rootItem=None):
        """
        Returns item tree as a string
        """
        if rootItem:
            return "\n".join(self._dumpTree(rootItem))
        else:
            if self._rootItems:
                rootsDumps = ("\n".join(self._dumpTree(rootItem)) for rootItem in self._rootItems)
            else:
                rootsDumps = ("\n".join(self._dumpTree(rootItem)) for rootItem in self._viewItems.itervalues())
            return "\n".join(rootsDumps)

    def __str__(self):
        return "View(%r, %s items)" % (self._dumpFilename, len(self._viewItems))

    def findItems(self, comparator, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        foundItems = []
        if count == 0: return foundItems
        if searchRootItem != None:
            if comparator(searchRootItem) and (
                    not onScreen or (self._itemOnScreen(searchRootItem))):
                foundItems.append(searchRootItem)
            for c in searchRootItem.children():
                foundItems.extend(self.findItems(comparator, count=count-len(foundItems), searchRootItem=c, onScreen=onScreen))
        else:
            if searchItems:
                domain = iter(searchItems)
            else:
                domain = self._viewItems.itervalues
            for i in domain():
                if comparator(i) and (not onScreen or (self._itemOnScreen(i))):
                    foundItems.append(i)
                    if count > 0 and len(foundItems) >= count:
                        break
        return foundItems

    def findItemsByText(self, text, partial=False, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        if partial:
            c = lambda item: (text in item._text)
        else:
            c = lambda item: (text == item._text)
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByClass(self, className, partial=False, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        if partial:
            c = lambda item: (className in item._className)
        else:
            c = lambda item: (className == item._className)
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsById(self, itemId, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        c = lambda item: (itemId == item._itemId or itemId == item.properties().get("AutomationId", None))
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByProperties(self, properties, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns ViewItems where every property matches given properties

        Parameters:
          properties (dictionary):
                  names and required values of properties

        Example:
          view.findItemsByProperties({"Value": "HELLO", "Name": "File name:"})

        See also:
          viewitem.dumpProperties()

        Notes:
          - requires uiautomation (refreshView(viewSource="uiautomation"))
          - all names and values are strings
        """
        c = lambda item: 0 == len([key for key in properties
                                   if properties[key] != item.properties().get(key, None)])
        return self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)

    def findItemsByPos(self, pos, count=-1, searchRootItem=None, searchItems=None, onScreen=False):
        """
        Returns list of ViewItems whose bounding box contains the position.

        Parameters:
          pos (pair of floats (0.0..0.1) or integers (x, y)):
                  coordinates that fall in the bounding box of found items.

          other parameters: refer to findItems documentation.

        Items are listed in ascending order based on area. They may
        or may not be from the same branch in the widget hierarchy.
        """
        x, y = self._intCoords(pos)
        c = lambda item: (item.bbox()[0] <= x <= item.bbox()[2] and item.bbox()[1] <= y <= item.bbox()[3])
        items = self.findItems(c, count=count, searchRootItem=searchRootItem, searchItems=searchItems, onScreen=onScreen)
        # sort from smallest to greatest area
        area_items = [((i.bbox()[2] - i.bbox()[0]) * (i.bbox()[3] - i.bbox()[1]), i) for i in items]
        return [i for _, i in sorted(area_items)]

    def items(self):
        """
        Returns list of all items in the view
        """
        return fmbtgti.sortItems(self._viewItems.values(), "topleft")

    def save(self, fileOrDirName):
        """
        Save view dump to a file.
        """
        shutil.copy(self._dumpFilename, fileOrDirName)


class Device(fmbtgti.GUITestInterface):
    def __init__(self, connspec=None, password=None, screenshotSize=(None, None),
                 connect=True, **kwargs):
        """Connect to windows device under test.

        Parameters:

          connspec (string or None, optional):
                  specification for connecting to a pythonshare
                  server that will run fmbtwindows-agent. The format is
                  "[socket://][password@]<host>[:<port>][/namespace]".
                  The default is None: run the agent on host, do not
                  connect to a pythonshare server (works only on Windows).

          password (string or None, optional):
                  authenticate to pythonshare server with given
                  password. The default is None (no authentication).

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).

          connect (boolean, optional):
                  Immediately establish connection to the device. The
                  default is True.

        To prepare a windows device for connection, launch there

        python pythonshare-server --password mysecretpwd

        When not on trusted network, consider ssh port forward, for
        instance.
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self._defaultViewSource = _g_viewSources[1]
        self._refreshViewDefaults = kwargs
        self._lastView = None
        self._lastViewStats = {}
        self._refreshViewRetryLimit = 1
        self._connspec = connspec
        self._password = password
        if connect:
            self.setConnection(WindowsConnection(
                self._connspec, self._password, self))
        else:
            self.setConnection(None)

    def closeWindow(self, window):
        """
        Send WM_CLOSE to window

        Parameters:

          window (window title (string) or handle (integer)):
                  window to which the command will be sent.

        Returns True on success, otherwise False.
        """
        return self.existingConnection().sendCloseWindow(window)

    def setCacheMode(self, mode="lastwindow"):
        """
        Sets the server policy for caching AutomationElements.

        Parameters:

          mode (string, optional. Default is "lastwindow"):
                  Defines the cache policy, and can be one of:
                      "none", "lastdump", "lastwindow", "all".
                  "none" disables caching.
                  "lastdump" caches only the last dump.
                  "lastwindow" caches all elements of a window.
                      If a new window is dumped, the cache is
                      cleared.
                  "all" caches all element of all windows.
        """
        if mode not in ("none", "lastdump", "lastwindow", "all"):
            raise FMBTWindowsError("Unknown cache mode: %s" % mode)
        return self.existingConnection().sendSetCacheMode(mode)

    def clearCache(self):
        """
        Clears the server AutomationElements cache.
        """
        return self.existingConnection().sendClearCache()

    def errorReporting(self):
        """
        Returns Windows error reporting (WER) settings in a dictionary

        See also: setErrorReporting()
                  MSDN WER Settings.
        """
        supported_settings = ["DisableArchive",
                              "Disabled",
                              "DisableQueue",
                              "DontShowUI",
                              "DontSendAdditionalData",
                              "LoggingDisabled",
                              "MaxArchiveCount",
                              "MaxQueueCount"]
        settings = {}
        for setting in supported_settings:
            settings[setting] = self.getRegistry(
                r"HKEY_CURRENT_USER\Software\Microsoft\Windows\Windows Error Reporting",
                setting)[0]
        return settings

    def existingView(self):
        if self._lastView:
            return self._lastView
        else:
            raise FMBTWindowsError("view is not available. Missing refreshView()?")

    def fileProperties(self, filepath):
        """
        Returns file properties as a dictionary.

        Parameters:
          filepath (string):
                  full path to the file.
        """
        escapedFilename = filepath.replace('/', '\\').replace('\\', r'\\\\')
        return self.existingConnection().evalPython(
            '''wmicGet("datafile",'''
            '''componentArgs=("where", "name='%s'"))''' %
            escapedFilename)

    def getFile(self, remoteFilename, localFilename=None, compress=False):
        """
        Fetch file from the device.

        Parameters:

          remoteFilename (string):
                  file to be fetched on device

          localFilename (optional, string or None):
                  file to be saved to local filesystem. If None,
                  return contents of the file without saving them.

          compress (optional, boolean or integer):
                  if True, file contents will be compressed for the transfer.
                  Integer (0-9) defines compression level. The default is
                  False: transfer without compression.
        """
        return self._conn.recvFile(remoteFilename, localFilename, compress)

    def getMatchingPaths(self, pathnamePattern):
        """
        Returns list of paths matching pathnamePattern on the device.

        Parameters:

          pathnamePattern (string):
                  Pattern for matching files and directories on the device.

        Example:

          getMatchingPaths("c:/windows/*.ini")

        Implementation runs glob.glob(pathnamePattern) on remote device.
        """
        return self._conn.recvMatchingPaths(pathnamePattern)

    def getClipboard(self):
        """
        Returns clipboard contents in text format.

        See also: setClipboard()
        """
        return self.existingConnection().evalPython("getClipboardText()")

    def itemOnScreen(self, guiItem, relation="touch", topWindowBbox=None):
        """
        Returns True if bbox of guiItem is non-empty and on the screen

        Parameters:

          relation (string, optional):
                  One of the following:
                  - "overlap": item intersects the screen and the window.
                  - "touch": mid point (the default touch point) of the item
                             is within the screen and the window.
                  - "within": the screen and the window includes the item.
                  The default is "touch".
        """
        if guiItem.properties().get("IsOffscreen", False) == "True":
            return False
        if relation == "touch":
            x1, y1, x2, y2 = guiItem.bbox()
            if x1 == x2 or y1 == y2:
                return False # a dimension is missing => empty item
            itemBox = (guiItem.coords()[0], guiItem.coords()[1],
                       guiItem.coords()[0] + 1, guiItem.coords()[1] + 1)
            partial = True
        elif relation == "overlap":
            itemBox = guiItem.bbox()
            partial = True
        elif relation == "within":
            itemBox = guiItem.bbox()
            partial = False
        else:
            raise ValueError('invalid itemOnScreen relation: "%s"' % (relation,))
        maxX, maxY = self.screenSize()
        if topWindowBbox == None:
            try:
                topWindowBbox = self.topWindowProperties()['bbox']
            except TypeError:
                topWindowBbox = (0, 0, maxX, maxY)
        return (fmbtgti._boxOnRegion(itemBox, (0, 0, maxX, maxY), partial=partial) and
                fmbtgti._boxOnRegion(itemBox, topWindowBbox, partial=partial))

    def kill(self, pid):
        """
        Terminate process

        Parameters:

          pid (integer):
                  ID of the process to be terminated.
        """
        try:
            return self.existingConnection().evalPython(
                "kill(%s)" % (repr(pid),))
        except:
            return False

    def keyNames(self):
        """
        Returns list of key names recognized by pressKey
        """
        return sorted(_g_keyNames)

    def osProperties(self):
        """
        Returns OS properties as a dictionary
        """
        return self.existingConnection().evalPython(
            "wmicGet('os')")

    def pinch(self, (x, y), startDistance, endDistance,
              finger1Dir=90, finger2Dir=270, movePoints=20,
              duration=0.75):
        """
        Pinch (open or close) on coordinates (x, y).

        Parameters:
          x, y (integer):
                  the central point of the gesture. Values in range
                  [0.0, 1.0] are scaled to full screen width and
                  height.

          startDistance, endDistance (float):
                  distance from both finger tips to the central point
                  of the gesture, at the start and at the end of the
                  gesture. Values in range [0.0, 1.0] are scaled up to
                  the distance from the coordinates to the edge of the
                  screen. Both finger tips will reach an edge if
                  distance is 1.0.

          finger1Dir, finger2Dir (integer, optional):
                  directions for finger tip movements, in range [0,
                  360]. 0 is to the east, 90 to the north, etc. The
                  defaults are 90 and 270.

          movePoints (integer, optional):
                  number of points to which finger tips are moved
                  after laying them to the initial positions. The
                  default is 20.

          duration (float, optional):
                  duration of the gesture in seconds, the default is 0.75.
        """
        screenWidth, screenHeight = self.screenSize()
        screenDiagonal = math.sqrt(screenWidth**2 + screenHeight**2)

        if x == None: x = 0.5
        if y == None: y = 0.5

        x, y = self.intCoords((x, y))

        if type(startDistance) == float and 0.0 <= startDistance <= 1.0:
            startDistanceInPixels = (
                startDistance *
                min(fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger1Dir),
                    fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger2Dir)))
        else:
            startDistanceInPixels = int(startDistance)

        if type(endDistance) == float and 0.0 <= endDistance <= 1.0:
            endDistanceInPixels = (
                endDistance *
                min(fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger1Dir),
                    fmbtgti._edgeDistanceInDirection((x, y), self.screenSize(), finger2Dir)))
        else:
            endDistanceInPixels = int(endDistance)

        finger1startX = int(x + math.cos(math.radians(finger1Dir)) * startDistanceInPixels)
        finger1startY = int(y - math.sin(math.radians(finger1Dir)) * startDistanceInPixels)
        finger1endX = int(x + math.cos(math.radians(finger1Dir)) * endDistanceInPixels)
        finger1endY = int(y - math.sin(math.radians(finger1Dir)) * endDistanceInPixels)

        finger2startX = int(x + math.cos(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2startY = int(y - math.sin(math.radians(finger2Dir)) * startDistanceInPixels)
        finger2endX = int(x + math.cos(math.radians(finger2Dir)) * endDistanceInPixels)
        finger2endY = int(y - math.sin(math.radians(finger2Dir)) * endDistanceInPixels)

        self.existingConnection().sendPinch(
            (finger1startX, finger1startY), (finger1endX, finger1endY),
            (finger2startX, finger2startY), (finger2endX, finger2endY),
            movePoints, duration)
        return True

    def pinchOpen(self, (x, y) = (0.5, 0.5), startDistance=0.1, endDistance=0.5, **pinchKwArgs):
        """
        Make the open pinch gesture.

        Parameters:
          x, y (integer, optional):
                  the central point of the gesture, the default is in
                  the middle of the screen.

          startDistance, endDistance (float, optional):
                  refer to pinch documentation. The default is 0.1 and
                  0.5.

          for the rest of the parameters, refer to pinch documentation.
        """
        return self.pinch((x, y), startDistance, endDistance, **pinchKwArgs)

    def pinchClose(self, (x, y) = (0.5, 0.5), startDistance=0.5, endDistance=0.1, **pinchKwArgs):
        """
        Make the close pinch gesture.

        Parameters:
          x, y (integer, optional):
                  the central point of the gesture, the default is in
                  the middle of the screen.

          startDistance, endDistance (float, optional):
                  refer to pinch documentation. The default is 0.5 and
                  0.1.

          rest of the parameters: refer to pinch documentation.
        """
        return self.pinch((x, y), startDistance, endDistance, **pinchKwArgs)


    def putFile(self, localFilename, remoteFilepath, data=None):
        """
        Send local file to the device.

        Parameters:

          localFilename (string):
                  file to be sent.

          remoteFilepath (string):
                  destination on the device. If destination is an
                  existing directory, the file will be saved to the
                  directory with its original local name. Otherwise the file
                  will be saved with remoteFilepath as new name.

          data (string, optional):
                  data to be stored to remoteFilepath. The default is
                  the data in the local file.

        Example: Copy local /tmp/file.txt to c:/temp
          putFile("/tmp/file.txt", "c:/temp/")

        Example: Create new remote file
          putFile(None, "c:/temp/file.txt", "remote file contents")
        """
        return self._conn.sendFile(localFilename, remoteFilepath, data)

    def rmFile(self, remoteFilepath):
        """
        Remove a file from the device.

        Parameters:

          remoteFilepath (string):
                  file to be removed from the device.
        """
        return self.existingConnection().evalPython(
            "os.remove(%s)" % (repr(remoteFilepath),))

    def reconnect(self, connspec=None, password=None):
        """
        Close connections to the device and reconnect.

        Parameters:

          connspec (string, optional):
                  Specification for new connection. The default is current
                  connspec.

          password (string, optional):
                  Password for new connection. The default is current password.
        """
        self.setConnection(None)
        import gc
        gc.collect()
        if connspec != None:
            self._connspec = connspec
        if password != None:
            self._password = password
        if self._connspec == None:
            _adapterLog("reconnect failed: missing connspec")
            return False
        try:
            self.setConnection(WindowsConnection(
                self._connspec, self._password, self))
            return True
        except Exception, e:
            _adapterLog("reconnect failed: %s" % (e,))
            return False

    def getDumpFilename(self, suffix):
        if self.screenshotDir() == None:
            self.setScreenshotDir(self._screenshotDirDefault)
        if self.screenshotSubdir() == None:
            self.setScreenshotSubdir(self._screenshotSubdirDefault)
        return self._newScreenshotFilepath()[:-3] + suffix


    def refreshView(self, window=None, forcedView=None, viewSource=None,
                    items=None, properties=None, area=None,
                    filterType="none", filterCondition="",
                    dumpChildClass="", dumpChildName="", doNotDump=False):
        """
        (Re)reads widgets on the top window and updates the latest view.

        Parameters:

          window (integer (hWnd) or string (title), optional):
                  read widgets from given window instead of the top window.

          forcedView (View or filename, optional):
                  use given View object or view file instead of reading the
                  items from the device.

          viewSource (string, optional):
                  source of UI information. Supported sources are:
                  "uiautomation" the UIAutomation framework.
                  "enumchildwindows" less data
                  but does not require UIAutomation.
                  The default is "uiautomation".
                  You can define TreeWalker used by "uiautomation" by defining
                  viewSource as "uiautomation/raw", "uiautomation/control" or
                  "uiautomation/content".
                  See also setViewSource().

          items (list of view items, optional):
                  update only contents of these items in the view.
                  Works only for "uiautomation" view source.

          properties (list of property names, optional):
                  read only given properties from items, the default
                  is to read all available properties.
                  Works only for "uiautomation" view source.
                  See also setViewSource().

          area ((left, top, right, bottom), optional):
                  refresh only items that intersect the area.
                  The default is None: locations do not affect refreshed
                  items.

          filterType (string, optional):
                  specify how the widgets should be filtered.
                  Supported values are:
                  "none", which is the default, which means that all widgets
                  will be retrieved.
                  "first": only the first element which satisfy the condition
                  defined by the filterCondition parameter is returned.
                  "all": all elements which satisfy the condition defined by
                  the filterCondition parameter are returned.
                  "first" and "all" allow to specify an additional "+children"
                  qualifier, which returns also all element's children.
                  So, passing "first+children" as filterType, then the element
                  all its children are returned, if the element (and only it)
                  satisfy filterCondition.
                  It's import to underline that the conditions defined by the
                  items, properties, and area, parameters are still all
                  applied on top of filterType and filterCondition.

          filterCondition (string, optional):
                  specify the condition for filtering the widgets.
                  It only works if filterType is not "none".
                  Currently only a basic filter conditions are supported, that
                  allows to specify a property name, the == operator, and
                  a double-quoted string with the value to be compared.
                  Filter conditions can be chained together using the "and"
                  operator; this allows more fine-grained filtering.
                  For example:
                      'ClassName == "ToolBar" and Name == "Explorer"'
                  matches all widgets whose "ClassName" property is equal
                  to "ToolBar" and the Name is "Explorer".
                  The list of currently allowed properties is the following:
                  AutomationId, ClassName, HelpText, LabeledBy, Name.

          dumpChildClass (string, optional):
                if specified, only widgets of this class will be dumped /
                reported. Otherwise all widgets will be dumped (if no other
                dumping option is given. See below).
                For example, setting dumpChildClass to "TextBlock" will
                return only this kind of widgets.
                Imagine a big ListView, where a single ListViewItem is a
                complex container / panel which incorporates several widgets,
                but you don't want to dump all of them, and you're interested
                only to the ones which carry textual information.
                You can do this using the filtering options to catch the
                ListView widget and visiting all its children/descendants,
                but setting dumpChildClass will give back only the TextBlocks.
                So, this is quite different from the above filtering options,
                because filtering only defines how the UI widgets are
                traversed (and eventually cached), whereas dumping defines
                what widgets will be really reported back and collected by
                the view.
                Filtering reduces the amount of widgets that will be
                evaluated. On top of that, dumping reduces the number of
                widgets that will be returned back to the view.

          dumpChildName (string, optional):
                if specified, only widgets with this name will be dumped /
                reported. Otherwise all widgets will be dumped (if no other
                dumping option is given).
                It works exactly like dumpChildClass, but works on the Name
                property. So, the same logic applies.
                It can be combined with dumpChildClass to further reduce the
                number of returned widgets.
                For example, dumpChildName = "Foo" will give back all widgets
                which have "Foo" as Name.

          doNotDump (boolean, optional):
                if specified, no widgets will be dumped / reported, regarding
                of all other dump options.
                It's used to only cache the widgets in the server. All widgets
                will be traversed and cached (if a cache option is defined).


        See also setRefreshViewDefaults().

        Returns View object.
        """
        if window == None:
            window = self._refreshViewDefaults.get("window", None)
        if forcedView == None:
            forcedView = self._refreshViewDefaults.get("forcedView", None)
        if viewSource == None:
            viewSource = self.viewSource()
        if not viewSource in _g_viewSources:
            raise ValueError('invalid view source "%s"' % (viewSource,))
        if items == None:
            items = self._refreshViewDefaults.get("items", [])
        if properties == None:
            properties = self._refreshViewDefaults.get("properties", None)
        if area == None:
            area = self._refreshViewDefaults.get("area", None)

        if forcedView != None:
            retryCount = 0
            startTime = time.time()
            lastStartTime = startTime
            viewFilename = forcedView
            if isinstance(forcedView, View):
                self._lastView = forcedView
            elif type(forcedView) in [str, unicode]:
                try:
                    self._lastView = View(
                        forcedView, ast.literal_eval(file(viewFilename).read()),
                        device=self, freeDumps=dumpChildClass or dumpChildName or doNotDump)
                except Exception:
                    self._lastView = None
            endTime = time.time()
        else:
            viewFilename = self.getDumpFilename("view")
            retryCount = 0
            startTime = time.time()
            lastStartTime = startTime
            while True:
                try:
                    topWindowBbox = self.topWindowProperties()['bbox']
                except TypeError:
                    topWindowBbox = None # top window unavailable
                if area:
                    leftTopRightBottom = (
                        self.intCoords((area[0], area[1])) +
                        self.intCoords((area[2], area[3])))
                else:
                    leftTopRightBottom = None
                if viewSource == "enumchildwindows":
                    viewData = self._conn.recvViewData(window)
                else:
                    if "/" in viewSource:
                        walker = viewSource.split("/")[1]
                    else:
                        walker = "raw"
                    if properties != None:
                        if properties == "all":
                            viewItemProperties = None
                        elif properties == "fast":
                            viewItemProperties = ["AutomationId",
                                                   "BoundingRectangle",
                                                   "ClassName",
                                                   "HelpText",
                                                   "ToggleState",
                                                   "Value",
                                                   "Minimum",
                                                   "Maximum",
                                                   "Name"]
                        elif isinstance(properties, list) or isinstance(properties, tuple):
                            viewItemProperties = list(properties)
                        else:
                            raise ValueError('invalid properties argument, expected "all", '
                                             '"fast" or a list')
                    else:
                        viewItemProperties = properties
                    viewData = self._conn.recvViewUIAutomation(
                        window, items, viewItemProperties, leftTopRightBottom, walker,
                        filterType, filterCondition, dumpChildClass, dumpChildName, doNotDump)
                file(viewFilename, "w").write(repr(viewData))
                try:
                    self._lastView = View(
                        viewFilename, viewData,
                        itemOnScreen=lambda i: self.itemOnScreen(i, topWindowBbox=topWindowBbox),
                        device=self, freeDumps=dumpChildClass or dumpChildName or doNotDump)
                    break
                except Exception, e:
                    self._lastView = None
                    _adapterLog(
                        "refreshView %s failed (%s), source=%s topWindow=%s" %
                        (retryCount, e, repr(viewSource), self.topWindow()))
                    retryCount += 1
                    if retryCount < self._refreshViewRetryLimit:
                        time.sleep(0.2)
                    else:
                        break
                lastStartTime = time.time()
            endTime = time.time()
        itemCount = -1
        if self._lastView:
            itemCount = len(self._lastView._viewItems)
        self._lastViewStats = {
            "retries": retryCount,
            "timestamp": endTime,
            "total time": endTime - startTime,
            "last time": endTime - lastStartTime,
            "filename": viewFilename,
            "source": viewSource,
            "forced": (forcedView != None),
            "window": window,
            "view": str(self._lastView),
            "item count": itemCount}
        return self._lastView

    def refreshViewDefaults(self):
        """Returns default arguments for refreshView() calls.

        See also setRefreshViewDefaults().
        """
        return dict(self._refreshViewDefaults)

    def setClipboard(self, data):
        """
        Set text on clipboard

        Parameters:

          data (string):
                  data to be set on the clipboard.

        Note: any type of data on clipboard will be emptied.

        See also: getClipboard()
        """
        return self.existingConnection().evalPython(
            "setClipboardText(%s)" % (repr(data),))

    def setErrorReporting(self, settings):
        """
        Modify Windows error reporting settings (WER)

        Parameters:
          settings (dictionary):
                  WER settings and values to be set.

        Example: disable showing interactive crash dialogs
          setErrorReporting({"DontShowUI": 1})

        See also: errorReporting(),
                  MSDN WER Settings.
        """
        for setting in settings:
            self.setRegistry(
                r"HKEY_CURRENT_USER\Software\Microsoft\Windows\Windows Error Reporting",
                setting, settings[setting])
        return True

    def setDisplaySize(self, size):
        """
        Transform coordinates of synthesized events (like a tap) from
        screenshot resolution to display input area size. By default
        events are synthesized directly to screenshot coordinates.

        Parameters:

          size (pair of integers: (width, height)):
                  width and height of display in pixels. If not given,
                  values from EnumDisplayMonitors are used.

        Returns None.
        """
        width, height = size
        screenWidth, screenHeight = self.screenSize()
        self._conn.setScreenToDisplayCoords(
            lambda x, y: (x * width / screenWidth,
                          y * height / screenHeight))
        self._conn.setDisplayToScreenCoords(
            lambda x, y: (x * screenWidth / width,
                          y * screenHeight / height))

    def setForegroundWindow(self, window):
        """
        Set a window with the title as a foreground window

        Parameters:

          window (title (string) or hwnd (integer):
                  title or handle of the window to be raised
                  foreground.

        Returns True if the window was brought to the foreground,
        otherwise False.

        Notes: calls SetForegroundWindow in user32.dll.
        """
        return self.existingConnection().sendSetForegroundWindow(window)

    def setRefreshViewDefaults(self, **kwargs):
        """Set new default arguments for refreshView() calls

        Parameters:
          **kwargs (keyword arguments)
                  new default values for optional refreshView() parameters.

        Note: default arguments are overridden by arguments given
        directly in refreshView calls.

        Note: setViewSource() can change the default arguments.

        Example:
          setRefreshViewDefaults(window="My app title",
                                 viewSource="uiautomation/content")

        """
        self._refreshViewDefaults = kwargs

    def findRegistry(self, rootKey, key=None, valueName=None, limit=1):
        """Search for key and/or valueName from the registry.

        Returns a list of matching (fullKeyPath, valueName) pairs
        found under the rootKey. The list has at most limit items, the
        default is 1.

        Parameters:

          rootKey (string):
                  root key path for the search. Example:
                  "HKEY_LOCAL_MACHINE".

          key (string, optional):
                  key name to be searched for under the rootKey.
                  The key is a regular expression that is searched for
                  from full key path. Use "\\name$" to require exact
                  match.
                  If not given, valueName should be defined.

          valueName (string, optional):
                  value name to be searched for under the rootKey.
                  The value can be a regular expression.
                  If not given, key should be defined and
                  returned valueName will be None.

          limit (integer, optional):
                  maximum number of matches to be returned. The
                  default is 1. limit=None returns all matching
                  pairs.

        Example:
          findRegistry("HKEY_LOCAL_MACHINE", key="\\Windows$")

        """
        if key == None and valueName == None:
            raise ValueError("either key or valueName must be provided")
        return self.existingConnection().evalPython(
            'findRegistry(%s, key=%s, valueName=%s, limit=%s)' % (
                repr(rootKey), repr(key), repr(valueName), repr(limit)))

    def setRegistry(self, key, valueName, value, valueType=None):
        """
        Set Windows registry value.

        Parameters:

          key (string):
                  full key name.

          valueName (string):
                  name of the value to be set.

          value (string):
                  string that specifies the new value.

          valueType (string, optional for str and int values):
                  REG_BINARY, REG_DWORD, REG_DWORD_LITTLE_ENDIAN,
                  REG_DWORD_BIG_ENDIAN, REG_EXPAND_SZ, REG_LINK,
                  REG_MULTI_SZ, REG_NONE, REG_RESOURCE_LIST or REG_SZ.
                  Default types for storing str and int values
                  are REG_SZ and REG_DWORD.

        Example:
          setRegistry(r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet"
                       "\Control\Session Manager\Environment",
                       "PATH", r"C:\MyExecutables", "REG_EXPAND_SZ")

        Returns True on success.
        """
        return self.existingConnection().evalPython(
            "setRegistry(%s,%s,%s,%s)" % (repr(key), repr(valueName),
                                          repr(value), repr(valueType)))

    def getRegistry(self, key, valueName):
        """
        Return Windows registry value and type

        Parameters:

          key (string):
                  full key name.

          valueName (string):
                  name of the value to be read.

        Returns a pair (value, valueType)

        Example:
          getRegistry(r"HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet"
                       "\Control\Session Manager\Environment", "PATH")
        """
        return self.existingConnection().evalPython(
            "getRegistry(%s,%s)" % (repr(key), repr(valueName)))

    def processList(self):
        """
        Return list of processes running on the device.

        Returns list of dictionaries with keys:
          "pid": process ID, and
          "ProcessImageFileName": full path to the executable in win32 format.
        """
        return self.existingConnection().evalPython("processList()")

    def processStatus(self, pid):
        """
        Return status of a process

        Parameters:

          pid (integer):
                  Process ID of the process

        Returns properties in a dictionary.

        Example:
          print "Memory usage:", processStatus(4242)["WorkingSetSize"]
        """
        return self.existingConnection().evalPython(
            "processStatus(%s)" % (repr(pid),))

    def productList(self):
        """
        Return list of products installed or advertised in the system

        Returns list of dictionaries, each containing properties of a product.
        """
        return self.existingConnection().evalPython("products()")

    def pycosh(self, command):
        """
        Run command in pycosh shell on the device.

        Parameters:

          command (string):
                  pycosh command to be executed. Pycosh implements
                  stripped-down versions of zip, tar, find, md5sum, diff,
                  grep, head, tail, curl,... the usual handy shell utils.
                  For information on pycosh commands, try
                  device.pycosh("help") or run in shell:
                  echo help | python -m pycosh.
        """
        return self.existingConnection().pycosh(command)

    def setScreenshotSize(self, size):
        """
        Force screenshots from device to use given resolution.
        Overrides detected monitor resolution on device.

        Parameters:

          size (pair of integers: (width, height)):
                  width and height of screenshot.
        """
        self._conn.setScreenshotSize(size)

    def setTopWindow(self, window):
        """
        Set a window as a foreground window and bring it to front.

        Parameters:

          window (title (string) or hwnd (integer):
                  title or handle of the window to be raised
                  foreground.

        Returns True if the window was brought to the foreground,
        otherwise False.

        Notes: calls SetForegroundWindow in user32.dll.
        """
        return self.existingConnection().sendSetTopWindow(window)

    def setViewSource(self, source, properties=None):
        """
        Set default view source for refreshView()

        Parameters:

          source (string):
                  default source, "enumchildwindow" or "uiautomation",
                  "uiautomation/raw", "uiautomation/control",
                  "uiautomation/content".

          properties (string or list of strings, optional):
                  set list of view item properties to be read.
                  "all" reads all available properties for each item.
                  "fast" reads a set of preselected properties.
                  list of strings reads properties in the list.
                  The default is "all".

        Returns None.

        See also refreshView(), viewSource(), refreshViewDefaults().
        """
        if not source in _g_viewSources:
            raise ValueError(
                'invalid view source "%s", expected one of: "%s"' %
                (source, '", "'.join(_g_viewSources)))
        if properties != None:
            self._refreshViewDefaults["properties"] = properties
        self._refreshViewDefaults["viewSource"] = source

    def shell(self, command):
        """
        Execute command in Windows.

        Parameters:

          command (string or list of strings):
                  command to be executed. Will be forwarded directly
                  to subprocess.check_output.  If command is a string,
                  then it will be executed in subshell, otherwise without
                  shell.

        Returns what is printed by the command.

        If you wish to receive exitstatus or standard output and error
        separated from command, refer to shellSOE().

        """
        return self._conn.evalPython('shell(%s)' % (repr(command),))

    def shellSOE(self, command, asyncStatus=None, asyncOut=None,
                 asyncError=None, cwd=None, timeout=None, env=None):
        """Execute command on Windows.

        Parameters:

          command (string or list of strings):
                  command to be executed. If command is a list of
                  string, it will be executed without shell
                  (subprocess.check_output with shell=False).
                  If command is a single-line string, it will be
                  executed in shell (subprocess.check_output with
                  shell=True).
                  If command is a multiline string, it will be written
                  to a BAT file and executed as a script.

          asyncStatus (string, True or None)
                  filename (on device) to which the status of
                  asynchronously executed shellCommand will be
                  written. If True, the command will be executed
                  asynchronously but exit status will not be
                  saved. The default is None, that is, command will be
                  run synchronously, and status will be returned in
                  the tuple.

          asyncOut (string, True or None)
                  filename (on device) to which the standard output of
                  asynchronously executed shellCommand will be
                  written. If True, the command will be executed
                  asynchronously but output will not saved. The
                  default is None.

          asyncError (string, True or None)
                  filename (on device) to which the standard error of
                  asynchronously executed shellCommand will be
                  written. If True, the command will be executed
                  asynchronously but standard error will not be
                  saved. The default is None.

          cwd (string, optional)
                  current working directory in which the command
                  will be executed. If not given, the cwd defaults
                  to the current working directory of the pythonshare
                  server process on the device, or the cwd of the Python
                  process if executed on host without pythonshare-server.

          timeout (float, optional)
                  forcefully kill child processes and return after
                  given time (in seconds). If timed out, returned output
                  and error strings contain what was printed until processes
                  were killed. Returned status is a fmbtwindows.Timeout
                  instance. Asynchronous executions cannot be timed out.
                  The default is None (no timeout).

          env (dictionary, optional)
                  defines variables and values for the environment
                  where the command will be executed.
                  - Variables that are not in the dictionary are
                    inherited from the pythonshare-server environment on
                    DUT.
                  - Variables with value None are removed from
                    inherited environment.
                  - Variables with string values override inherited
                    variables.
                  The default is None (no changes to inherited
                  environment).
                  Example: unset TEMPDIR and override default PATH
                  env={"TEMPDIR": None, "PATH": r"c:\windows\system32"}

        Returns triplet: exit status, standard output and standard error
        (int, str, str) from the command.

        If executing command fails, returns (None, None, None).

        If execution is timed out, returns (fmbtwindows.Timeout, str, str)
        or (fmbtwindows.Timeout, None, None) if outputs could not be read.
        """
        if (timeout != None and
            (asyncStatus, asyncOut, asyncError) != (None, None, None)):
            raise NotImplementedError(
                "timeout for asynchronous execution is not supported")
        s, o, e = self._conn.evalPython(
            'shellSOE(%s, asyncStatus=%s, asyncOut=%s, asyncError=%s, '
            'cwd=%s, timeout=%s, env=%s)'
            % (repr(command),
               repr(asyncStatus), repr(asyncOut), repr(asyncError),
               repr(cwd), repr(timeout), repr(env)))
        if isinstance(s, str) and s.startswith("TIMEOUT"):
            s = Timeout(command=command[:1024*8],
                        pid=int(s.split()[-1]))
        return s, o, e

    def showWindow(self, window, showCmd=SW_NORMAL):
        """
        Send showCmd to window.

        Parameters:

          window (window title (string) or handle (integer)):
                  window to which the command will be sent.

          showCmd (integer or string):
                  command to be sent. Valid commands are 0..11:
                  SW_HIDE, SW_NORMAL, SW_MINIMIZED, SW_MAXIMIZE,
                  SW_NOACTIVATE, SW_SHOW SW_MINIMIZE, SW_MINNOACTIVE,
                  SW_SHOWNA, SW_RESTORE, SW_DEFAULT, SW_FORCEMINIMIZE.

        Returns True if the window was previously visible,
        otherwise False.

        Notes: calls ShowWindow in user32.dll.
        """
        return self.existingConnection().sendShowWindow(window, showCmd)

    def tapText(self, text, partial=False, **tapKwArgs):
        """
        Find an item with given text from the latest view, and tap it.

        Parameters:

          partial (boolean, optional):
                  refer to verifyText documentation. The default is
                  False.

          tapPos (pair of floats (x, y)):
                  refer to tapItem documentation.

          button, long, hold, count, delayBetweenTaps (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        items = self.existingView().findItemsByText(text, partial=partial, count=1, onScreen=True)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def topWindow(self):
        """
        Returns a handle to the window.
        """
        return self.existingConnection().evalPython(
            "ctypes.windll.user32.GetForegroundWindow()")

    def topWindowProperties(self):
        """
        Return properties of the top window as a dictionary
        """
        return self._conn.recvTopWindowProperties()

    def verifyText(self, text, partial=False):
        """
        Verify that the last view has at least one item with given
        text.

        Parameters:

          text (string):
                  text to be searched for in items.

          partial (boolean, optional):
                  if True, match items if item text contains given
                  text, otherwise match only if item text is equal to
                  the given text. The default is False (exact match).
        """
        assert self._lastView != None, "View required."
        return self._lastView.findItemsByText(text, partial=partial, count=1, onScreen=True) != []

    def viewSource(self):
        """
        Returns current default view source.

        See also refreshView(), setViewSource().
        """
        return self._refreshViewDefaults.get(
            "viewSource", self._defaultViewSource)

    def windowList(self):
        """
        Return list of properties of windows (dictionaries)

        Example: list window handles and titles:
          for props in d.windowList():
              print props["hwnd"], props["title"]
        """
        return self._conn.recvWindowList()

    def windowProperties(self, window):
        """
        Returns properties of a window.

        Parameters:
          window (title (string) or hwnd (integer):
                  The window whose properties will be returned.

        Returns properties in a dictionary.
        """
        return self.existingConnection().recvWindowProperties(window)

    def windowStatus(self, window):
        """
        Returns status of a window.

        Parameters:
          window (title (string) or hwnd (integer):
                  The window whose properties will be returned.

        Returns status in a dictionary.
        """
        return self.existingConnection().recvWindowStatus(window)

    def view(self):
        return self._lastView

    def viewStats(self):
        return self._lastViewStats

class _NoPythonshareConnection(object):
    """Fake Pythonshare connection, evaluate everything locally"""
    def __init__(self, namespace="default"):
        self._namespaces = {}
        self._ns = namespace

    def exec_in(self, ns, code):
        if not ns in self._namespaces:
            self._namespaces[ns] = {}
        exec code in self._namespaces[ns]

    def eval_in(self, ns, expr):
        if not ns in self._namespaces:
            self._namespaces[ns] = {}
        return eval(expr, self._namespaces[ns])

    def namespace(self):
        return self._ns

class WindowsConnection(fmbtgti.GUITestConnection):
    def __init__(self, connspec, password, device):
        fmbtgti.GUITestConnection.__init__(self)
        self._device = device
        self._screenshotSize = (None, None) # autodetect
        self._pycosh_sent_to_dut = False
        if connspec != None:
            self._agent = pythonshare.connect(connspec, password=password)
        else:
            if os.name != "nt":
                raise ValueError("connecting to host works only on Windows")
            self._agent = _NoPythonshareConnection()
        self._agent_ns = self._agent.namespace()
        agentFilename = os.path.join(
            os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))),
            "fmbtwindows_agent.py")
        self._agent.exec_in(self._agent_ns, file(agentFilename).read())
        self.setScreenToDisplayCoords(lambda x, y: (x, y))
        self.setDisplayToScreenCoords(lambda x, y: (x, y))

    def pycosh(self, command):
        if not self._pycosh_sent_to_dut:
            # upload pycosh module to DUT
            try:
                self.evalPython("len(_g_pycosh_source)")
            except pythonshare.RemoteEvalError:
                self.execPython(file(inspect.getsourcefile(pycosh)).read())
            self._pycosh_sent_to_dut = True
        return self.evalPython("pycosh_eval(%s)" % (repr(command),))

    def setScreenshotSize(self, screenshotSize):
        self._screenshotSize = screenshotSize
        screenW, screenH = self._screenshotSize
        inputW, inputH = self._agent.eval_in(self._agent_ns, "_mouse_input_area")
        self.setScreenToDisplayCoords(
            lambda x, y: (x * inputW / screenW, y * inputH / screenH))
        self.setDisplayToScreenCoords(
            lambda x, y: (x * screenW / inputW, y * screenH / inputH))

    def execPython(self, code):
        return self._agent.exec_in(self._agent_ns, code)

    def evalPython(self, code):
        return self._agent.eval_in(self._agent_ns, code)

    def recvFile(self, remoteFilename, localFilename=None, compress=False):
        if compress:
            if isinstance(compress, int):
                compressLevel = compress
            else:
                compressLevel = 3
            data_b64_z = self._agent.eval_in(
                self._agent_ns,
                "base64.b64encode(zlib.compress(file(%s, 'rb').read(), %s))" % (
                    repr(remoteFilename), compressLevel))
            data = zlib.decompress(base64.b64decode(data_b64_z))
        else:
            data_b64 = self._agent.eval_in(
                self._agent_ns,
                "base64.b64encode(file(%s, 'rb').read())" % (repr(remoteFilename),))
            data = base64.b64decode(data_b64)
        if localFilename:
            file(localFilename, "wb").write(data)
            return True
        else:
            return data

    def sendFile(self, localFilename, remoteFilepath, data=None):
        sendBlockMaxLen = 10 * 1024 * 1024 # Send at most 10 MB at a time
        sendDataFromFile = False
        if data == None:
            fileSize = os.stat(localFilename).st_size
            if fileSize < sendBlockMaxLen:
                data = open(localFilename, "rb").read()
            else:
                data = ""
                dataFile = open(localFilename, "rb")
                sendDataFromFile = True
        if localFilename:
            basename = os.path.basename(localFilename)
        else:
            basename = localFilename
        if sendDataFromFile:
            dataLen = fileSize
        else:
            dataLen = len(data)
        sendIndex = 0
        while sendIndex < dataLen or dataLen == 0:
            if sendDataFromFile:
                sendData = dataFile.read(sendBlockMaxLen)
            else:
                sendData = data[sendIndex:sendIndex + sendBlockMaxLen]
            rv = self.evalPython(
                'saveFile(%s, %s, base64.b64decode(%s), append=%s)' %
                (repr(basename),
                 repr(remoteFilepath),
                 repr(base64.b64encode(sendData)),
                 repr(sendIndex != 0)))
            sendIndex += sendBlockMaxLen
            if not rv or dataLen == 0:
                break
        if sendDataFromFile:
            dataFile.close()
        return rv

    def recvMatchingPaths(self, pathnamePattern):
        filepaths = self._agent.eval_in(
            self._agent_ns,
            "glob.glob(%s)" % (repr(pathnamePattern),))
        if "/" in pathnamePattern:
            # Unix-style directory naming in input,
            # stick with it and fix mixed / and \ that might
            # come out from glob.glob.
            return [p.replace('\\', '/') for p in filepaths]
        else:
            # use glob output as it is
            return filepaths

    def recvScreenshot(self, filename, screenshotSize=(None, None)):
        ppmfilename = filename + ".ppm"

        if screenshotSize == (None, None):
            screenshotSize = self._screenshotSize

        width, height, zdata = self._agent.eval_in(
            self._agent_ns, "screenshotZYBGR(%s)" % (repr(screenshotSize),))

        data = zlib.decompress(zdata)

        fmbtgti.eye4graphics.wbgr2rgb(data, width, height)
        if fmbtpng != None:
            file(filename, "wb").write(
                fmbtpng.raw2png(data, width, height, 8, "RGB"))
        else:
            ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)

            f = file(filename + ".ppm", "wb")
            f.write(ppm_header)
            f.write(data)
            f.close()
            _run([fmbt_config.imagemagick_convert, ppmfilename, filename], expectedExitStatus=[0])
            os.remove(ppmfilename)
        return True

    def recvTopWindowProperties(self):
        return self.evalPython("topWindowProperties()")

    def recvWindowProperties(self, window):
        hwnd = self._window2hwnd(window)
        return self.evalPython("windowProperties(%s)" % (hwnd,))

    def recvWindowStatus(self, window):
        hwnd = self._window2hwnd(window)
        return self.evalPython("windowStatus(%s)" % (hwnd,))

    def recvViewData(self, window=None):
        rv = None
        if window == None:
            rv = self.evalPython("topWindowWidgets()")
        elif isinstance(window, int):
            rv = self.evalPython("windowWidgets(%s)" % (repr(window),))
        elif isinstance(window, str) or isinstance(window, unicode):
            wlist = self.evalPython("windowList()")
            for w in wlist:
                if w["title"] == window:
                    rv = self.evalPython("windowWidgets(%s)" % (repr(w["hwnd"]),))
                    break
            else:
                raise ValueError('no window with title "%s"' % (window,))
        else:
            raise ValueError('illegal window "%s", expected integer or string (hWnd or title)' % (window,))
        return rv

    def _parseDumps(self, dumps, dump_suffix, error_template):
        dumpFilename = self._device.getDumpFilename(dump_suffix) + '.log'
        error_message = ''
        rv = []
        prop_data = {}
        items = None
        with open(dumpFilename, 'w') as f:
            for dump in dumps:
                f.write(dump + '\n')
                for line in dump.split('\0'):
                    if line.startswith('!'):
                        error_message = line[1:]
                        continue
                    if line.startswith('#'):  # It's a comment / debug output: skip it!
                        continue
                    if line == '[':
                        items = []
                        continue
                    if line == ']':
                        rv.append(items)
                        continue
                    if items is not None:
                        items.append(line)
                    if "=" not in line:
                        continue
                    prop_name, prop_value = line.split("=", 1)
                    if prop_name == "hash" and prop_data:
                        rv.append(prop_data)
                        prop_data = {}
                    prop_data[prop_name] = prop_value.replace(r"\r\n", "\n").replace(r"\\", "\\")
        if prop_data:
            rv.append(prop_data)
        if error_message:
            raise FMBTWindowsError(error_template % error_message)
        return rv

    def recvViewUIAutomation(self, window=None, items=[], properties=None, area=None, walker="raw",
        filterType="none", filterCondition="", dumpChildClass="", dumpChildName="", doNotDump=False):
        """returns list of dictionaries, each of which contains properties of
        an item"""
        if not walker in ["raw", "control", "content"]:
            raise ValueError('invalid walker %r' % walker)
        hwnd = self._window2hwnd(window) if window else None
        if properties is None:
            properties = []
        else:
            # make sure certain properties are always included
            properties = list(frozenset(properties) | frozenset(["BoundingRectangle"]))
        dumps = []
        if items:
            for item in items:
                dumps.append(self.evalPython("dumpUIAutomationElements(%r, %r, %r, %r, %r, %r, %r, %r, %r, %r)" % (
                    hwnd,
                    [str(item.id()) for item in item.branch()],
                    properties,
                    area,
                    walker,
                    filterType,
                    filterCondition,
                    dumpChildClass,
                    dumpChildName,
                    doNotDump)))
        else:
            dumps.append(self.evalPython("dumpUIAutomationElements(%r, %r, %r, %r, %r, %r, %r, %r, %r, %r)" % (
                hwnd,
                [],
                properties,
                area,
                walker,
                filterType,
                filterCondition,
                dumpChildClass,
                dumpChildName,
                doNotDump)))
        return self._parseDumps(dumps, "dumpUIAutomationElements",
            "view is not available. An error happened while collecting UI elements with refreshView().\n%s")

    def sendSetCacheMode(self, mode):
        dump = self.evalPython("serverSetCacheMode(%r)" % mode)
        self._parseDumps([dump], "serverSetCacheMode",
            "An error happened while setting the cache mode.\n%s")

    def sendClearCache(self):
        dump = self.evalPython("serverClearCache()")
        self._parseDumps([dump], "serverClearCache",
            "An error happened while clearing the cache.\n%s")

    def sendSetFocus(self, eltHash):
        dump = self.evalPython("setAutomationElementFocus(%s)" % eltHash)
        self._parseDumps([dump], "setAutomationElementFocus",
            "An error happened while setting the focus.\n%s")

    def sendCollapse(self, eltHash):
        dump = self.evalPython("AutomationElementCollapse(%s)" % eltHash)
        self._parseDumps([dump], "AutomationElementCollapse",
            "An error happened while collapsing the viewitem.\n%s")

    def sendExpand(self, eltHash):
        dump = self.evalPython("AutomationElementExpand(%s)" % eltHash)
        self._parseDumps([dump], "AutomationElementExpand",
            "An error happened while expanding the viewitem.\n%s")

    def recvViewCachedItem(self, eltHash):
        dump = self.evalPython("getCachedAutomationElement(%s)" % eltHash)
        return self._parseDumps([dump], "getCachedAutomationElement",
            "viewitem is not available. An error happened while dumping it with cachedElement().\n%s")

    def recvViewItemPatterns(self, eltHash):
        dump = self.evalPython("getAutomationElementPatterns(%s)" % eltHash)
        return self._parseDumps([dump], "getAutomationElementPatterns",
            "viewitem patterns are not available. An error happened while collecting them with patterns().\n%s")

    def recvViewItemProperties(self, eltHash):
        dump = self.evalPython("getAutomationElementProperties(%s)" % eltHash)
        return self._parseDumps([dump], "getAutomationElementProperties",
            "viewitem properties are not available. An error happened while collecting them with refresh().\n%s")

    def recvViewItemItems(self, eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren):
        dump = self.evalPython("getAutomationElementItems(%s, %r, %r, %r, %r)" % (
            eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren))
        return self._parseDumps([dump], "getAutomationElementItems",
            "viewitem items aren't available. An error happened while getting it with items().\n%s")

    def recvViewItemContainerItems(self, eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll):
        dump = self.evalPython("getAutomationElementContainerItems(%s, %r, %r, %r, %r, %r)" % (
            eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll))
        return self._parseDumps([dump], "getAutomationElementContainerItems",
            "viewitem items aren't available. An error happened while getting it with containerItems().\n%s")

    def recvViewItemSelectedItems(self, eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll):
        dump = self.evalPython("getAutomationElementSelectedItems(%s, %r, %r, %r, %r, %r)" % (
            eltHash, propertyName, separator, filterSubChildClassName, maxSubChildren, scroll))
        return self._parseDumps([dump], "getAutomationElementSelectedItems",
            "viewitem selected items aren't available. An error happened while getting it with selectedItems().\n%s")

    def recvViewItemText(self, eltHash, maxLength):
        dump = self.evalPython("getAutomationElementText(%s, %s)" % (eltHash, maxLength))
        return self._parseDumps([dump], "getAutomationElementText",
            "viewitem text isn't available. An error happened while getting it with longText().\n%s")

    def recvViewItemSetValue(self, eltHash, value):
        dump = self.evalPython("setAutomationElementValue(%s, %r)" % (eltHash, value))
        return self._parseDumps([dump], "setAutomationElementValue",
            "viewitem value isn't editable. An error happened while setting it with setValue().\n%s")

    def recvWindowList(self):
        return self.evalPython("windowList()")

    def _window2hwnd(self, window):
        if isinstance(window, str) or isinstance(window, unicode):
            windowList = self.recvWindowList()
            hwndList = [w["hwnd"] for w in windowList if w["title"] == window]
            if not hwndList:
                raise ValueError('no window with title "%s"' % (window,))
            hwnd = hwndList[0]
        elif isinstance(window, dict) and "hwnd" in window:
            hwnd = window["hwnd"]
        elif isinstance(window, int) or isinstance(window, long):
            hwnd = window
        else:
            raise ValueError('invalid window "%s", string, integer or dict with "hwnd" key expected' % (window,))
        return hwnd

    def sendCloseWindow(self, window):
        hwnd = self._window2hwnd(window)
        return self.evalPython("closeWindow(%s)" % (repr(hwnd),))

    def sendSetForegroundWindow(self, window):
        hwnd = self._window2hwnd(window)
        return 0 != self.evalPython("ctypes.windll.user32.SetForegroundWindow(%s)" %
                                    (repr(hwnd),))

    def sendSetTopWindow(self, window):
        hwnd = self._window2hwnd(window)
        return 0 != self.evalPython("setTopWindow(%s)" %
                                    (repr(hwnd),))

    def sendShowWindow(self, window, showCmd):
        hwnd = self._window2hwnd(window)
        return self.evalPython("showWindow(%s, %s)" % (repr(hwnd), repr(showCmd)))

    def sendType(self, text):
        command = 'sendType(%s)' % (repr(text),)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendPress(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKey(%r,[])' % (keyCode,)
        else:
            command = 'sendKey(%r,%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyDown(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyDown(%r,[])' % (keyCode,)
        else:
            command = 'sendKeyDown(%r,%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendKeyUp(self, keyCode, modifiers=None):
        if modifiers == None:
            command = 'sendKeyUp(%r,[])' % (keyCode,)
        else:
            command = 'sendKeyUp(%r,%s)' % (keyCode, repr(modifiers))
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTap(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTap(%s, %s)" % (x, y)
        else:
            command = "sendClick(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchDown(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchDown(%s, %s)" % (x, y)
        else:
            command = "(sendMouseMove(%s, %s), sendMouseDown(%s))" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchMove(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchMove(%s, %s)" % (x, y)
        else:
            command = "sendMouseMove(%s, %s, %s)" % (x, y, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendTouchUp(self, x, y, button=None):
        x, y = self._screenToDisplay(x, y)
        if button == None:
            command = "sendTouchUp(%s, %s)" % (x, y)
        else:
            command = "(sendMouseMove(%s, %s, %s), sendMouseUp(%s))" % (
                x, y, button, button)
        self._agent.eval_in(self._agent_ns, command)
        return True

    def sendPinch(self, *args):
        self.evalPython("touchPinch%s" % (args,))
        return True

    def setScreenToDisplayCoords(self, screenToDisplayFunction):
        self._screenToDisplay = screenToDisplayFunction

    def setDisplayToScreenCoords(self, displayToScreenFunction):
        self._displayToScreen = displayToScreenFunction

class FMBTWindowsError(Exception): pass
