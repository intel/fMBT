# fMBT, free Model Based Testing tool
# Copyright (c) 2013-2016, Intel Corporation.
#
# This program is free software; you can redistribute it and/or modify it
# under the terms and conditions of the GNU Lesser General Public License,
# version 2.1, as published by the Free Software Foundation.
#
# This program is distributed in the hope it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin St - Fifth Floor, Boston, MA 02110-1301 USA.

"""
This library implements fmbt GUITestInterface for X.

Using Screen.refreshView() requires the pyatspi library and enabling
accessilibity. For example:

gsettings set org.gnome.desktop.interface toolkit-accessibility true
"""

import fmbt_config
import fmbtgti

fmbtgti._OCRPREPROCESS = [
    "",
    "-sharpen 5 -level 90%%,100%%,3.0 -sharpen 5"
    ]

import ctypes
import os
import subprocess
import zlib

import fmbtx11_conn

def _run(command):
    exit_status = subprocess.call(command,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  shell=False,
                                  close_fds=(os.name != "nt"))
    return exit_status

sortItems = fmbtgti.sortItems

class ViewItem(fmbtgti.GUIItem):
    def __init__(self, view, itemId, parentId, className, text, bbox,
                 dumpFilename, rawProperties=None):
        self._view = view
        self._itemId = itemId
        self._parentId = parentId
        self._className = className
        self._text = text
        if rawProperties:
            self._properties = rawProperties
        else:
            self._properties = {}
        fmbtgti.GUIItem.__init__(self, self._className, bbox, dumpFilename)

    def branch(self):
        """Returns list of view items from the root down to this item"""
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
        items = self._view._viewItems
        return [items[itemId]
                for itemId in items
                if items[itemId]._parentId == self._itemId]

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
        rv = []
        if self._properties:
            for key in sorted(self._properties.keys()):
                rv.append("%s=%s" % (key, self._properties[key]))
        return "\n".join(rv)

    def __str__(self):
        return "ViewItem(%s)" % (self._view._dumpItem(self),)


class View(object):
    def __init__(self, dumpFilename, itemTree, itemOnScreen=None):
        self._dumpFilename = dumpFilename
        self._itemTree = itemTree
        self._rootItem = None
        self._viewItems = {}
        if itemOnScreen == None:
            self._itemOnScreen = lambda item: True
        else:
            self._itemOnScreen = itemOnScreen
        self._viewSource = "atspi"
        for item in itemTree:
            className = item.get("class", "")
            text = item.get("text", "")
            if text == "" or text == None:
                text = item.get("name", "")
            if text == "":
                text = className
            vi = ViewItem(
                self, item["id"], item["parent"],
                className,
                text,
                item["bbox"],
                dumpFilename,
                item)
            self._viewItems[item["id"]] = vi
            if vi.parent() == None:
                self._rootItem = vi
        if not self._rootItem:
            raise ValueError("no root item in view data")

    def _intCoords(self, *args):
        # TODO: relative coordinates like (0.5, 0.9)
        return [int(c) for c in args[0]]

    def filename(self):
        return self._dumpFilename

    def rootItem(self):
        return self._rootItem

    def _dumpItem(self, viewItem):
        return "id=%s cls=%s text=%s bbox=%s" % (
            viewItem._itemId, repr(viewItem._className), repr(viewItem._text),
            viewItem._bbox)

    def _dumpTree(self, rootItem, depth=0):
        l = ["%s%s" % (" " * (depth * 4), self._dumpItem(rootItem))]
        for child in rootItem.children():
            l.extend(self._dumpTree(child, depth+1))
        return l

    def dumpTree(self, rootItem=None):
        """
        Returns item tree as a string
        """
        if rootItem == None:
            rootItem = self.rootItem()
        return "\n".join(self._dumpTree(rootItem))

    def __str__(self):
        return "View(%s, %s items)" % (repr(self._dumpFilename), len(self._viewItems))

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
            c = lambda item: (text in item._text or text in item.properties()["name"])
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


class Screen(fmbtgti.GUITestInterface):
    def __init__(self, display="", **kwargs):
        """Parameters:

          display (string, optional)
                  X display to connect to.
                  Example: display=":0". The default is "", that is,
                  the default X display in the DISPLAY environment
                  variable will be used.

          rotateScreenshot (integer, optional)
                  rotate new screenshots by rotateScreenshot degrees.
                  Example: rotateScreenshot=-90. The default is 0 (no
                  rotation).
        """
        fmbtgti.GUITestInterface.__init__(self, **kwargs)
        self._lastView = None
        self._refreshViewDefaults = {}
        self.setConnection(X11Connection(display))

    def atspiApplicationList(self):
        """Returns list of running ATSPI applications.

        refreshView with view source "atspi" works for these
        applications.
        """
        return fmbtx11_conn.atspiApplicationList()

    def existingView(self):
        if self._lastView:
            return self._lastView
        else:
            raise FMBTWindowsError("view is not available. Missing refreshView()?")

    def itemOnScreen(self, guiItem):
        maxX, maxY = self.screenSize()
        return fmbtgti._boxOnRegion(guiItem.bbox(), (0, 0, maxX, maxY))

    def keyNames(self):
        return _keyNames[:]

    def refreshView(self, window=None, forcedView=None, viewSource=None):
        """Update toolkit data"""
        self._lastView = None
        if window == None:
            window = self._refreshViewDefaults.get("window", None)
        if viewSource == None:
            viewSource = self._refreshViewDefaults.get("viewSource", "atspi")
        if viewSource == "atspi":
            foundItems = self.existingConnection().recvAtspiViewData(window)
            if self.screenshotDir() == None:
                self.setScreenshotDir(self._screenshotDirDefault)
            if self.screenshotSubdir() == None:
                self.setScreenshotSubdir(self._screenshotSubdirDefault)
            viewFilename = self._newScreenshotFilepath()[:-3] + "view"
            file(viewFilename, "w").write(repr(foundItems))
            self._lastView = View(
                viewFilename, foundItems,
                itemOnScreen=lambda i: self.itemOnScreen(i))
        else:
            raise ValueError('viewSource "%s" not supported' % (viewSource,))
        return self._lastView

    def refreshViewDefaults(self):
        return self._refreshViewDefaults

    def setRefreshViewDefaults(self, **kwargs):
        """Set default arguments for refreshView() calls

        Parameters:
          **kwargs (keyword arguments)
                  new default values for optional refreshView() parameters.
        """
        self._refreshViewDefaults = kwargs

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

    def view(self):
        return self._lastView

    def windowList(self):
        """
        Return list of properties of windows (dictionaries)

        Example: list window id's and names:
          for props in screen.windowList():
              print props["window"], props["name"]
        """
        return self.existingConnection().recvChildWindows(recursive=True)

class X11Connection(fmbtx11_conn.Display):
    def __init__(self, display):
        fmbtx11_conn.Display.__init__(self, display)

    def target(self):
        return "X11"

    def recvAtspiViewData(self, window):
        return fmbtx11_conn.atspiViewData(window)

    def recvScreenshot(self, filename):
        # This is a hack to get this stack quickly testable,
        # let's replace this with Xlib/libMagick functions, too...
        data = fmbtx11_conn.Display.recvScreenshot(self, "PNG")
        if data:
            if data.startswith("FMBTRAWX11"):
                try:
                    header, zdata = data.split('\n', 1)
                    width, height, depth, bpp = [int(n) for n in header.split()[1:]]
                    data = zlib.decompress(zdata)
                except Exception, e:
                    raise FMBTX11Error("Corrupted screenshot data: %s" % (e,))

                if len(data) != width * height * 4:
                    raise FMBTX11Error("Image data size mismatch.")

                fmbtgti.eye4graphics.bgrx2rgb(data, width, height)
                ppm_header = "P6\n%d %d\n%d\n" % (width, height, 255)
                f = file(filename + ".ppm", "w").write(ppm_header + data[:width*height*3])
                _run([fmbt_config.imagemagick_convert, filename + ".ppm", filename])
                os.remove("%s.ppm" % (filename,))
            elif fmbtx11_conn.fmbtpng and data.startswith(fmbtx11_conn.fmbtpng.PNG_MAGIC):
                file(filename, "w").write(data)
            else:
                raise FMBTX11Error('Unsupported image format "%s"...' % (data[:4],))
        else:
            return False
        return True

class FMBTX11Error(Exception): pass
X11ConnectionError = fmbtx11_conn.X11ConnectionError

_keyNames = [ "VoidSymbol", "BackSpace", "Tab", "Linefeed", "Clear",
              "Return", "Pause", "Scroll_Lock", "Sys_Req", "Escape",
              "Delete", "Multi_key", "Codeinput", "SingleCandidate",
              "MultipleCandidate", "PreviousCandidate", "Kanji",
              "Muhenkan", "Henkan_Mode", "Henkan", "Romaji",
              "Hiragana", "Katakana", "Hiragana_Katakana", "Zenkaku",
              "Hankaku", "Zenkaku_Hankaku", "Touroku", "Massyo",
              "Kana_Lock", "Kana_Shift", "Eisu_Shift", "Eisu_toggle",
              "Kanji_Bangou", "Zen_Koho", "Mae_Koho", "Home", "Left",
              "Up", "Right", "Down", "Prior", "Page_Up", "Next",
              "Page_Down", "End", "Begin", "Select", "Print",
              "Execute", "Insert", "Undo", "Redo", "Menu", "Find",
              "Cancel", "Help", "Break", "Mode_switch",
              "script_switch", "Num_Lock", "KP_Space", "KP_Tab",
              "KP_Enter", "KP_F1", "KP_F2", "KP_F3", "KP_F4",
              "KP_Home", "KP_Left", "KP_Up", "KP_Right", "KP_Down",
              "KP_Prior", "KP_Page_Up", "KP_Next", "KP_Page_Down",
              "KP_End", "KP_Begin", "KP_Insert", "KP_Delete",
              "KP_Equal", "KP_Multiply", "KP_Add", "KP_Separator",
              "KP_Subtract", "KP_Decimal", "KP_Divide", "KP_0",
              "KP_1", "KP_2", "KP_3", "KP_4", "KP_5", "KP_6", "KP_7",
              "KP_8", "KP_9", "F1", "F2", "F3", "F4", "F5", "F6",
              "F7", "F8", "F9", "F10", "F11", "L1", "F12", "L2",
              "F13", "L3", "F14", "L4", "F15", "L5", "F16", "L6",
              "F17", "L7", "F18", "L8", "F19", "L9", "F20", "L10",
              "F21", "R1", "F22", "R2", "F23", "R3", "F24", "R4",
              "F25", "R5", "F26", "R6", "F27", "R7", "F28", "R8",
              "F29", "R9", "F30", "R10", "F31", "R11", "F32", "R12",
              "F33", "R13", "F34", "R14", "F35", "R15", "Shift_L",
              "Shift_R", "Control_L", "Control_R", "Caps_Lock",
              "Shift_Lock", "Meta_L", "Meta_R", "Alt_L", "Alt_R",
              "Super_L", "Super_R", "Hyper_L", "Hyper_R", "ISO_Lock",
              "ISO_Level2_Latch", "ISO_Level3_Shift",
              "ISO_Level3_Latch", "ISO_Level3_Lock",
              "ISO_Level5_Shift", "ISO_Level5_Latch",
              "ISO_Level5_Lock", "ISO_Group_Shift", "ISO_Group_Latch",
              "ISO_Group_Lock", "ISO_Next_Group",
              "ISO_Next_Group_Lock", "ISO_Prev_Group",
              "ISO_Prev_Group_Lock", "ISO_First_Group",
              "ISO_First_Group_Lock", "ISO_Last_Group",
              "ISO_Last_Group_Lock", "ISO_Left_Tab",
              "ISO_Move_Line_Up", "ISO_Move_Line_Down",
              "ISO_Partial_Line_Up", "ISO_Partial_Line_Down",
              "ISO_Partial_Space_Left", "ISO_Partial_Space_Right",
              "ISO_Set_Margin_Left", "ISO_Set_Margin_Right",
              "ISO_Release_Margin_Left", "ISO_Release_Margin_Right",
              "ISO_Release_Both_Margins", "ISO_Fast_Cursor_Left",
              "ISO_Fast_Cursor_Right", "ISO_Fast_Cursor_Up",
              "ISO_Fast_Cursor_Down", "ISO_Continuous_Underline",
              "ISO_Discontinuous_Underline", "ISO_Emphasize",
              "ISO_Center_Object", "ISO_Enter", "dead_grave",
              "dead_acute", "dead_circumflex", "dead_tilde",
              "dead_perispomeni", "dead_macron", "dead_breve",
              "dead_abovedot", "dead_diaeresis", "dead_abovering",
              "dead_doubleacute", "dead_caron", "dead_cedilla",
              "dead_ogonek", "dead_iota", "dead_voiced_sound",
              "dead_semivoiced_sound", "dead_belowdot", "dead_hook",
              "dead_horn", "dead_stroke", "dead_abovecomma",
              "dead_psili", "dead_abovereversedcomma", "dead_dasia",
              "dead_doublegrave", "dead_belowring",
              "dead_belowmacron", "dead_belowcircumflex",
              "dead_belowtilde", "dead_belowbreve",
              "dead_belowdiaeresis", "dead_invertedbreve",
              "dead_belowcomma", "dead_currency", "dead_a", "dead_A",
              "dead_e", "dead_E", "dead_i", "dead_I", "dead_o",
              "dead_O", "dead_u", "dead_U", "dead_small_schwa",
              "dead_capital_schwa", "dead_greek",
              "First_Virtual_Screen", "Prev_Virtual_Screen",
              "Next_Virtual_Screen", "Last_Virtual_Screen",
              "Terminate_Server", "AccessX_Enable",
              "AccessX_Feedback_Enable", "RepeatKeys_Enable",
              "SlowKeys_Enable", "BounceKeys_Enable",
              "StickyKeys_Enable", "MouseKeys_Enable",
              "MouseKeys_Accel_Enable", "Overlay1_Enable",
              "Overlay2_Enable", "AudibleBell_Enable", "Pointer_Left",
              "Pointer_Right", "Pointer_Up", "Pointer_Down",
              "Pointer_UpLeft", "Pointer_UpRight", "Pointer_DownLeft",
              "Pointer_DownRight", "Pointer_Button_Dflt",
              "Pointer_Button1", "Pointer_Button2", "Pointer_Button3",
              "Pointer_Button4", "Pointer_Button5",
              "Pointer_DblClick_Dflt", "Pointer_DblClick1",
              "Pointer_DblClick2", "Pointer_DblClick3",
              "Pointer_DblClick4", "Pointer_DblClick5",
              "Pointer_Drag_Dflt", "Pointer_Drag1", "Pointer_Drag2",
              "Pointer_Drag3", "Pointer_Drag4", "Pointer_Drag5",
              "Pointer_EnableKeys", "Pointer_Accelerate",
              "Pointer_DfltBtnNext", "Pointer_DfltBtnPrev", "ch",
              "Ch", "CH", "c_h", "C_h", "C_H", "space", "exclam",
              "quotedbl", "numbersign", "dollar", "percent",
              "ampersand", "apostrophe", "quoteright", "parenleft",
              "parenright", "asterisk", "plus", "comma", "minus",
              "period", "slash", "0", "1", "2", "3", "4", "5", "6",
              "7", "8", "9", "colon", "semicolon", "less", "equal",
              "greater", "question", "at", "A", "B", "C", "D", "E",
              "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
              "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
              "bracketleft", "backslash", "bracketright",
              "asciicircum", "underscore", "grave", "quoteleft", "a",
              "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l",
              "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w",
              "x", "y", "z", "braceleft", "bar", "braceright",
              "asciitilde", "nobreakspace", "exclamdown", "cent",
              "sterling", "currency", "yen", "brokenbar", "section",
              "diaeresis", "copyright", "ordfeminine",
              "guillemotleft", "notsign", "hyphen", "registered",
              "macron", "degree", "plusminus", "twosuperior",
              "threesuperior", "acute", "mu", "paragraph",
              "periodcentered", "cedilla", "onesuperior", "masculine",
              "guillemotright", "onequarter", "onehalf",
              "threequarters", "questiondown", "Agrave", "Aacute",
              "Acircumflex", "Atilde", "Adiaeresis", "Aring", "AE",
              "Ccedilla", "Egrave", "Eacute", "Ecircumflex",
              "Ediaeresis", "Igrave", "Iacute", "Icircumflex",
              "Idiaeresis", "ETH", "Eth", "Ntilde", "Ograve",
              "Oacute", "Ocircumflex", "Otilde", "Odiaeresis",
              "multiply", "Oslash", "Ooblique", "Ugrave", "Uacute",
              "Ucircumflex", "Udiaeresis", "Yacute", "THORN", "Thorn",
              "ssharp", "agrave", "aacute", "acircumflex", "atilde",
              "adiaeresis", "aring", "ae", "ccedilla", "egrave",
              "eacute", "ecircumflex", "ediaeresis", "igrave",
              "iacute", "icircumflex", "idiaeresis", "eth", "ntilde",
              "ograve", "oacute", "ocircumflex", "otilde",
              "odiaeresis", "division", "oslash", "ooblique",
              "ugrave", "uacute", "ucircumflex", "udiaeresis",
              "yacute", "thorn", "ydiaeresis", "Aogonek", "breve",
              "Lstroke", "Lcaron", "Sacute", "Scaron", "Scedilla",
              "Tcaron", "Zacute", "Zcaron", "Zabovedot", "aogonek",
              "ogonek", "lstroke", "lcaron", "sacute", "caron",
              "scaron", "scedilla", "tcaron", "zacute", "doubleacute",
              "zcaron", "zabovedot", "Racute", "Abreve", "Lacute",
              "Cacute", "Ccaron", "Eogonek", "Ecaron", "Dcaron",
              "Dstroke", "Nacute", "Ncaron", "Odoubleacute", "Rcaron",
              "Uring", "Udoubleacute", "Tcedilla", "racute", "abreve",
              "lacute", "cacute", "ccaron", "eogonek", "ecaron",
              "dcaron", "dstroke", "nacute", "ncaron", "odoubleacute",
              "rcaron", "uring", "udoubleacute", "tcedilla",
              "abovedot", "Hstroke", "Hcircumflex", "Iabovedot",
              "Gbreve", "Jcircumflex", "hstroke", "hcircumflex",
              "idotless", "gbreve", "jcircumflex", "Cabovedot",
              "Ccircumflex", "Gabovedot", "Gcircumflex", "Ubreve",
              "Scircumflex", "cabovedot", "ccircumflex", "gabovedot",
              "gcircumflex", "ubreve", "scircumflex", "kra", "kappa",
              "Rcedilla", "Itilde", "Lcedilla", "Emacron", "Gcedilla",
              "Tslash", "rcedilla", "itilde", "lcedilla", "emacron",
              "gcedilla", "tslash", "ENG", "eng", "Amacron",
              "Iogonek", "Eabovedot", "Imacron", "Ncedilla",
              "Omacron", "Kcedilla", "Uogonek", "Utilde", "Umacron",
              "amacron", "iogonek", "eabovedot", "imacron",
              "ncedilla", "omacron", "kcedilla", "uogonek", "utilde",
              "umacron", "Wcircumflex", "wcircumflex", "Ycircumflex",
              "ycircumflex", "Babovedot", "babovedot", "Dabovedot",
              "dabovedot", "Fabovedot", "fabovedot", "Mabovedot",
              "mabovedot", "Pabovedot", "pabovedot", "Sabovedot",
              "sabovedot", "Tabovedot", "tabovedot", "Wgrave",
              "wgrave", "Wacute", "wacute", "Wdiaeresis",
              "wdiaeresis", "Ygrave", "ygrave", "OE", "oe",
              "Ydiaeresis", "overline"]
