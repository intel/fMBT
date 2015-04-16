# fMBT, free Model Based Testing tool
# Copyright (c) 2013-2014, Intel Corporation.
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

# fMBT GUI Test Interface (fmbtgti) provides a set of classes that
# implement a GUI testing interface with a rich collection of
# convenience methods and visual logging capabilities.
#
# GUI Test Interface does not implement a connection to any particular
# GUI technology, such as Android or X11. Platforms are wired up as
# separate GUITestConnection implementations that are given to
# GUITestInterface with the setConnection method. GUI Test Interface
# classes and wiring up required methods to the technology.
"""This module provides common functionality for all GUITestInterfaces
(like fmbtandroid.Device, fmbttizen.Device, fmbtx11.Screen,
fmbtvnc.Screen).

Bitmap matching (Optical Image Recognition, OIR)
------------------------------------------------

Bitmaps are searched from the directories listed in bitmapPath.

If a bitmap is found in a directory, default OIR parameters for
matching the bitmap are loaded from .fmbtoirrc file in the directory.

If a bitmap is not found in a directory, but .fmbtoirrc in the
directory contains lines like

  includedir = alt-directory

then the bitmap file is searched from alt-directory, too. If found
from there, OIR parameters defined in .fmbtoirrc below the includedir
line will be used for matching alt-directory/bitmap.

There can be several includedir lines, and many alternative sets of
OIR parameters can be given for each includedir. Sets are separated by
"alternative" line in the file.

Example:

Assume that bitmaps/android-4.2/device-A contains bitmaps captured
from the screen of device A.

Assume device B has higher resolution so that bitmaps of A have to be
scaled up by factor 1.3 or 1.2 - depending on bitmap - to match device
B. This can be handled by creating bitmaps/android-4.2/device-B
directory with .fmbtoirrc file that contains:

# OIR parameters for bitmaps in device-B in case some bitmaps will be
# created directly from device-B screenshots.
colorMatch = 0.9

# Two alternative parameter sets for bitmaps in device-A
includedir = ../device-A
scale = 1.3
colorMatch = 0.9
bitmapPixelSize = 3
screenshotPixelSize = 3

alternative
scale = 1.2
colorMatch = 0.8
bitmapPixelSize = 3
bitmapPixelSize = 3

After that, device B can be tested without taking new screenshot.

d = fmbtandroid.Device()
d.setBitmapPath("bitmaps/android-4.2/device-B")


All bitmap methods support alternative bitmaps. For example, if

    verifyBitmap("bitmap.png")

finds bitmap.png file in directory bitmapdir in the bitmap path, but
bitmap.png cannot be found in the screenshot with any given match
parameters, then it automatically tries the same for all

    bitmap.png.alt*.png

files in the same bitmapdir directory. If any of those match, then
verifyBitmap("bitmap.png") returns True. Visual log shows the
information about which of the alternatives actually matched.
"""

import cgi
import ctypes
import datetime
import distutils.sysconfig
import gc
import glob
import inspect
import math
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import traceback
import types

import fmbt
import fmbt_config
import eyenfinger

# See imagemagick convert parameters.
_OCRPREPROCESS = [
    ''
]

# See tesseract -pagesegmode.
_OCRPAGESEGMODES = [3]

_g_defaultOcrEngine = None # optical character recognition engine
_g_defaultOirEngine = None # optical image recognition engine
_g_ocrEngines = []
_g_oirEngines = []

_g_forcedLocExt = ".fmbtoir.loc"

class _USE_DEFAULTS:
    pass

class fmbtlogger():
    def write(self,msg):
        fmbt.fmbtlograw(msg)
    def flush(self):
        pass

def _fmbtLog(msg):
    fmbt.fmbtlog("fmbtgti: %s" % (msg,))

def _filenameTimestamp(t=None):
    return fmbt.formatTime("%Y%m%d-%H%M%S-%f", t)

def _takeDragArgs(d):
    return _takeArgs(("startOffset", "startPos",
                      "delayBeforeMoves", "delayBetweenMoves",
                      "delayAfterMoves", "movePoints"), d)

def _takeTapArgs(d):
    return _takeArgs(("tapOffset", "tapPos", "long", "hold", "count", "delayBetweenTaps", "button"), d)

def _takeWaitArgs(d):
    return _takeArgs(("waitTime", "pollDelay",
                      "beforeRefresh", "afterRefresh"), d)

def _takeOirArgs(screenshotOrOirEngine, d, thatsAll=False):
    if isinstance(screenshotOrOirEngine, Screenshot):
        oirEngine = screenshotOrOirEngine.oirEngine()
    else:
        oirEngine = screenshotOrOirEngine
    return _takeArgs(oirEngine._findBitmapArgNames(), d, thatsAll)

def _takeOcrArgs(screenshotOrOcrEngine, d, thatsAll=False):
    if isinstance(screenshotOrOcrEngine, Screenshot):
        ocrEngine = screenshotOrOcrEngine.ocrEngine()
    else:
        ocrEngine = screenshotOrOcrEngine
    return _takeArgs(ocrEngine._findTextArgNames(), d, thatsAll)

def _takeArgs(argNames, d, thatsAll=False):
    """
    Returns pair:
        (dict of items where key in argNames,
         dict of items that were left in d)

    If thatsAll is True, require that all arguments have been
    consumed.
    """
    retval = {}
    for a in argNames:
        if a in d:
            retval[a] = d.pop(a, None)
    if thatsAll and len(d) > 0:
        raise TypeError('Unknown argument(s): "%s"' %
                        ('", "'.join(sorted(d.keys()))))
    return retval, d

def _convert(srcFile, convertArgs, dstFile):
    if isinstance(convertArgs, basestring):
        convertArgs = shlex.split(convertArgs)
    if (os.access(dstFile, os.R_OK) and
        os.stat(srcFile).st_mtime < os.stat(dstFile).st_mtime):
        return # cached file is up-to-date
    subprocess.call([fmbt_config.imagemagick_convert, srcFile] + convertArgs + [dstFile])

def _ppFilename(origFilename, preprocess):
    return origFilename + ".fmbtoir.cache." + re.sub("[^a-zA-Z0-9.]", "", preprocess) + ".png"

def _intCoords((x, y), (width, height)):
    if 0 <= x <= 1 and type(x) == float: x = x * width
    if 0 <= y <= 1 and type(y) == float: y = y * height
    return (int(round(x)), int(round(y)))

def _boxOnRegion((x1, y1, x2, y2), (minX, minY, maxX, maxY)):
    return (x1 < x2 and ((minX <= x1 <= maxX) or (minX <= x2 <= maxX)) and
            y1 < y2 and ((minY <= y1 <= maxY) or (minY <= y2 <= maxY)))

def _edgeDistanceInDirection((x, y), (width, height), direction):
    x, y = _intCoords((x, y), (width, height))

    direction = direction % 360 # -90 => 270, 765 => 45

    dirRad = math.radians(direction)

    if 0 < direction < 180:
        distTopBottom = y / math.sin(dirRad)
    elif 180 < direction < 360:
        distTopBottom = -(height - y) / math.sin(dirRad)
    else:
        distTopBottom = float('inf')

    if 90 < direction < 270:
        distLeftRight = -x / math.cos(dirRad)
    elif 270 < direction <= 360 or 0 <= direction < 90:
        distLeftRight = (width - x) / math.cos(dirRad)
    else:
        distLeftRight = float('inf')

    return min(distTopBottom, distLeftRight)

### Binding to eye4graphics C-library
class _Bbox(ctypes.Structure):
    _fields_ = [("left", ctypes.c_int32),
                ("top", ctypes.c_int32),
                ("right", ctypes.c_int32),
                ("bottom", ctypes.c_int32),
                ("error", ctypes.c_int32)]

_libpath = ["", ".",
            os.path.dirname(os.path.abspath(__file__)),
            distutils.sysconfig.get_python_lib(plat_specific=1)]
_suffix = ".so"
if os.name == "nt":
    _suffix = ".dll"
for _dirname in _libpath:
    try:
        eye4graphics = ctypes.CDLL(os.path.join(_dirname , "eye4graphics"+_suffix))
        struct_bbox = _Bbox(0, 0, 0, 0, 0)
        eye4graphics.findNextHighErrorBlock.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_double,
            ctypes.c_void_p]
        eye4graphics.openImage.restype = ctypes.c_void_p
        eye4graphics.closeImage.argtypes = [ctypes.c_void_p]
        break
    except: pass
else:
    raise ImportError("%s cannot load eye4graphics%s" % (__file__, _suffix))

def _e4gOpenImage(filename):
    image = eye4graphics.openImage(filename)
    if not image:
        raise IOError('Cannot open image "%s"' % (filename,))
    else:
        return image

def _e4gImageDimensions(e4gImage):
    struct_bbox = _Bbox(0, 0, 0, 0, 0)
    eye4graphics.openedImageDimensions(ctypes.byref(struct_bbox), e4gImage)
    return (struct_bbox.right, struct_bbox.bottom)

def _e4gImageIsBlank(filename):
    e4gImage = _e4gOpenImage(filename)
    rv = (eye4graphics.openedImageIsBlank(e4gImage) == 1)
    eye4graphics.closeImage(e4gImage)
    return rv
### end of binding to eye4graphics.so

class GUITestConnection(object):
    """
    Implements GUI testing primitives needed by GUITestInterface.

    All send* and recv* methods return
    - True on success
    - False on user error (unknown keyName, coordinates out of range)
    - raise Exception on framework error (connection lost, missing
      dependencies).
    """
    def sendPress(self, keyName):
        return self.sendKeyDown(keyName) and self.sendKeyUp(keyName)
    def sendKeyDown(self, keyName):
        raise NotImplementedError('sendKeyDown("%s") needed but not implemented.' % (keyName,))
    def sendKeyUp(self, keyName):
        raise NotImplementedError('sendKeyUp("%s") needed but not implemented.' % (keyName,))
    def sendTap(self, x, y):
        return self.sendTouchDown(x, y) and self.sendTouchUp(x, y)
    def sendTouchDown(self, x, y):
        raise NotImplementedError('sendTouchDown(%d, %d) needed but not implemented.' % (x, y))
    def sendTouchMove(self, x, y):
        raise NotImplementedError('sendTouchMove(%d, %d) needed but not implemented.' % (x, y))
    def sendTouchUp(self, x, y):
        raise NotImplementedError('sendTouchUp(%d, %d) needed but not implemented.' % (x, y))
    def sendType(self, text):
        raise NotImplementedError('sendType("%s") needed but not implemented.' % (text,))
    def recvScreenshot(self, filename):
        """
        Saves screenshot from the GUI under test to given filename.
        """
        raise NotImplementedError('recvScreenshot("%s") needed but not implemented.' % (filename,))
    def recvScreenUpdated(self, waitTime, pollDelay):
        """
        Wait until the screen has been updated, but no longer than the
        timeout (waitTime). Return True if the screen was updated
        before the timeout, otherwise False.

        Implementing this method is optional. If not implemented, the
        method returns None, and an inefficient recvScreenshot-based
        implementation is used instead from fmbtgti. pollDelay can be
        ignored if more efficient solutions are available
        (update-event based triggering, for instance).
        """
        return None
    def target(self):
        """
        Returns a string that is unique to each test target. For
        instance, Android device serial number.
        """
        return "GUITestConnectionTarget"

class SimulatedGUITestConnection(GUITestConnection):
    """
    Simulates GUITestConnection: records method calls and fakes screenshots

    All send* methods return True. recvScreenshot returns always True
    if non-empty list of fake screenshot filenames is given (see
    constructor and setScreenshotFilenames). Otherwise it returns
    False.
    """
    def __init__(self, screenshotFilenames=()):
        """
        Parameters:

          screenshotFilenames (tuple of filenames):
                  calling recvScreenshot uses next item in this tuple as
                  the observed screenshot.
        """
        GUITestConnection.__init__(self)
        self.setScreenshotFilenames(screenshotFilenames)
        self._calls = []

        for recordedMethod in ("sendPress", "sendKeyDown", "sendKeyUp",
                               "sendTap", "sendTouchDown", "sendTouchMove",
                               "sendTouchUp", "sendType"):
            self.__dict__[recordedMethod] = self._recorder(recordedMethod)

    def _recorder(self, method):
        return lambda *args, **kwargs: self._calls.append(
            (time.time(), method, args, kwargs)) or True

    def history(self):
        return self._calls

    def clearHistory(self):
        self._calls = []

    def setScreenshotFilenames(self, screenshotFilenames):
        self._screenshotFilenames = screenshotFilenames
        self._nextScreenshotFilename = 0

    def recvScreenshot(self, filename):
        self._calls.append((time.time(), "recvScreenshot", (filename,), {}))
        if self._screenshotFilenames:
            if self._nextScreenshotFilename >= len(self._screenshotFilenames):
                self._nextScreenshotFilename = 0
            fakeFilename = self._screenshotFilenames[self._nextScreenshotFilename]
            self._nextScreenshotFilename += 1
            if not os.access(fakeFilename, os.R_OK):
                raise IOError('screenshot file not found: "%s"' % (fakeFilename,))
            shutil.copy(fakeFilename, filename)
            return True
        else:
            return False

    def target(self):
        return "SimulatedGUITestConnection"

class OrEngine(object):
    """
    Optical recognition engine. Base class for OCR and OIR engines,
    enables registering engine instances.
    """
    def __init__(self, *args, **kwargs):
        pass

    def register(self, defaultOcr=False, defaultOir=False):
        """
        Register this engine instance to the list of OCR and/or OIR
        engines.

        Parameters:

          defaultOcr (optional, boolean):
                  if True, use this OCR engine by default in all new
                  GUITestInterface instances. The default is False.

          defaultOir (optional, boolean):
                  if True, use this OIR engine by default in all new
                  GUITestInterface instances. The default is False.

        Returns the index with which the engine was registered to the
        list of OCR or OIR engines. If this instance implements both
        OCR and OIR engines, returns pair (OCR index, OIR index).
        """
        # Allow a single engine implement both OCR and OIR engine
        # interfaces. Therefore, it must be possible to call
        # e.register(defaultOcr=True, defaultOir=True).
        #
        global _g_defaultOcrEngine, _g_defaultOirEngine
        global _g_ocrEngines, _g_oirEngines

        engineIndexes = []

        if isinstance(self, OcrEngine):
            if not self in _g_ocrEngines:
                _g_ocrEngines.append(self)
            engineIndexes.append(_g_ocrEngines.index(self))
            if defaultOcr:
                _g_defaultOcrEngine = self

        if isinstance(self, OirEngine):
            if not self in _g_oirEngines:
                _g_oirEngines.append(self)
            engineIndexes.append(_g_oirEngines.index(self))
            if defaultOir:
                _g_defaultOirEngine = self

        if len(engineIndexes) == 1:
            return engineIndexes[0]
        else:
            return engineIndexes

class OcrEngine(OrEngine):
    """
    This is an abstract interface for OCR engines that can be plugged
    into fmbtgti.GUITestInterface instances and Screenshots.

    To implement an OCR engine, you need to override _findText() at
    minimum. See _findText documentation in this class for
    requirements.

    If possible in your OCR engine, you can provide _dumpOcr() to
    reveal what is recognized in screenshots.

    For efficient caching of results and freeing cached results, you
    can override _addScreenshot() and _removeScreenshot(). Every
    screenshot is added before findText() or dumpOcr().

    A typical usage of OcrEngine instance:
    - oe.addScreenshot(ss)
    - oe.findText(ss, text1, <engine/screenshot/find-specific-args>)
    - oe.findText(ss, text2, <engine/screenshot/find-specific-args>)
    - oe.removeScreenshot(ss)

    Note that there may be several screenshots added before they are
    removed.
    """
    def __init__(self, *args, **kwargs):
        super(OcrEngine, self).__init__(*args, **kwargs)
        self._ssFindTextDefaults = {}
        self._findTextDefaults = {}
        ocrFindArgs, _ = _takeOcrArgs(self, kwargs)
        self._setFindTextDefaults(ocrFindArgs)

    def dumpOcr(self, screenshot, **kwargs):
        """
        Returns what is recognized in the screenshot. For debugging
        purposes.
        """
        ocrArgs = self.__ocrArgs(screenshot, **kwargs)
        return self._dumpOcr(screenshot, **ocrArgs)

    def _dumpOcr(self, screenshot, **kwargs):
        return None

    def addScreenshot(self, screenshot, **findTextDefaults):
        """
        Prepare for finding text from the screenshot.

        Parameters:

          screenshot (fmbtgti.Screenshot)
                  screenshot object to be searched from.

          other parameters (optional)
                  findText defaults for this screenshot.

        Notice that there may be many screenshots simultaneously.
        Do not keep reference to the screenshot object.
        """
        self.setScreenshotFindTextDefaults(screenshot, **findTextDefaults)
        return self._addScreenshot(screenshot, **findTextDefaults)

    def _addScreenshot(self, screenshot, **findTextDefaults):
        pass

    def removeScreenshot(self, screenshot):
        """
        OCR queries on the screenshot will not be made anymore.
        """
        self._removeScreenshot(screenshot)
        try:
            del self._ssFindTextDefaults[id(screenshot)]
        except KeyError:
            raise KeyError('screenshot "%s" does not have findTextDefaults. '
                           'If OcrEngine.addScreenshot() is overridden, it '
                           '*must* call parent\'s addScreenshot.' % (screenshot.filename(),))

    def _removeScreenshot(self, screenshot):
        pass

    def setFindTextDefaults(self, **findTextDefaults):
        return self._setFindTextDefaults(findTextDefaults, screenshot=None)

    def setScreenshotFindTextDefaults(self, screenshot, **findTextDefaults):
        return self._setFindTextDefaults(findTextDefaults, screenshot=screenshot)

    def _setFindTextDefaults(self, defaults, screenshot=None):
        """
        Set default values for optional arguments for findText().

        Parameters:

          defaults (dictionary)
                  Default keyword arguments and their values.

          screenshot (optional, fmbtgti.Screenshot instance)
                  Use the defaults for findText on this screenshot. If
                  the defaults are None, make them default for all
                  screenshots. Screenshot-specific defaults override
                  engine default.
        """
        if screenshot == None:
            self._findTextDefaults.update(defaults)
        else:
            ssid = id(screenshot)
            if not ssid in self._ssFindTextDefaults:
                self._ssFindTextDefaults[ssid] = self._findTextDefaults.copy()
            self._ssFindTextDefaults[ssid].update(defaults)

    def findTextDefaults(self, screenshot=None):
        if screenshot == None:
            return self._findTextDefaults
        elif id(screenshot) in self._ssFindTextDefaults:
            return self._ssFindTextDefaults[id(screenshot)]
        else:
            return None

    def _findTextArgNames(self):
        """
        Returns names of optional findText arguments.
        """
        return inspect.getargspec(self._findText).args[3:]

    def __ocrArgs(self, screenshot, **priorityArgs):
        ocrArgs = {}
        ocrArgs.update(self._findTextDefaults)
        ssId = id(screenshot)
        if ssId in self._ssFindTextDefaults:
            ocrArgs.update(self._ssFindTextDefaults[ssId])
        ocrArgs.update(priorityArgs)
        return ocrArgs

    def findText(self, screenshot, text, **kwargs):
        """
        Return list of fmbtgti.GUIItems that match to text.
        """
        ocrArgs = self.__ocrArgs(screenshot, **kwargs)
        return self._findText(screenshot, text, **ocrArgs)

    def _findText(self, screenshot, text, **kwargs):
        """
        Find appearances of text from the screenshot.

        Parameters:

          screenshot (fmbtgti.Screenshot)
                  Screenshot from which text is to be searched
                  for. Use Screenshot.filename() to get the filename.

          text (string)
                  text to be searched for.

          other arguments (engine specific)
                  kwargs contain keyword arguments given to
                  findText(screenshot, text, ...), already extended
                  first with screenshot-specific findTextDefaults, then
                  with engine-specific findTextDefaults.

                  _findText *must* define all engine parameters as
                  explicit keyword arguments:

                  def _findText(self, screenshot, text, engArg1=42):
                      ...

        Return list of fmbtgti.GUIItems.
        """
        raise NotImplementedError("_findText needed but not implemented.")


class _EyenfingerOcrEngine(OcrEngine):
    """
    OCR engine parameters that can be used in all
    ...OcrText() methods (swipeOcrText, tapOcrText, findItemsByOcrText, ...):

      match (float, optional):
              minimum match score in range [0.0, 1.0].  The default is
              1.0 (exact match).

      area ((left, top, right, bottom), optional):
              search from the given area only. Left, top, right and
              bottom are either absolute coordinates (integers) or
              floats in range [0.0, 1.0]. In the latter case they are
              scaled to screenshot dimensions. The default is (0.0,
              0.0, 1.0, 1.0), that is, search everywhere in the
              screenshot.

      lang (string, optional):
              pass given language option to Tesseract. See supported
              LANGUAGES (-l) in Tesseract documentation. The default
              is "eng" (English).

      pagesegmodes (list of integers, optional):
              try all integers as tesseract -pagesegmode
              arguments. The default is [3], another good option could
              be [3, 6].

      preprocess (string, optional):
              preprocess filter to be used in OCR for better
              result. Refer to eyenfinger.autoconfigure to search for
              a good one, or try with ImageMagick's convert:
              $ convert screenshot.png <preprocess> screenshot-pp.png
              $ tesseract screenshot-pp.png stdout

      configfile (string, optional):
              Tesseract configuration file.


    Example: limit recognized characters to hexadecimals by creating file
    "hexchars" with content

        tessedit_char_whitelist 0123456789abcdefABCDEF

    To use this file in a single run, pass it to any Ocr method:

        dut.verifyOcrText("DEADBEEF", configfile="hexchars")

    or to use it on every Ocr method, set it as a default:

        dut.ocrEngine().setFindTextDefaults(configfile="hexchars")
    """
    class _OcrResults(object):
        __slots__ = ("filename", "screenSize", "pagesegmodes", "preprocess", "area", "words", "lang", "configfile")
        def __init__(self, filename, screenSize):
            self.filename = filename
            self.screenSize = screenSize
            self.pagesegmodes = None
            self.preprocess = None
            self.area = None
            self.words = None
            self.lang = None
            self.configfile = None

    def __init__(self, *args, **engineDefaults):
        engineDefaults["area"] = engineDefaults.get("area", (0.0, 0.0, 1.0, 1.0))
        engineDefaults["lang"] = engineDefaults.get("lang", "eng")
        engineDefaults["match"] = engineDefaults.get("match", 1.0)
        engineDefaults["pagesegmodes"] = engineDefaults.get("pagesegmodes", _OCRPAGESEGMODES)
        engineDefaults["preprocess"] = engineDefaults.get("preprocess", _OCRPREPROCESS)
        engineDefaults["configfile"] = engineDefaults.get("configfile", None)
        super(_EyenfingerOcrEngine, self).__init__(*args, **engineDefaults)
        self._ss = {} # OCR results for screenshots

    def _addScreenshot(self, screenshot, **findTextDefaults):
        ssId = id(screenshot)
        self._ss[ssId] = _EyenfingerOcrEngine._OcrResults(screenshot.filename(), screenshot.size())

    def _removeScreenshot(self, screenshot):
        ssId = id(screenshot)
        if ssId in self._ss:
            del self._ss[ssId]

    def _findText(self, screenshot, text, match=None, preprocess=None, area=None, pagesegmodes=None, lang=None, configfile=None):
        ssId = id(screenshot)
        self._assumeOcrResults(screenshot, preprocess, area, pagesegmodes, lang, configfile)

        for ppfilter in self._ss[ssId].words.keys():
            try:
                score_text_bbox_list = eyenfinger.findText(
                    text, self._ss[ssId].words[ppfilter], match=match)
                if not score_text_bbox_list:
                    continue
                else:
                    break
            except eyenfinger.BadMatch:
                continue
        else:
            return []
        retval = [GUIItem("OCR text (match %.2f)" % (score,),
                          bbox, self._ss[ssId].filename,
                          ocrFind=text, ocrFound=matching_text)
                  for score, matching_text, bbox in score_text_bbox_list]
        return retval

    def _dumpOcr(self, screenshot, match=None, preprocess=None, area=None, pagesegmodes=None, lang=None, configfile=None):
        ssId = id(screenshot)
        self._assumeOcrResults(screenshot, preprocess, area, pagesegmodes, lang, configfile)
        w = []
        for ppfilter in self._ss[ssId].preprocess:
            for word in self._ss[ssId].words[ppfilter]:
                for appearance, (wid, middle, bbox) in enumerate(self._ss[ssId].words[ppfilter][word]):
                    (x1, y1, x2, y2) = bbox
                    w.append((word, (x1, y1, x2, y2)))
        return sorted(set(w), key=lambda i:(i[1][1]/8, i[1][0]))

    def _assumeOcrResults(self, screenshot, preprocess, area, pagesegmodes, lang, configfile):
        ssId = id(screenshot)
        if not type(preprocess) in (list, tuple):
            preprocess = [preprocess]

        if (self._ss[ssId].words == None
            or self._ss[ssId].preprocess != preprocess
            or self._ss[ssId].area != area
            or self._ss[ssId].lang != lang
            or self._ss[ssId].configfile != configfile):
            self._ss[ssId].words = {}
            self._ss[ssId].preprocess = preprocess
            self._ss[ssId].area = area
            self._ss[ssId].lang = lang
            self._ss[ssId].configfile = configfile
            for ppfilter in preprocess:
                pp = ppfilter % { "zoom": "-resize %sx" % (self._ss[ssId].screenSize[0] * 2) }
                try:
                    eyenfinger.iRead(source=self._ss[ssId].filename, ocr=True, preprocess=pp, ocrArea=area, ocrPageSegModes=pagesegmodes, lang=lang, configfile=configfile)
                except Exception:
                    self._ss[ssId].words = None
                    raise
                self._ss[ssId].words[ppfilter] = eyenfinger._g_words

def _defaultOcrEngine():
    if _g_defaultOcrEngine:
        return _g_defaultOcrEngine
    else:
        _EyenfingerOcrEngine().register(defaultOcr=True)
        return _g_defaultOcrEngine

class OirEngine(OrEngine):
    """
    This is an abstract interface for OIR (optical image recognition)
    engines that can be plugged into fmbtgti.GUITestInterface
    instances and Screenshots.

    To implement an OIR engine, you need to override _findBitmap() at
    minimum. See _findBitmap documentation in this class for
    requirements.

    This base class provides full set of OIR parameters to
    _findBitmap. The parameters are combined from

    - OirEngine find defaults, specified when OirEngine is
      instantiated.

    - Screenshot instance find defaults.

    - bitmap / bitmap directory find defaults (read from the
      .fmbtoirrc that is in the same directory as the bitmap).

    - ...Bitmap() method parameters.

    The latter in the list override the former.


    For efficient caching of results and freeing cached results, you
    can override _addScreenshot() and _removeScreenshot(). Every
    screenshot is added before findBitmap().

    A typical usage of OirEngine instance:
    - oe.addScreenshot(ss)
    - oe.findBitmap(ss, bmpFilename1, <engine/screenshot/find-specific-args>)
    - oe.findBitmap(ss, bmpFilename2, <engine/screenshot/find-specific-args>)
    - oe.removeScreenshot(ss)

    Note that there may be several screenshots added before they are
    removed. ss is a Screenshot instance. Do not keep references to
    Screenshot intances, otherwise garbage collector will not remove
    them.
    """
    def __init__(self, *args, **kwargs):
        super(OirEngine, self).__init__(*args, **kwargs)
        self._ssFindBitmapDefaults = {}
        self._findBitmapDefaults = {}
        oirArgs, _ = _takeOirArgs(self, kwargs)
        self._setFindBitmapDefaults(oirArgs)

    def addScreenshot(self, screenshot, **findBitmapDefaults):
        """
        Prepare for finding bitmap from the screenshot.

        Parameters:

          screenshot (fmbtgti.Screenshot)
                  screenshot object to be searched from.

          other parameters (optional)
                  findBitmap defaults for this screenshot.

        Notice that there may be many screenshots simultaneously.
        Do not keep reference to the screenshot object.
        """
        self.setScreenshotFindBitmapDefaults(screenshot, **findBitmapDefaults)
        return self._addScreenshot(screenshot, **findBitmapDefaults)

    def _addScreenshot(self, screenshot, **findBitmapDefaults):
        pass

    def removeScreenshot(self, screenshot):
        """
        OIR queries on the screenshot will not be made anymore.
        """
        self._removeScreenshot(screenshot)
        try:
            del self._ssFindBitmapDefaults[id(screenshot)]
        except KeyError:
            raise KeyError('screenshot "%s" does not have findBitmapDefaults. '
                           'If OirEngine.addScreenshot() is overridden, it '
                           '*must* call parent\'s addScreenshot.' % (screenshot.filename(),))

    def _removeScreenshot(self, screenshot):
        pass

    def setFindBitmapDefaults(self, **findBitmapDefaults):
        return self._setFindBitmapDefaults(findBitmapDefaults, screenshot=None)

    def setScreenshotFindBitmapDefaults(self, screenshot, **findBitmapDefaults):
        return self._setFindBitmapDefaults(findBitmapDefaults, screenshot=screenshot)

    def _setFindBitmapDefaults(self, defaults, screenshot=None):
        """
        Set default values for optional arguments for findBitmap().

        Parameters:

          defaults (dictionary)
                  Default keyword arguments and their values.

          screenshot (optional, fmbtgti.Screenshot instance)
                  Use the defaults for findBitmap on this screenshot. If
                  the defaults are None, make them default for all
                  screenshots. Screenshot-specific defaults override
                  engine default.
        """
        if screenshot == None:
            self._findBitmapDefaults.update(defaults)
        else:
            ssid = id(screenshot)
            if not ssid in self._ssFindBitmapDefaults:
                self._ssFindBitmapDefaults[ssid] = self._findBitmapDefaults.copy()
            self._ssFindBitmapDefaults[ssid].update(defaults)

    def findBitmapDefaults(self, screenshot=None):
        if screenshot == None:
            return self._findBitmapDefaults
        elif id(screenshot) in self._ssFindBitmapDefaults:
            return self._ssFindBitmapDefaults[id(screenshot)]
        else:
            return None

    def _findBitmapArgNames(self):
        """
        Returns names of optional findBitmap arguments.
        """
        return inspect.getargspec(self._findBitmap).args[3:]

    def __oirArgs(self, screenshot, bitmap, **priorityArgs):
        oirArgs = {}
        oirArgs.update(self._findBitmapDefaults)
        ssId = id(screenshot)
        if ssId in self._ssFindBitmapDefaults:
            oirArgs.update(self._ssFindBitmapDefaults[ssId])
        oirArgs.update(priorityArgs)
        return oirArgs

    def findBitmap(self, screenshot, bitmap, **kwargs):
        """
        Return list of fmbtgti.GUIItems that match to bitmap.
        """
        oirArgs = self.__oirArgs(screenshot, bitmap, **kwargs)
        bitmapLocsFilename = bitmap + _g_forcedLocExt
        if os.access(bitmapLocsFilename, os.R_OK):
            # Use hardcoded bitmap locations file instead of real OIR
            # bitmap.png.locs file format:
            # [(x11, y11, x12, y12), ..., (xn1, yn1, xn2, yn2)]
            try:
                bboxList = eval(file(bitmapLocsFilename).read().strip())
                foundItems = []
                for (left, top, right, bottom) in bboxList:
                    x1, y1 = _intCoords((left, top), screenshot.size())
                    x2, y2 = _intCoords((right, bottom), screenshot.size())
                    foundItems.append(
                        GUIItem("bitmap location", (x1, y1, x2, y2),
                                screenshot.filename(), bitmap=bitmapLocsFilename))
                return foundItems
            except Exception, e:
                raise ValueError('Error reading bounding box list from %s: %s' %
                                 repr(bitmapLocsFilename), e)
        return self._findBitmap(screenshot, bitmap, **oirArgs)

    def _findBitmap(self, screenshot, bitmap, **kwargs):
        """
        Find appearances of bitmap from the screenshot.

        Parameters:

          screenshot (fmbtgti.Screenshot)
                  Screenshot from which bitmap is to be searched
                  for. Use Screenshot.filename() to get the filename.

          bitmap (string)
                  bitmap to be searched for.

          other arguments (engine specific)
                  kwargs contain keyword arguments given to
                  findBitmap(screenshot, bitmap, ...), already extended
                  first with screenshot-specific findBitmapDefaults, then
                  with engine-specific findBitmapDefaults.

                  _findBitmap *must* define all engine parameters as
                  explicit keyword arguments:

                  def _findBitmap(self, screenshot, bitmap, engArg1=42):
                      ...

        Returns list of fmbtgti.GUIItems.
        """
        raise NotImplementedError("_findBitmap needed but not implemented.")


class _Eye4GraphicsOirEngine(OirEngine):
    """OIR engine parameters that can be used in all
    ...Bitmap() methods (swipeBitmap, tapBitmap, findItemsByBitmap, ...):

      colorMatch (float, optional):
              required color matching accuracy. The default is 1.0
              (exact match). For instance, 0.75 requires that every
              pixel's every RGB component value on the bitmap is at
              least 75 % match with the value of corresponding pixel's
              RGB component in the screenshot.

      opacityLimit (float, optional):
              threshold for comparing pixels with non-zero alpha
              channel. Pixels less opaque than the given threshold are
              skipped in match comparison. The default is 0, that is,
              alpha channel is ignored.

      area ((left, top, right, bottom), optional):
              search bitmap from the given area only. Left, top right
              and bottom are either absolute coordinates (integers) or
              floats in range [0.0, 1.0]. In the latter case they are
              scaled to screenshot dimensions. The default is (0.0,
              0.0, 1.0, 1.0), that is, search everywhere in the
              screenshot.

      limit (integer, optional):
              number of returned matches is limited to the limit. The
              default is -1: all matches are returned. Applicable in
              findItemsByBitmap.

      allowOverlap (boolean, optional):
              allow returned icons to overlap. If False, returned list
              contains only non-overlapping bounding boxes. The
              default is False.

      scale (float or pair of floats, optional):
              scale to be applied to the bitmap before
              matching. Single float is a factor for both X and Y
              axis, pair of floats is (xScale, yScale). The default is
              1.0.

      bitmapPixelSize (integer, optional):
              size of pixel rectangle on bitmap for which there must
              be same color on corresponding screenshot rectangle.  If
              scale is 1.0, default is 1 (rectangle is 1x1). If scale
              != 1.0, the default is 2 (rectangle is 2x2).

      screenshotPixelSize (integer, optional):
              size of pixel rectangle on screenshot in which there
              must be a same color pixel as in the corresponding
              rectangle on bitmap. The default is scale *
              bitmapPixelSize.

      preprocess (string, optional):
              preprocess parameters that are executed to both screenshot
              and reference bitmap before running findBitmap. By default
              there is no preprocessing.
              Example: d.verifyBitmap("ref.png", preprocess="-threshold 60%")
              will execute two imagemagick commands:
                1. convert screenshot.png -threshold 60% screenshot-pp.png
                2. convert ref.png -threshold 60% ref-pp.png
              and then search for ref-pp.png in screenshot-pp.png. This results
              in black-and-white comparison (immune to slight color changes).

    If unsure about parameters, but you have a bitmap that should be
    detected in a screenshot, try obj.oirEngine().adjustParameters().

    Example:

    d.enableVisualLog("params.html")
    screenshot = d.refreshScreenshot()
    results = d.oirEngine().adjustParameters(screenshot, "mybitmap.png")
    if results:
        item, params = results[0]
        print "found %s with parameters:" % (item,)
        print "\n".join(sorted(["  %s = %s" % (k, params[k]) for k in params]))
        print "verify:", d.verifyBitmap("mybitmap.png", **params)

    Notice, that you can force refreshScreenshot to load old screenshot:
    d.refreshScreenshot("old.png")
    """
    def __init__(self, *args, **engineDefaults):
        engineDefaults["colorMatch"] = engineDefaults.get("colorMatch", 1.0)
        engineDefaults["opacityLimit"] = engineDefaults.get("opacityLimit", 0.0)
        engineDefaults["area"] = engineDefaults.get("area", (0.0, 0.0, 1.0, 1.0))
        engineDefaults["limit"] = engineDefaults.get("limit", -1)
        engineDefaults["allowOverlap"] = engineDefaults.get("allowOverlap", False)
        engineDefaults["scale"] = engineDefaults.get("scale", 1.0)
        engineDefaults["bitmapPixelSize"] = engineDefaults.get("bitmapPixelSize", 0)
        engineDefaults["screenshotPixelSize"] = engineDefaults.get("screenshotPixelSize", 0)
        engineDefaults["preprocess"] = engineDefaults.get("preprocess", "")
        OirEngine.__init__(self, *args, **engineDefaults)
        self._openedImages = {}
        # openedRelatedScreenshots maps a screenshot filename to
        # a list of preprocessed screenshot objects. All those objects
        # must be closed when the screenshot is removed.
        self._openedRelatedScreenshots = {}
        self._findBitmapCache = {}

    def _addScreenshot(self, screenshot, **findBitmapDefaults):
        filename = screenshot.filename()
        self._openedImages[filename] = _e4gOpenImage(filename)
        # make sure size() is available, this can save an extra
        # opening of the screenshot file.
        if screenshot.size(allowReadingFile=False) == None:
            screenshot.setSize(_e4gImageDimensions(self._openedImages[filename]))
        self._findBitmapCache[filename] = {}

    def _removeScreenshot(self, screenshot):
        filename = screenshot.filename()
        if filename in self._openedRelatedScreenshots:
            for screenshotPP in self._openedRelatedScreenshots[filename]:
                self._removeScreenshot(screenshotPP)
            del self._openedRelatedScreenshots[filename]
        eye4graphics.closeImage(self._openedImages[filename])
        del self._openedImages[filename]
        del self._findBitmapCache[filename]

    def adjustParameters(self, screenshot, bitmap,
                         scaleRange = [p/100.0 for p in range(110,210,10)],
                         colorMatchRange = [p/100.0 for p in range(100,60,-10)],
                         pixelSizeRange = range(2,5),
                         resultCount = 1,
                         **oirArgs):
        """
        Search for scale, colorMatch, bitmapPixelSize and
        screenshotPixelSize parameters that find the bitmap in the
        screenshot.

        Parameters:
          screenshot (Screenshot instance):
                  screenshot that contains the bitmap.

          bitmap (string):
                  bitmap filename.

          scaleRange (list of floats, optional):
                  scales to go through.
                  The default is: 1.1, 1.2, ... 2.0.

          colorMatchRange (list of floats, optional):
                  colorMatches to try out.
                  The default is: 1.0, 0.9, ... 0.7.

          pixelSizeRange (list of integers, optional):
                  values for bitmapPixelSize and screenshotPixelSize.
                  The default is: [2, 3]

          resultCount (integer, optional):
                  number of parameter combinations to be found.
                  The default is 1. 0 is unlimited.

          other OIR parameters: as usual, refer to engine documentation.

        Returns list of pairs: (GUIItem, findParams), where
        GUIItem is the detected item (GUIItem.bbox() is the box around it),
        and findParams is a dictionary containing the parameters.
        """
        if not screenshot.filename() in self._findBitmapCache:
            self.addScreenshot(screenshot)
            ssAdded = True
        else:
            ssAdded = False
        retval = []
        for colorMatch in colorMatchRange:
            for pixelSize in pixelSizeRange:
                for scale in scaleRange:
                    findParams = oirArgs.copy()
                    findParams.update({"colorMatch": colorMatch,
                                       "limit": 1,
                                       "scale": scale,
                                       "bitmapPixelSize": pixelSize,
                                       "screenshotPixelSize": pixelSize})
                    results = self.findBitmap(screenshot, bitmap,
                                               **findParams)
                    if results:
                        retval.append((results[0], findParams))
                        if len(retval) == resultCount:
                            return retval
        if ssAdded:
            self.removeScreenshot(screenshot)
        return retval

    def _findBitmap(self, screenshot, bitmap, colorMatch=None,
                    opacityLimit=None, area=None, limit=None,
                    allowOverlap=None, scale=None,
                    bitmapPixelSize=None, screenshotPixelSize=None,
                    preprocess=None):
        """
        Find items on the screenshot that match to bitmap.
        """
        ssFilename = screenshot.filename()
        ssSize = screenshot.size()
        cacheKey = (bitmap, colorMatch, opacityLimit, area, limit,
                    scale, bitmapPixelSize, screenshotPixelSize, preprocess)
        if cacheKey in self._findBitmapCache[ssFilename]:
            return self._findBitmapCache[ssFilename][cacheKey]
        self._findBitmapCache[ssFilename][cacheKey] = []

        if preprocess:
            ssFilenamePP = _ppFilename(ssFilename, preprocess)
            bitmapPP = _ppFilename(bitmap, preprocess)
            if not ssFilenamePP in self._openedImages:
                _convert(ssFilename, preprocess, ssFilenamePP)
                screenshotPP = Screenshot(ssFilenamePP)
                self.addScreenshot(screenshotPP)
                if not ssFilename in self._openedRelatedScreenshots:
                    self._openedRelatedScreenshots[ssFilename] = []
                self._openedRelatedScreenshots[ssFilename].append(screenshotPP)
            _convert(bitmap, preprocess, bitmapPP)
            ssFilename = ssFilenamePP
            bitmap = bitmapPP
            self._findBitmapCache[ssFilename][cacheKey] = []

        e4gIcon = _e4gOpenImage(bitmap)
        matchCount = 0
        leftTopRightBottomZero = (_intCoords((area[0], area[1]), ssSize) +
                                  _intCoords((area[2], area[3]), ssSize) +
                                  (0,))
        struct_area_bbox = _Bbox(*leftTopRightBottomZero)
        struct_bbox = _Bbox(0, 0, 0, 0, 0)
        contOpts = 0 # search for the first hit
        try:
            xscale, yscale = scale
        except TypeError:
            xscale = yscale = float(scale)
        while True:
            if matchCount == limit: break
            result = eye4graphics.findNextIcon(
                ctypes.byref(struct_bbox),
                ctypes.c_void_p(self._openedImages[ssFilename]),
                ctypes.c_void_p(e4gIcon),
                0, # no fuzzy matching
                ctypes.c_double(colorMatch),
                ctypes.c_double(opacityLimit),
                ctypes.byref(struct_area_bbox),
                ctypes.c_int(contOpts),
                ctypes.c_float(xscale),
                ctypes.c_float(yscale),
                ctypes.c_int(bitmapPixelSize),
                ctypes.c_int(screenshotPixelSize))
            contOpts = 1 # search for the next hit
            if result < 0: break
            bbox = (int(struct_bbox.left), int(struct_bbox.top),
                    int(struct_bbox.right), int(struct_bbox.bottom))
            addToFoundItems = True
            if allowOverlap == False:
                for guiItem in self._findBitmapCache[ssFilename][cacheKey]:
                    itemLeft, itemTop, itemRight, itemBottom = guiItem.bbox()
                    if ((itemLeft <= bbox[0] <= itemRight or itemLeft <= bbox[2] <= itemRight) and
                        (itemTop <= bbox[1] <= itemBottom or itemTop <= bbox[3] <= itemBottom)):
                        if ((itemLeft < bbox[0] < itemRight or itemLeft < bbox[2] < itemRight) or
                            (itemTop < bbox[1] < itemBottom or itemTop < bbox[3] < itemBottom)):
                            addToFoundItems = False
                            break
            if addToFoundItems:
                self._findBitmapCache[ssFilename][cacheKey].append(
                    GUIItem("bitmap", bbox, ssFilename, bitmap=bitmap))
                matchCount += 1
        eye4graphics.closeImage(e4gIcon)
        return self._findBitmapCache[ssFilename][cacheKey]

def _defaultOirEngine():
    if _g_defaultOirEngine:
        return _g_defaultOirEngine
    else:
        _Eye4GraphicsOirEngine().register(defaultOir=True)
        return _g_defaultOirEngine


class _OirRc(object):
    """Optical image recognition settings for a directory.
    Currently loaded from file .fmbtoirc in the directory.
    There is once _OirRc instance per directory.
    """
    _filename = ".fmbtoirrc"
    _cache = {}

    @classmethod
    def load(cls, directory):
        if directory in cls._cache:
            pass
        elif os.access(os.path.join(directory, cls._filename), os.R_OK):
            cls._cache[directory] = cls(directory)
        else:
            cls._cache[directory] = None
        return cls._cache[directory]

    def __init__(self, directory):
        self._key2value = {}
        curdir = "."
        self._dir2oirArgsList = {curdir: [{}]}
        oirRcFilepath = os.path.join(directory, _OirRc._filename)
        for line in file(oirRcFilepath):
            line = line.strip()
            if line == "" or line[0] in "#;":
                continue
            elif line == "alternative":
                self._dir2oirArgsList[curdir].append({}) # new set of args
                self._key2value = {}
            elif "=" in line:
                key, value_str = line.split("=", 1)
                value_str = value_str.strip()
                if key.strip().lower() == "includedir":
                    curdir = value_str
                    self._dir2oirArgsList[curdir] = [{}]
                    if not os.access(curdir, os.X_OK):
                        _fmbtLog("warning: %s: inaccessible includedir %s" %
                                 (repr(oirRcFilepath), curdir))
                else:
                    try: value = int(value_str)
                    except ValueError:
                        try: value = float(value_str)
                        except ValueError:
                            if value_str[0] in "([\"'": # tuple, list, string
                                value = eval(value_str)
                            else:
                                value = value_str
                    self._dir2oirArgsList[curdir][-1][key.strip()] = value

    def searchDirs(self):
        return self._dir2oirArgsList.keys()

    def oirArgsList(self, searchDir):
        return self._dir2oirArgsList[searchDir]


class _Paths(object):
    def __init__(self, bitmapPath, relativeRoot):
        self.bitmapPath = bitmapPath
        self.relativeRoot = relativeRoot
        self._oirAL = {} # OIR parameters for bitmaps
        self._abspaths = {} # bitmap to abspaths

    def abspaths(self, bitmap, checkReadable=True):
        if bitmap in self._abspaths:
            return self._abspaths[bitmap]
        if bitmap.startswith("/"):
            path = [os.path.dirname(bitmap)]
            bitmap = os.path.basename(bitmap)
        else:
            path = []
            for singleDir in self.bitmapPath.split(":"):
                if singleDir and not singleDir.startswith("/"):
                    path.append(os.path.join(self.relativeRoot, singleDir))
                else:
                    path.append(singleDir)

        for singleDir in path:
            candidate = os.path.join(singleDir, bitmap)
            if not checkReadable or os.access(candidate, os.R_OK):
                oirRc = _OirRc.load(os.path.dirname(candidate))
                if oirRc:
                    self._oirAL[candidate] = oirRc.oirArgsList(".")
                else:
                    self._oirAL[candidate] = [{}]
                self._oirAL[bitmap] = self._oirAL[candidate]
                break
            else:
                # bitmap is not in singleDir, but there might be .fmbtoirrc
                oirRc = _OirRc.load(os.path.dirname(candidate))
                if oirRc:
                    for d in oirRc.searchDirs():
                        if d.startswith("/"):
                            candidate = os.path.join(d, os.path.basename(bitmap))
                        else:
                            candidate = os.path.join(os.path.dirname(candidate), d, os.path.basename(bitmap))
                        if os.access(candidate, os.R_OK):
                            self._oirAL[candidate] = oirRc.oirArgsList(d)
                            self._oirAL[bitmap] = self._oirAL[candidate]
                            break

        if checkReadable and not os.access(candidate, os.R_OK):
            raise ValueError('Bitmap "%s" not readable in bitmapPath %s' % (bitmap, ':'.join(path)))
        self._abspaths[bitmap] = [candidate]
        # check for alternative bitmaps
        try:
            candidate_ext = "." + candidate.rsplit(".", 1)[1]
        except IndexError:
            candidate_ext = ""
        alt_candidates = glob.glob(candidate + ".alt*" + candidate_ext)
        self._abspaths[bitmap].extend(alt_candidates)
        return self._abspaths[bitmap]

    def oirArgsList(self, bitmap):
        """Returns list of alternative OIR parameters associated to the bitmap
        by appropriate .fmbtoirrc file
        """
        if bitmap in self._oirAL:
            return self._oirAL[bitmap]
        else:
            absBitmap = self.abspaths(bitmap)[0]
            if absBitmap in self._oirAL:
                return self._oirAL[absBitmap]
            else:
                return None


class GUITestInterface(object):
    def __init__(self, ocrEngine=None, oirEngine=None, rotateScreenshot=None):
        self._paths = _Paths("", "")
        self._conn = None
        self._lastScreenshot = None
        self._longPressHoldTime = 2.0
        self._longTapHoldTime = 2.0
        self._ocrEngine = None
        self._oirEngine = None
        self._rotateScreenshot = rotateScreenshot
        self._screenshotLimit = None
        self._screenshotRefCount = {} # filename -> Screenshot object ref count
        self._screenshotArchiveMethod = "resize"

        if ocrEngine == None:
            self.setOcrEngine(_defaultOcrEngine())
        else:
            if type(ocrEngine) == int:
                self.setOcrEngine(_g_ocrEngines[ocrEngine])
            else:
                self.setOcrEngine(ocrEngine)

        if oirEngine == None:
            self.setOirEngine(_defaultOirEngine())
        else:
            if type(oirEngine) == int:
                self.setOirEngine(_g_oirEngines[oirEngine])
            else:
                self.setOirEngine(oirEngine)

        self._screenshotDir = None
        self._screenshotDirDefault = "screenshots"
        self._screenshotSubdir = None
        self._screenshotSubdirDefault = ""
        self._screenSize = None
        self._tapDefaults = {}
        self._visualLog = None
        self._visualLogFileObj = None
        self._visualLogFilenames = set()

    def bitmapPath(self):
        """
        Returns bitmapPath from which bitmaps are searched for.
        """
        return self._paths.bitmapPath

    def bitmapPathRoot(self):
        """
        Returns the path that prefixes all relative directories in
        bitmapPath.
        """
        return self._paths.relativeRoot

    def close(self):
        self._lastScreenshot = None
        if self._visualLog:
            if (hasattr(self._visualLog._outFileObj, "name") and
                self._visualLog._outFileObj.name in self._visualLogFilenames):
                self._visualLogFilenames.remove(self._visualLog._outFileObj.name)
            self._visualLog.close()
            if self._visualLogFileObj:
                self._visualLogFileObj.close()
            self._visualLog = None

    def connection(self):
        """
        Returns GUITestConnection instance or None if not available.

        See also existingConnection().
        """
        return self._conn

    def drag(self, (x1, y1), (x2, y2), delayBetweenMoves=0.01, delayBeforeMoves=0, delayAfterMoves=0, movePoints=20):
        """
        Touch the screen on coordinates (x1, y1), drag along straight
        line to coordinates (x2, y2), and raise fingertip.

        coordinates (floats in range [0.0, 1.0] or integers):
                floating point coordinates in range [0.0, 1.0] are
                scaled to full screen width and height, others are
                handled as absolute coordinate values.

        delayBeforeMoves (float, optional):
                seconds to wait after touching and before dragging.
                If negative, starting touch event is not sent.

        delayBetweenMoves (float, optional):
                seconds to wait when moving between points when
                dragging.

        delayAfterMoves (float, optional):
                seconds to wait after dragging, before raising
                fingertip.
                If negative, fingertip is not raised.

        movePoints (integer, optional):
                the number of intermediate move points between end
                points of the line.

        Returns True on success, False if sending input failed.
        """
        x1, y1 = self.intCoords((x1, y1))
        x2, y2 = self.intCoords((x2, y2))
        if delayBeforeMoves >= 0:
            if not self.existingConnection().sendTouchDown(x1, y1):
                return False
        if delayBeforeMoves > 0:
            time.sleep(delayBeforeMoves)
        else:
            time.sleep(delayBetweenMoves)
        for i in xrange(0, movePoints):
            nx = x1 + int(round(((x2 - x1) / float(movePoints+1)) * (i+1)))
            ny = y1 + int(round(((y2 - y1) / float(movePoints+1)) * (i+1)))
            if not self.existingConnection().sendTouchMove(nx, ny): return False
            time.sleep(delayBetweenMoves)
        if delayAfterMoves > 0:
            self.existingConnection().sendTouchMove(x2, y2)
            time.sleep(delayAfterMoves)
        if delayAfterMoves >= 0:
            if self.existingConnection().sendTouchUp(x2, y2):
                return True
            else:
                return False
        else:
            return True

    def enableVisualLog(self, filenameOrObj,
                        screenshotWidth="240", thumbnailWidth="",
                        timeFormat="%s.%f", delayedDrawing=False,
                        copyBitmapsToScreenshotDir=False):
        """
        Start writing visual HTML log on this device object.

        Parameters:

          filenameOrObj (string or a file object)
                  The file to which the log is written. Log can be
                  split into multiple html files by using strftime
                  conversion specifications in filenameOrObj. For
                  instance, "%a-%H.html" will log to "Thu-16.html" on
                  Thurday from 4 pm to 5 pm.

          screenshotWidth (string, optional)
                  Width of screenshot images in HTML.
                  The default is "240".

          thumbnailWidth (string, optional)
                  Width of thumbnail images in HTML.
                  The default is "", that is, original size.

          timeFormat (string, optional)
                  Timestamp format. The default is "%s.%f".
                  Refer to strftime documentation.

          delayedDrawing (boolean, optional)
                  If True, screenshots with highlighted icons, words
                  and gestures are not created during the
                  test. Instead, only shell commands are stored for
                  later execution. The value True can significantly
                  save test execution time and disk space. The default
                  is False.

          copyBitmapsToScreenshotDir (boolean, optional)
                  If True, every logged bitmap file will be copied to
                  bitmaps directory in screenshotDir. The default is
                  False.
        """
        if type(filenameOrObj) == str:
            try:
                outFileObj = file(filenameOrObj, "w")
                self._visualLogFileObj = outFileObj
            except Exception, e:
                _fmbtLog('Failed to open file "%s" for logging.' % (filenameOrObj,))
                raise
        else:
            outFileObj = filenameOrObj
            # someone else opened the file => someone else will close it
            self._visualLogFileObj = None
        if hasattr(outFileObj, "name"):
            if outFileObj.name in self._visualLogFilenames:
                raise ValueError('Visual logging on file "%s" is already enabled' % (outFileObj.name,))
            else:
                self._visualLogFilenames.add(outFileObj.name)
        self._visualLog = _VisualLog(self, outFileObj, screenshotWidth,
                                     thumbnailWidth, timeFormat, delayedDrawing,
                                     copyBitmapsToScreenshotDir)

    def existingConnection(self):
        """
        Returns GUITestConnection, raises ConnectionError if not available.

        See also connection()
        """
        if self._conn:
            return self._conn
        else:
            raise ConnectionError("not connected")

    def visualLog(self, *args):
        """Writes parameters to the visual log, given that visual logging is
        enabled.
        """
        pass

    def intCoords(self, (x, y)):
        """
        Convert floating point coordinate values in range [0.0, 1.0] to
        screen coordinates.
        """
        width, height = self.screenSize()
        return _intCoords((x, y), (width, height))

    def itemOnScreen(self, guiItem):
        """
        Returns True if bbox of guiItem is non-empty and at least
        partially on screen, otherwise False.
        """
        maxX, maxY = self.screenSize()
        return _boxOnRegion(guiItem.bbox(), (0, 0, maxX, maxY))

    def ocrEngine(self):
        """
        Returns the OCR engine that is used by default for new
        screenshots.
        """
        return self._ocrEngine

    def oirEngine(self):
        """
        Returns the OIR engine that is used by default for new
        screenshots.
        """
        return self._oirEngine

    def pressKey(self, keyName, long=False, hold=0.0, modifiers=None):
        """
        Press a key.

        Parameters:

          keyName (string):
                  the name of the key, like KEYCODE_HOME.

          long (boolean, optional):
                  if True, press the key for long time.

          hold (float, optional):
                  time in seconds to hold the key down.

          modifiers (list of strings, optional)
                  modifier key(s) to be pressed at the same time.
        """

        extraParams = {}
        if modifiers != None:
            extraParams['modifiers'] = modifiers
        if long and hold == 0.0:
            hold = self._longPressHoldTime
        if hold > 0.0:
            try:
                assert self.existingConnection().sendKeyDown(keyName, **extraParams)
                time.sleep(hold)
                assert self.existingConnection().sendKeyUp(keyName, **extraParams)
            except AssertionError:
                return False
            return True
        return self.existingConnection().sendPress(keyName, **extraParams)

    def _newScreenshotFilepath(self):
        """
        Returns path and filename for next screenshot file.
        Makes sure the file can be written (necessary directory
        structure exists).
        """
        t = datetime.datetime.now()
        if not self._conn:
            target = ""
        else:
            target = self._conn.target()
        filename = _filenameTimestamp(t) + "-" + target + ".png"
        screenshotPath = self.screenshotDir()
        if self.screenshotSubdir():
            screenshotPath = os.path.join(screenshotPath,
                                          self.screenshotSubdir())
        screenshotPath = fmbt.formatTime(screenshotPath, t)
        filepath = os.path.join(screenshotPath, filename)
        necessaryDirs = os.path.dirname(filepath)
        if necessaryDirs and not os.path.isdir(necessaryDirs):
            try:
                os.makedirs(necessaryDirs)
            except Exception, e:
                _fmbtLog('creating directory "%s" for screenshots failed: %s' %
                         (necessaryDirs, e))
                raise
        return filepath

    def _archiveScreenshot(self, filepath):
        if self._screenshotArchiveMethod == "remove":
            try:
                os.remove(filepath)
            except IOError:
                pass
        elif self._screenshotArchiveMethod.startswith("resize"):
            if self._screenshotArchiveMethod == "resize":
                convertArgs = ["-resize",
                               "%sx" % (int(self.screenSize()[0]) / 4,)]
            else:
                widthHeight = self._screenshotArchiveMethod.split()[1]
                convertArgs = ["-resize", widthHeight]
            subprocess.call([fmbt_config.imagemagick_convert, filepath] + convertArgs + [filepath])

    def _archiveScreenshots(self):
        """
        Archive screenshot files if screenshotLimit has been exceeded.
        """
        freeScreenshots = [filename
                           for (filename, refCount) in self._screenshotRefCount.iteritems()
                           if refCount == 0]
        archiveCount = len(freeScreenshots) - self._screenshotLimit
        if archiveCount > 0:
            freeScreenshots.sort(reverse=True) # archive oldest
            while archiveCount > 0:
                toBeArchived = freeScreenshots.pop()
                try:
                    self._archiveScreenshot(toBeArchived)
                except IOError:
                    pass
                del self._screenshotRefCount[toBeArchived]
                archiveCount -= 1

    def refreshScreenshot(self, forcedScreenshot=None, rotate=None):
        """
        Takes new screenshot and updates the latest screenshot object.

        Parameters:

          forcedScreenshot (Screenshot or string, optional):
                  use given screenshot object or image file, do not
                  take new screenshot.

          rotate (integer, optional):
                  rotate screenshot by given number of degrees. This
                  overrides constructor rotateScreenshot parameter
                  value. The default is None (no override).

        Returns Screenshot object, and makes the same object "the
        latest screenshot" that is used by all *Bitmap and *OcrText
        methods. Returns None if screenshot cannot be taken.
        """
        if forcedScreenshot != None:
            if type(forcedScreenshot) == str:
                self._lastScreenshot = Screenshot(
                    screenshotFile=forcedScreenshot,
                    paths = self._paths,
                    ocrEngine=self._ocrEngine,
                    oirEngine=self._oirEngine,
                    screenshotRefCount=self._screenshotRefCount)
            else:
                self._lastScreenshot = forcedScreenshot
        elif self._conn: # There is a connection, get new screenshot
            if self.screenshotDir() == None:
                self.setScreenshotDir(self._screenshotDirDefault)
            if self.screenshotSubdir() == None:
                self.setScreenshotSubdir(self._screenshotSubdirDefault)
            screenshotFile = self._newScreenshotFilepath()
            if self.existingConnection().recvScreenshot(screenshotFile):
                # New screenshot successfully received from device
                if rotate == None:
                    rotate = self._rotateScreenshot
                if rotate != None and rotate != 0:
                    subprocess.call([fmbt_config.imagemagick_convert, screenshotFile, "-rotate", str(rotate), screenshotFile])
                self._lastScreenshot = Screenshot(
                    screenshotFile=screenshotFile,
                    paths = self._paths,
                    ocrEngine=self._ocrEngine,
                    oirEngine=self._oirEngine,
                    screenshotRefCount=self._screenshotRefCount)
            else:
                self._lastScreenshot = None
        else: # No connection, cannot get a screenshot
            self._lastScreenshot = None
        # Make sure unreachable Screenshot instances are released from
        # memory.
        gc.collect()
        for obj in gc.garbage:
            if isinstance(obj, Screenshot):
                if hasattr(obj, "_logCallReturnValue"):
                    # Some methods have been wrapped by visual
                    # log. Break reference cycles to let gc collect
                    # them.
                    del obj.findItemsByBitmap
                    del obj.findItemsByOcr
        del gc.garbage[:]
        gc.collect()

        # If screenshotLimit has been set, archive old screenshot
        # stored on the disk.
        if self._screenshotLimit != None and self._screenshotLimit >= 0:
            self._archiveScreenshots()

        return self._lastScreenshot

    def screenshot(self):
        """
        Returns the latest Screenshot object.

        Use refreshScreenshot() to get a new screenshot.
        """
        return self._lastScreenshot

    def screenshotArchiveMethod(self):
        """
        Returns how screenshots exceeding screenshotLimit are archived.
        """
        return self._screenshotArchiveMethod

    def screenshotDir(self):
        """
        Returns the directory under which new screenshots are saved.
        """
        return self._screenshotDir

    def screenshotLimit(self):
        """
        Returns the limit after which unused screenshots are archived.
        """
        return self._screenshotLimit

    def screenshotSubdir(self):
        """
        Returns the subdirectory in screenshotDir under which new
        screenshots are stored.
        """
        return self._screenshotSubdir

    def screenSize(self):
        """
        Returns screen size in pixels in tuple (width, height).
        """
        if self._lastScreenshot != None:
            self._screenSize = self._lastScreenshot.size()
        if self._screenSize == None:
            if self._lastScreenshot == None:
                self.refreshScreenshot()
                self._screenSize = self._lastScreenshot.size()
                self._lastScreenshot = None
            else:
                self._screenSize = self._lastScreenshot.size()
        return self._screenSize

    def setBitmapPath(self, bitmapPath, rootForRelativePaths=None):
        """
        Set new path for finding bitmaps.

        Parameters:

          bitmapPath (string)
                  colon-separated list of directories from which
                  bitmap methods look for bitmap files.

          rootForRelativePaths (string, optional)
                  path that will prefix all relative paths in
                  bitmapPath.

        Example:

          gui.setBitmapPath("bitmaps:icons:/tmp", "/home/X")
          gui.tapBitmap("start.png")

          will look for /home/X/bitmaps/start.png,
          /home/X/icons/start.png and /tmp/start.png, in this order.
        """
        self._paths.bitmapPath = bitmapPath
        if rootForRelativePaths != None:
            self._paths.relativeRoot = rootForRelativePaths

    def setConnection(self, conn):
        """
        Set the connection object that performs actions on real target.

        Parameters:

          conn (GUITestConnection instance):
                  The connection to be used.
        """
        self._conn = conn

    def setOcrEngine(self, ocrEngine):
        """
        Set OCR (optical character recognition) engine that will be
        used by default in new screenshots.

        Returns previous default.
        """
        prevDefault = self._ocrEngine
        self._ocrEngine = ocrEngine
        return prevDefault

    def setOirEngine(self, oirEngine):
        """
        Set OIR (optical image recognition) engine that will be used
        by default in new screenshots.

        Returns previous default.
        """
        prevDefault = self._oirEngine
        self._oirEngine = oirEngine
        return prevDefault

    def setScreenshotArchiveMethod(self, screenshotArchiveMethod):
        """
        Set method for archiving screenshots when screenshotLimit is exceeded.

        Parameters:
          screenshotArchiveMethod (string)
                  Supported methods are "resize [WxH]" and "remove"
                  where W and H are integers that define maximum width and
                  height for an archived screenshot.
                  The default method is "resize".
        """
        if screenshotArchiveMethod == "remove":
            pass
        elif screenshotArchiveMethod == "resize":
            pass
        elif screenshotArchiveMethod.startswith("resize"):
            try:
                w, h = screenshotArchiveMethod.split(" ")[1].split("x")
            except:
                raise ValueError("Invalid resize syntax")
            try:
                w, h = int(w), int(h)
            except:
                raise ValueError(
                    "Invalid resize width or height, integer expected")
        else:
            raise ValueError('Unknown archive method "%s"' %
                             (screenshotArchiveMethod,))
        self._screenshotArchiveMethod = screenshotArchiveMethod

    def setScreenshotDir(self, screenshotDir):
        self._screenshotDir = screenshotDir
        self._newScreenshotFilepath() # make directories

    def setScreenshotLimit(self, screenshotLimit):
        """
        Set maximum number for unarchived screenshots.

        Parameters:
          screenshotLimit (integer)
                  Maximum number of unarchived screenshots that are
                  free for archiving (that is, not referenced by test code).
                  The default is None, that is, there is no limit and
                  screenshots are never archived.

        See also:
          setScreenshotArchiveMethod()
        """
        self._screenshotLimit = screenshotLimit

    def setScreenshotSubdir(self, screenshotSubdir):
        """
        Define a subdirectory under screenshotDir() for screenshot files.

        Parameters:

          screenshotSubdir (string)
                  Name of a subdirectory. The name should contain
                  conversion specifiers supported by strftime.

        Example:

          sut.setScreenshotSubdir("%m-%d-%H")
                  A screenshot taken on June 20th at 4.30pm will
                  be stored to screenshotDir/06-20-16. That is,
                  screenshots taken on different hours will be
                  stored to different subdirectories.

        By default, all screenshots are stored directly to screenshotDir().
        """
        self._screenshotSubdir = screenshotSubdir

    def setTapDefaults(self, **tapDefaults):
        """
        Define default parameters for tap methods.

        Parameters:

          **tapDefaults (keyword arguments):
                  default arguments to be used in sendTap call unless
                  explicitely overridden by user.

        Example:

          sut.setTapDefaults(button=1)
                  after this sut.tapBitmap("ref.png") does the same as
                  sut.tapBitmap("ref.png", button=1) did before.
        """
        self._tapDefaults.update(tapDefaults)

    def swipe(self, (x, y), direction, distance=1.0, **dragArgs):
        """
        swipe starting from coordinates (x, y) to given direction.

        Parameters:

          coordinates (floats in range [0.0, 1.0] or integers):
                  floating point coordinates in range [0.0, 1.0] are
                  scaled to full screen width and height, others are
                  handled as absolute coordinate values.

          direction (string or integer):
                  Angle (0..360 degrees), or "north", "south", "east"
                  and "west" (corresponding to angles 90, 270, 0 and
                  180).

          distance (float, optional):
                  Swipe distance. Values in range [0.0, 1.0] are
                  scaled to the distance from the coordinates to the
                  edge of the screen. The default is 1.0: swipe to the
                  edge of the screen.

          rest of the parameters: refer to drag documentation.

        Returns True on success, False if sending input failed.
        """
        if type(direction) == str:
            d = direction.lower()
            if d in ["n", "north"]: direction = 90
            elif d in ["s", "south"]: direction = 270
            elif d in ["e", "east"]: direction = 0
            elif d in ["w", "west"]: direction = 180
            else: raise ValueError('Illegal direction "%s"' % (direction,))

        direction = direction % 360
        x, y = self.intCoords((x, y))
        dirRad = math.radians(direction)
        distToEdge = _edgeDistanceInDirection((x, y), self.screenSize(), direction)

        if distance > 1.0: distance = float(distance) / distToEdge

        x2 = int(x + math.cos(dirRad) * distToEdge * distance)
        y2 = int(y - math.sin(dirRad) * distToEdge * distance)

        return self.drag((x, y), (x2, y2), **dragArgs)

    def swipeBitmap(self, bitmap, direction, distance=1.0, **dragAndOirArgs):
        """
        swipe starting from bitmap to given direction.

        Parameters:

          bitmap (string)
                  bitmap from which swipe starts

          direction, distance
                  refer to swipe documentation.

          startPos, startOffset
                  refer to swipeItem documentation.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).

          delayBeforeMoves, delayBetweenMoves, delayAfterMoves,
          movePoints
                  refer to drag documentation.

        Returns True on success, False if sending input failed.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        dragArgs, rest = _takeDragArgs(dragAndOirArgs)
        oirArgs, _ = _takeOirArgs(self._lastScreenshot, rest, thatsAll=True)
        oirArgs["limit"] = 1
        items = self._lastScreenshot.findItemsByBitmap(bitmap, **oirArgs)
        if len(items) == 0:
            return False
        return self.swipeItem(items[0], direction, distance, **dragArgs)

    def swipeItem(self, viewItem, direction, distance=1.0, **dragArgs):
        """
        swipe starting from viewItem to given direction.

        Parameters:

          viewItem (ViewItem)
                  item from which swipe starts

          direction, distance
                  refer to swipe documentation.

          startPos (pair of floats (x, y)):
                  position of starting swipe, relative to the item.
                  (0.0, 0.0) is the top-left corner,
                  (1.0, 0.0) is the top-right corner,
                  (1.0, 1.0) is the lower-right corner.
                  Values < 0.0 and > 1.0 start swiping from coordinates
                  outside the item.
                  The default is (0.5, 0.5), in the middle of the item.

          startOffset (pair of integers or floats (x, y)):
                  offset of swipe start coordinates. Integers are
                  pixels, floats are relative to screensize.
                  Example:
                  startOffset=(0, 0.1) will keep the X coordinate
                  unchagned and add 10 % of screensize to Y.

          delayBeforeMoves, delayBetweenMoves, delayAfterMoves,
          movePoints
                  refer to drag documentation.

        Returns True on success, False if sending input failed.
        """
        if "startPos" in dragArgs:
            posX, posY = dragArgs["startPos"]
            del dragArgs["startPos"]
            x1, y1, x2, y2 = viewItem.bbox()
            swipeCoords = (x1 + (x2-x1) * posX,
                           y1 + (y2-y1) * posY)
        else:
            swipeCoords = viewItem.coords()

        if "startOffset" in dragArgs:
            offX, offY = dragArgs["startOffset"]
            del dragArgs["startOffset"]
            x, y = swipeCoords
            if isinstance(offX, int):
                x += offX
            elif isinstance(offX, float):
                width, _ = self.screenSize()
                x += offX * width
            else:
                raise TypeError('invalid offset %s (int or float expected)' %
                                (repr(offX),))
            if isinstance(offY, int):
                y += offY
            elif isinstance(offY, float):
                _, height = self.screenSize()
                y += offY * height
            else:
                raise TypeError('invalid offset %s (int or float expected)' %
                                (repr(offY),))
            swipeCoords = (x, y)

        return self.swipe(swipeCoords, direction, distance, **dragArgs)

    def swipeOcrText(self, text, direction, distance=1.0, **dragAndOcrArgs):
        """
        Find text from the latest screenshot using OCR, and swipe it.

        Parameters:

          text (string):
                  the text to be swiped.

          direction, distance
                  refer to swipe documentation.

          startPos
                  refer to swipeItem documentation.

          delayBeforeMoves, delayBetweenMoves, delayAfterMoves,
          movePoints
                  refer to drag documentation.

          OCR engine specific arguments
                  refer to help(obj.ocrEngine())

        Returns True on success, False otherwise.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        dragArgs, rest = _takeDragArgs(dragAndOcrArgs)
        ocrArgs, _ = _takeOcrArgs(self._lastScreenshot, rest, thatsAll=True)
        items = self._lastScreenshot.findItemsByOcr(text, **ocrArgs)
        if len(items) == 0:
            return False
        return self.swipeItem(items[0], direction, distance, **dragArgs)

    def tap(self, (x, y), long=_USE_DEFAULTS, hold=_USE_DEFAULTS,
            count=_USE_DEFAULTS, delayBetweenTaps=_USE_DEFAULTS,
            button=_USE_DEFAULTS):
        """
        Tap screen on coordinates (x, y).

        Parameters:

          coordinates (floats in range [0.0, 1.0] or integers):
                  floating point coordinates in range [0.0, 1.0] are
                  scaled to full screen width and height, others are
                  handled as absolute coordinate values.

          count (integer, optional):
                  number of taps to the coordinates. The default is 1.

          delayBetweenTaps (float, optional):
                  time (seconds) between taps when count > 1.
                  The default is 0.175 (175 ms).

          long (boolean, optional):
                  if True, touch the screen for a long time.

          hold (float, optional):
                  time in seconds to touch the screen.

          button (integer, optional):
                  send tap using given mouse button. The default is
                  None: button parameter is not passed to the
                  underlying connection layer (sendTouchDown etc.),
                  the default in the underlying layer will be used.
                  Note that all connection layers may not support
                  this parameter.

        Returns True if successful, otherwise False.
        """
        if long == _USE_DEFAULTS:
            long = self._tapDefaults.get("long", False)
        if hold == _USE_DEFAULTS:
            hold = self._tapDefaults.get("hold", 0.0)
        if count == _USE_DEFAULTS:
            count = self._tapDefaults.get("count", 1)
        if delayBetweenTaps == _USE_DEFAULTS:
            delayBetweenTaps = self._tapDefaults.get("delayBetweenTaps", 0.175)
        if button == _USE_DEFAULTS:
            button = self._tapDefaults.get("button", None)

        x, y = self.intCoords((x, y))
        count = int(count)
        if long and hold == 0.0:
            hold = self._longTapHoldTime
        extraParams = {}
        if button != None:
            extraParams['button'] = button
        if count == 0:
            self.existingConnection().sendTouchMove(x, y)
        while count > 0:
            if hold > 0.0:
                try:
                    assert self.existingConnection().sendTouchDown(x, y, **extraParams)
                    time.sleep(hold)
                    assert self.existingConnection().sendTouchUp(x, y, **extraParams)
                except AssertionError:
                    return False
            else:
                if not self.existingConnection().sendTap(x, y, **extraParams):
                    return False
            count = int(count) - 1
        return True

    def tapBitmap(self, bitmap, **tapAndOirArgs):
        """
        Find a bitmap from the latest screenshot, and tap it.

        Parameters:

          bitmap (string):
                  filename of the bitmap to be tapped.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).

          tapPos (pair of floats (x,y)):
                  refer to tapItem documentation.

          tapOffset (pair of floats or integers (x, y)):
                  refer to tapItem documentation.

          long, hold, count, delayBetweenTaps, button (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        tapArgs, rest = _takeTapArgs(tapAndOirArgs)
        oirArgs, _ = _takeOirArgs(self._lastScreenshot, rest, thatsAll=True)
        oirArgs["limit"] = 1
        items = self._lastScreenshot.findItemsByBitmap(bitmap, **oirArgs)
        if len(items) == 0:
            return False
        return self.tapItem(items[0], **tapArgs)

    def tapDefaults(self):
        """
        Returns default parameters for sendTap method.

        See also setTapDefaults.
        """
        return self._tapDefaults

    def tapItem(self, viewItem, **tapArgs):
        """
        Tap the center point of viewItem.

        Parameters:

          viewItem (GUIItem object):
                  item to be tapped, possibly returned by
                  findItemsBy... methods in Screenshot or View.

          tapPos (pair of floats (x, y)):
                  position to tap, relative to the item.
                  (0.0, 0.0) is the top-left corner,
                  (1.0, 0.0) is the top-right corner,
                  (1.0, 1.0) is the lower-right corner.
                  Values < 0 and > 1 tap coordinates outside the item.
                  The default is (0.5, 0.5), in the middle of the item.

          tapOffset (pair of floats or integers (x, y)):
                  offset of tap coordinates. Integers are
                  pixels, floats are relative to screensize.
                  Example:
                  tapOffset=(0, 0.1) will keep the X coordinate
                  unchagned and add 10 % of screensize to Y.

          long, hold, count, delayBetweenTaps, button (optional):
                  refer to tap documentation.
        """
        if "tapPos" in tapArgs:
            posX, posY = tapArgs["tapPos"]
            del tapArgs["tapPos"]
            x1, y1, x2, y2 = viewItem.bbox()
            tapCoords = (x1 + (x2-x1) * posX,
                         y1 + (y2-y1) * posY)
        else:
            tapCoords = viewItem.coords()

        if "tapOffset" in tapArgs:
            offX, offY = tapArgs["tapOffset"]
            del tapArgs["tapOffset"]
            x, y = tapCoords
            if isinstance(offX, int):
                x += offX
            elif isinstance(offX, float):
                width, _ = self.screenSize()
                x += offX * width
            else:
                raise TypeError('invalid offset %s (int or float expected)' %
                                (repr(offX),))
            if isinstance(offY, int):
                y += offY
            elif isinstance(offY, float):
                _, height = self.screenSize()
                y += offY * height
            else:
                raise TypeError('invalid offset %s (int or float expected)' %
                                (repr(offY),))
            tapCoords = (x, y)
        return self.tap(tapCoords, **tapArgs)

    def tapOcrText(self, text, appearance=0, **tapAndOcrArgs):
        """
        Find text from the latest screenshot using OCR, and tap it.

        Parameters:

          text (string):
                  the text to be tapped.

          long, hold, count, delayBetweenTaps, button (optional):
                  refer to tap documentation.

          OCR engine specific arguments
                  refer to help(obj.ocrEngine())

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        tapArgs, rest = _takeTapArgs(tapAndOcrArgs)
        ocrArgs, _ = _takeOcrArgs(self._lastScreenshot, rest, thatsAll=True)
        items = self._lastScreenshot.findItemsByOcr(text, **ocrArgs)
        if len(items) <= appearance:
            return False
        return self.tapItem(items[appearance], **tapArgs)

    def type(self, text):
        """
        Type text.
        """
        return self.existingConnection().sendType(text)

    def verifyOcrText(self, text, **ocrArgs):
        """
        Verify using OCR that the last screenshot contains the text.

        Parameters:

          text (string):
                  text to be verified.

          OCR engine specific arguments
                  refer to help(obj.ocrEngine())

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        ocrArgs, _ = _takeOcrArgs(self._lastScreenshot, ocrArgs, thatsAll=True)
        return self._lastScreenshot.findItemsByOcr(text, **ocrArgs) != []

    def verifyBitmap(self, bitmap, **oirArgs):
        """
        Verify that bitmap is present in the last screenshot.

        Parameters:

          bitmap (string):
                  filename of the bitmap file to be searched for.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).
        """
        assert self._lastScreenshot != None, "Screenshot required."
        oirArgs, _ = _takeOirArgs(self._lastScreenshot, oirArgs, thatsAll=True)
        oirArgs["limit"] = 1
        return self._lastScreenshot.findItemsByBitmap(bitmap, **oirArgs) != []

    def wait(self, refreshFunc, waitFunc, waitFuncArgs=(), waitFuncKwargs={},
             waitTime = 5.0, pollDelay = 1.0,
             beforeRefresh = lambda: None, afterRefresh = lambda: None):
        """
        Wait until waitFunc returns True or waitTime has expired.

        Parameters:

          refreshFunc (function):
                  this function is called before re-evaluating
                  waitFunc. For instance, refreshScreenshot.

          waitFunc, waitFuncArgs, waitFuncKwargs (function, tuple,
          dictionary):
                  wait for waitFunc(waitFuncArgs, waitFuncKwargs) to
                  return True

          waitTime (float, optional):
                  max. time in seconds to wait for. The default is
                  5.0.

          pollDelay (float, optional):
                  time in seconds to sleep between refreshs. The
                  default is 1.0.

          beforeRefresh (function, optional):
                  this function will be called before every refreshFunc call.
                  The default is no operation.

          afterRefresh (function, optional):
                  this function will be called after every refreshFunc call.
                  The default is no operation.

        Returns True if waitFunc returns True - either immediately or
        before waitTime has expired - otherwise False.

        refreshFunc will not be called if waitFunc returns immediately
        True.
        """
        if waitFunc(*waitFuncArgs, **waitFuncKwargs):
            return True
        startTime = time.time()
        endTime = startTime + waitTime
        now = startTime
        while now < endTime:
            time.sleep(min(pollDelay, (endTime - now)))
            now = time.time()
            beforeRefresh()
            refreshFunc()
            afterRefresh()
            if waitFunc(*waitFuncArgs, **waitFuncKwargs):
                return True
        return False

    def waitAnyBitmap(self, listOfBitmaps, **waitAndOirArgs):
        """
        Wait until any of given bitmaps appears on screen.

        Parameters:

          listOfBitmaps (list of strings):
                  list of bitmaps (filenames) to be waited for.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                  refer to wait documentation.

        Returns list of bitmaps appearing in the first screenshot that
        contains at least one of the bitmaps. If none of the bitmaps
        appear within the time limit, returns empty list.

        If the bitmap is not found from most recently refreshed
        screenshot, waitAnyBitmap updates the screenshot.
        """
        if listOfBitmaps == []: return []
        if not self._lastScreenshot: self.refreshScreenshot()
        waitArgs, rest = _takeWaitArgs(waitAndOirArgs)
        oirArgs, _ = _takeOirArgs(self._lastScreenshot, rest, thatsAll=True)
        foundBitmaps = []
        def observe():
            for bitmap in listOfBitmaps:
                if self._lastScreenshot.findItemsByBitmap(bitmap, **oirArgs):
                    foundBitmaps.append(bitmap)
            return foundBitmaps != []
        self.wait(self.refreshScreenshot, observe, **waitArgs)
        return foundBitmaps

    def waitAnyOcrText(self, listOfTexts, **waitAndOcrArgs):
        """
        Wait until OCR recognizes any of texts on the screen.

        Parameters:

          listOfTexts (list of string):
                  texts to be waited for.

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                  refer to wait documentation.

          OCR engine specific arguments
                  refer to help(obj.ocrEngine())

        Returns list of texts that appeared in the first screenshot
        that contains at least one of the texts. If none of the texts
        appear within the time limit, returns empty list.

        If any of texts is not found from most recently refreshed
        screenshot, waitAnyOcrText updates the screenshot.
        """
        if listOfTexts == []: return []
        if not self._lastScreenshot: self.refreshScreenshot()
        waitArgs, rest = _takeWaitArgs(waitAndOcrArgs)
        ocrArgs, _ = _takeOcrArgs(self._lastScreenshot, rest, thatsAll=True)
        foundTexts = []
        def observe():
            for text in listOfTexts:
                if self.verifyOcrText(text, **ocrArgs):
                    foundTexts.append(text)
            return foundTexts != []
        self.wait(self.refreshScreenshot, observe, **waitArgs)
        return foundTexts

    def waitBitmap(self, bitmap, **waitAndOirArgs):
        """
        Wait until bitmap appears on screen.

        Parameters:

          bitmap (string):
                  filename of the bitmap to be waited for.

          optical image recognition arguments (optional)
                  refer to help(obj.oirEngine()).

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                  refer to wait documentation.

        Returns True if bitmap appeared within given time limit,
        otherwise False.

        If the bitmap is not found from most recently refreshed
        screenshot, waitBitmap updates the screenshot.
        """
        return self.waitAnyBitmap([bitmap], **waitAndOirArgs) != []

    def waitOcrText(self, text, **waitAndOcrArgs):
        """
        Wait until OCR detects text on the screen.

        Parameters:

          text (string):
                  text to be waited for.

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                  refer to wait documentation.

          OCR engine specific arguments
                  refer to help(obj.ocrEngine())

        Returns True if the text appeared within given time limit,
        otherwise False.

        If the text is not found from most recently refreshed
        screenshot, waitOcrText updates the screenshot.
        """
        return self.waitAnyOcrText([text], **waitAndOcrArgs) != []

    def waitScreenUpdated(self, **waitArgs):
        """
        Wait until screenshot has been updated or waitTime expired.

        Parameters:

          waitTime, pollDelay, beforeRefresh, afterRefresh (optional):
                  refer to wait documentation.

        Returns True if screenshot was updated before waitTime expired,
        otherwise False. If waitTime is 0, screenshot is refreshed once.
        Returns True if the screenshot differs from the previous.

        waitScreenUpdated refreshes the screenshot.
        """
        waitTime = waitArgs.get("waitTime", 5.0)
        pollDelay = waitArgs.get("pollDelay", 1.0)
        beforeRefresh = waitArgs.get("beforeRefresh", lambda: None)
        afterRefresh = waitArgs.get("afterRefresh", lambda: None)
        updated = self.existingConnection().recvScreenUpdated(waitTime, pollDelay)
        if updated == None:
            # optimised version is not available, this is a fallback
            previousScreenshot = self.screenshot()
            if previousScreenshot == None:
                beforeRefresh()
                self.refreshScreenshot()
                afterRefresh()
                return True
            # return True if screen changed from previous even with
            # waitTime == 0, therefore refresh before calling wait.
            beforeRefresh()
            self.refreshScreenshot()
            afterRefresh()
            return self.wait(
                self.refreshScreenshot,
                lambda: not self.verifyBitmap(previousScreenshot.filename()),
                **waitArgs)
        elif updated == True:
            self.refreshScreenshot()
        elif updated == False:
            pass # no need to fetch the same screen
        else:
            raise ValueError("recvScreenUpdated returned illegal value: %s" % (repr(updated),))
        return updated

class Screenshot(object):
    """
    Screenshot class takes and holds a screenshot (bitmap) of device
    display, or a forced bitmap file if device connection is not given.
    """
    def __init__(self, screenshotFile=None, paths=None,
                 ocrEngine=None, oirEngine=None, screenshotRefCount=None):
        self._filename = screenshotFile
        self._ocrEngine = ocrEngine
        self._ocrEngineNotified = False
        self._oirEngine = oirEngine
        self._oirEngineNotified = False
        self._screenshotRefCount = screenshotRefCount
        if (type(self._screenshotRefCount) == dict and self._filename):
            self._screenshotRefCount[self._filename] = (1 +
                self._screenshotRefCount.get(self._filename, 0))
        self._screenSize = None
        self._paths = paths

    def __del__(self):
        if self._ocrEngine and self._ocrEngineNotified:
            self._ocrEngine.removeScreenshot(self)
        if self._oirEngine and self._oirEngineNotified:
            if (self._ocrEngineNotified == False or
                id(self._oirEngine) != id(self._ocrEngine)):
                self._oirEngine.removeScreenshot(self)
        if (type(self._screenshotRefCount) == dict and self._filename):
            self._screenshotRefCount[self._filename] -= 1

    def isBlank(self):
        """
        Returns True if screenshot is blank, otherwise False.
        """
        return _e4gImageIsBlank(self._filename)

    def setSize(self, screenSize):
        self._screenSize = screenSize

    def size(self, allowReadingFile=True):
        """
        Returns screenshot size in pixels, as pair (width, height).
        """
        if self._screenSize == None and allowReadingFile:
            e4gImage = _e4gOpenImage(self._filename)
            self._screenSize = _e4gImageDimensions(e4gImage)
            eye4graphics.closeImage(e4gImage)
        return self._screenSize

    def _notifyOcrEngine(self):
        if self._ocrEngine and not self._ocrEngineNotified:
            self._ocrEngine.addScreenshot(self)
            self._ocrEngineNotified = True
            if id(self._ocrEngine) == id(self._oirEngine):
                self._oirEngineNotified = True

    def _notifyOirEngine(self):
        if self._oirEngine and not self._oirEngineNotified:
            self._oirEngine.addScreenshot(self)
            self._oirEngineNotified = True
            if id(self._oirEngine) == id(self._ocrEngine):
                self._ocrEngineNotified = True

    def dumpHcr(self, filename, **hcrArgs):
        """
        Visualize high contrast regions, write image to given file.
        Experimental.
        """
        items = self.findItemsByHcr(**hcrArgs)
        eyenfinger.drawBboxes(self.filename(), filename,
                             [i.bbox() for i in items])

    def dumpOcr(self, **kwargs):
        """
        Return what OCR engine recognizes on this screenshot.

        Not all OCR engines provide this functionality.
        """
        self._notifyOcrEngine()
        return self._ocrEngine.dumpOcr(self, **kwargs)

    def dumpOcrWords(self, **kwargs):
        """
        Deprecated, use dumpOcr().
        """
        return self.dumpOcr(**kwargs)

    def filename(self):
        return self._filename

    def _findFirstMatchingBitmapCandidate(self, bitmap, **oirArgs):
        for candidate in self._paths.abspaths(bitmap):
            found = self._oirEngine.findBitmap(self, candidate, **oirArgs)
            if found:
                return found
        return []

    def findItemsByBitmap(self, bitmap, **oirFindArgs):
        if self._oirEngine != None:
            self._notifyOirEngine()
            oirArgsList = self._paths.oirArgsList(bitmap)
            results = []
            if oirArgsList:
                for oirArgs in oirArgsList:
                    oirArgs, _ = _takeOirArgs(self._oirEngine, oirArgs.copy())
                    oirArgs.update(oirFindArgs)
                    results.extend(self._findFirstMatchingBitmapCandidate(
                        bitmap, **oirArgs))
                    if results: break
            else:
                oirArgs = oirFindArgs
                results.extend(self._findFirstMatchingBitmapCandidate(
                    bitmap, **oirArgs))
            return results

        else:
            raise RuntimeError('Trying to use OIR on "%s" without OIR engine.' % (self.filename(),))

    def findItemsByOcr(self, text, **ocrEngineArgs):
        if self._ocrEngine != None:
            self._notifyOcrEngine()
            return self._ocrEngine.findText(self, text, **ocrEngineArgs)
        else:
            raise RuntimeError('Trying to use OCR on "%s" without OCR engine.' % (self.filename(),))

    def findItemsByHcr(self, xRes=24, yRes=24, threshold=0.1):
        """
        Return "high contrast regions" in the screenshot.

        Experimental. See if it finds regions that could be
        interacted with.
        """
        ppFilename = "%s-hcrpp.png" % (self.filename(),)
        _convert(self.filename(),
                 ["-colorspace", "gray", "-depth", "3"],
                 ppFilename)
        bbox = _Bbox(0, 0, 0, 0, 0)
        foundItems = []
        try:
            image = _e4gOpenImage(ppFilename)
            while True:
                if eye4graphics.findNextHighErrorBlock(ctypes.byref(bbox), image, xRes, yRes, threshold, 0) == 0:
                    break
                foundItems.append(GUIItem(
                    "%sx%s/%s" % (bbox.left/xRes, bbox.top/yRes, bbox.error),
                    (bbox.left, bbox.top, bbox.right, bbox.bottom),
                    self))
        finally:
            eye4graphics.closeImage(image)
        return foundItems

    def ocrItems(self, **ocrArgs):
        """
        Return list of GUIItems, each of them corresponding to a word
        recognized by OCR. OCR engine must support dumpOcr.

        Parameters:

          **ocrArgs (keyword parameters):
                  refer to ocrEngine() documentation.
        """
        foundItems = []
        if self._ocrEngine != None:
            self._notifyOcrEngine()
            for word, bbox in self._ocrEngine.dumpOcr(self, **ocrArgs):
                foundItems.append((GUIItem(word, bbox, self.filename())))
        return foundItems

    def save(self, fileOrDirName):
        shutil.copy(self._filename, fileOrDirName)

    def ocrEngine(self):
        return self._ocrEngine

    def oirEngine(self):
        return self._oirEngine

    def __str__(self):
        return 'Screenshot(filename="%s")' % (self._filename,)

class GUIItem(object):
    """
    GUIItem holds the information of a single GUI item.
    """
    def __init__(self, name, bbox, screenshot, bitmap=None, ocrFind=None, ocrFound=None):
        self._name = name
        if screenshot and hasattr(screenshot, "size"):
            x1, y1 = _intCoords(bbox[:2], screenshot.size())
            x2, y2 = _intCoords(bbox[2:], screenshot.size())
            self._bbox = (x1, y1, x2, y2)
        else:
            self._bbox = bbox
        self._bitmap = bitmap
        self._screenshot = screenshot
        self._ocrFind = ocrFind
        self._ocrFound = ocrFound
    def bbox(self): return self._bbox
    def name(self): return self._name
    def coords(self):
        left, top, right, bottom = self.bbox()
        return (left + (right-left)/2, top + (bottom-top)/2)
    def dump(self): return str(self)
    def __str__(self):
        extras = ""
        if self._bitmap:
            extras += ', bitmap="%s"' % (self._bitmap,)
        if self._ocrFind:
            extras += ', find="%s"' % (self._ocrFind,)
        if self._ocrFound:
            extras += ', found="%s"' % (self._ocrFound,)
        if self._screenshot:
            extras += ', screenshot="%s"' % (self._screenshot,)
        return ('GUIItem("%s", bbox=%s%s)'  % (
                self.name(), self.bbox(), extras))

class _VisualLog:
    def __init__(self, device, outFileObj,
                 screenshotWidth, thumbnailWidth,
                 timeFormat, delayedDrawing,
                 copyBitmapsToScreenshotDir):
        self._device = device
        self._outFileObj = outFileObj
        if hasattr(self._outFileObj, "name"):
            self._outFilename = self._outFileObj.name
        else:
            self._outFilename = ""
        self._formattedOutFilename = self._outFilename
        self._bytesToFile = 0
        self._testStep = -1
        self._actionName = None
        self._callStack = []
        self._highlightCounter = 0
        self._screenshotWidth = screenshotWidth
        self._thumbnailWidth = thumbnailWidth
        self._timeFormat = timeFormat
        self._copyBitmapsToScreenshotDir = copyBitmapsToScreenshotDir
        self._userFrameId = 0
        self._userFunction = ""
        self._userCallCount = 0
        eyenfinger.iSetDefaultDelayedDrawing(delayedDrawing)
        device.refreshScreenshot = self.refreshScreenshotLogger(device.refreshScreenshot)
        device.tap = self.tapLogger(device.tap)
        device.drag = self.dragLogger(device.drag)
        device.visualLog = self.messageLogger(device.visualLog)
        attrs = ['callContact', 'callNumber', 'close',
                 'loadConfig', 'platformVersion',
                 'pressAppSwitch', 'pressBack', 'pressHome',
                 'pressKey', 'pressMenu', 'pressPower',
                 'pressVolumeUp', 'pressVolumeDown',
                 'reboot', 'reconnect', 'refreshView',
                 'shell', 'shellSOE', 'smsNumber', 'supportsView',
                 'swipe', 'swipeBitmap', 'swipeItem', 'swipeOcrText',
                 'systemProperty',
                 'tapBitmap', 'tapId', 'tapItem', 'tapOcrText',
                 'tapText', 'topApp', 'topWindow', 'type',
                 'verifyOcrText', 'verifyText', 'verifyBitmap',
                 'waitAnyBitmap', 'waitBitmap', 'waitOcrText',
                 'waitScreenUpdated', 'waitText']
        for a in attrs:
            if hasattr(device, a):
                m = getattr(device, a)
                setattr(device, m.func_name, self.genericLogger(m))
        if not self.logFileSplit():
            self.logHeader()
        self._blockId = 0

    def close(self):
        if self._outFileObj != None:
            html = []
            if self._bytesToFile > 0:
                for c in xrange(len(self._callStack)):
                    html.append('</table></tr>') # end call
                html.append('</table></div></td></tr></table></ul>') # end step
                html.append('</body></html>') # end html
                self.write('\n'.join(html))
            if (self._formattedOutFilename and
                "%" in self._outFilename):
                # Files with strftime-formatted names are opened and
                # closed by this class. Other file-like objects are
                # own by someone else.
                if hasattr(self._outFileObj, "close"):
                    self._outFileObj.close()
                if os.stat(self._formattedOutFilename).st_size == 0:
                    os.remove(self._formattedOutFilename)
            # File instance should be closed by the opener
            self._outFileObj = None

    def open(self, newFormattedFilename):
        self._bytesToFile = 0
        self._formattedOutFilename = newFormattedFilename
        self._outFileObj = file(self._formattedOutFilename, "w")

    def write(self, s):
        self._bytesToFile += len(s)
        if self._outFileObj != None:
            self._outFileObj.write(s)
            self._outFileObj.flush()

    def timestamp(self, t=None):
        return fmbt.formatTime(self._timeFormat, t)

    def epochTimestamp(self, t=None):
        return fmbt.formatTime("%s.%f", t)

    def htmlTimestamp(self, t=None):
        if t == None:
            t = datetime.datetime.now()
        retval = '<div class="time" id="%s"><a id="time%s">%s</a></div>' % (
            self.epochTimestamp(t), self.epochTimestamp(t), self.timestamp(t))
        return retval

    def logFileSplit(self):
        """Returns True if old log file was closed and new initialised"""
        if "%" in self._outFilename:
            # log filename is strftime formatted
            newOutFilename = fmbt.formatTime(self._outFilename)
            if newOutFilename != self._formattedOutFilename:
                self.close()
                # prepare new log file
                self.open(newOutFilename)
                self.logHeader()
                return True
        return False

    def logBlock(self):
        ts = fmbt.getTestStep()
        an = fmbt.getActionName()
        if ts == -1 or an == "undefined":
            an = self._userFunction
            ts = self._userCallCount
        if self._testStep != ts or self._actionName != an:
            if self._blockId != 0:
                # new top level log entry
                self.write('</table></div></td></tr></table></ul>')
                # if log splitting is in use, this is a good place to
                # start logging into next file
                self.logFileSplit()
            actionHtml = '''\n\n<ul><li><table><tr><td>%s</td><td><div class="step"><a id="blockId%s" href="javascript:showHide('S%s')">%s. %s</a></div><div class="funccalls" id="S%s"><table>\n''' % (
                self.htmlTimestamp(), self._blockId, self._blockId, ts, cgi.escape(an), self._blockId)
            self.write(actionHtml)
            self._testStep = ts
            self._actionName = an
            self._blockId += 1

    def logCall(self, img=None, width="", imgTip=""):
        callee = inspect.currentframe().f_back.f_code.co_name[:-4] # cut "WRAP"
        argv = inspect.getargvalues(inspect.currentframe().f_back)
        # calleeArgs = str(argv.locals['args']) + " " + str(argv.locals['kwargs'])
        args = [repr(a) for a in argv.locals['args']]
        for key, value in argv.locals['kwargs'].iteritems():
            args.append("%s=%s" % (key, repr(value)))
        calleeArgs = "(%s)" % (", ".join(args),)
        callerFrame = inspect.currentframe().f_back.f_back
        callerFilename = callerFrame.f_code.co_filename
        callerLineno = callerFrame.f_lineno
        if len(self._callStack) == 0 and (self._userFunction == '<module>' or not self._userFrameId in [(id(se[0]), getattr(se[0].f_back, "f_lasti", None)) for se in inspect.stack()]):
            self._userFunction = callerFrame.f_code.co_name
            self._userCallCount += 1
            self._userFrameId = (id(callerFrame), getattr(callerFrame.f_back, "f_lasti", None))
        self.logBlock()
        imgHtml = self.imgToHtml(img, width, imgTip, "call:%s" % (callee,))
        t = datetime.datetime.now()
        callHtml = '''
             <tr><td></td><td><table><tr>
                 <td>%s</td><td><a title="%s:%s"><div class="call">%s%s</div></a></td>
             </tr>
             %s''' % (self.htmlTimestamp(t), cgi.escape(callerFilename), callerLineno, cgi.escape(callee), cgi.escape(str(calleeArgs)), imgHtml)
        self.write(callHtml)
        self._callStack.append(callee)
        return (self.timestamp(t), callerFilename, callerLineno)

    def logReturn(self, retval, img=None, width="", imgTip="", tip=""):
        imgHtml = self.imgToHtml(img, width, imgTip, "return:%s" % (self._callStack[-1],))
        self._callStack.pop()
        returnHtml = '''
             <tr>
                 <td>%s</td><td><div class="returnvalue"><a title="%s">== %s</a></div></td>
             </tr>%s
             </table></tr>\n''' % (self.htmlTimestamp(), tip, cgi.escape(str(retval)), imgHtml)
        self.write(returnHtml)

    def logException(self):
        einfo = sys.exc_info()
        self._callStack.pop()
        excHtml = '''
             <tr>
                 <td>%s</td><td><div class="exception"><a title="%s">!! %s</a></div></td>
             </tr>
             </table></tr>\n''' % (self.htmlTimestamp(), cgi.escape(traceback.format_exception(*einfo)[-2].replace('"','').strip()), cgi.escape(str(traceback.format_exception_only(einfo[0], einfo[1])[0])))
        self.write(excHtml)

    def logMessage(self, msg):
        callerFrame = inspect.currentframe().f_back.f_back
        callerFilename = callerFrame.f_code.co_filename
        callerLineno = callerFrame.f_lineno
        self.logBlock()
        t = datetime.datetime.now()
        msgHtml = '''
            <tr><td></td><td><table>
                <tr><td>%s</td><td><a title="%s:%s"><div class="message">%s</div></a></td></tr>
            </table></td></tr>\n''' % (self.htmlTimestamp(t), cgi.escape(callerFilename), callerLineno, cgi.escape(msg))
        self.write(msgHtml)

    def logHeader(self):
        self.write('''
            <!DOCTYPE html><html>
            <head><meta charset="utf-8"><title>fmbtandroid visual log</title>
            <SCRIPT><!--
            function showHide(eid){
                if (document.getElementById(eid).style.display != 'inline'){
                    document.getElementById(eid).style.display = 'inline';
                } else {
                    document.getElementById(eid).style.display = 'none';
                }
            }
            // --></SCRIPT>
            <style>
                td { vertical-align: top }
                ul { list-style-type: none }
                .funccalls { display: none }
            </style>
            </head><body>
            ''')

    def doCallLogException(self, origMethod, args, kwargs):
        try: return origMethod(*args, **kwargs)
        except:
            self.logException()
            raise

    def genericLogger(loggerSelf, origMethod):
        def origMethodWRAP(*args, **kwargs):
            loggerSelf.logCall()
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            loggerSelf.logReturn(retval, tip=origMethod.func_name)
            return retval
        loggerSelf.changeCodeName(origMethodWRAP, origMethod.func_name + "WRAP")
        return origMethodWRAP

    def messageLogger(loggerSelf, origMethod):
        def origMethodWRAP(*args, **kwargs):
            loggerSelf.logMessage(" ".join([str(a) for a in args]))
            return True
        loggerSelf.changeCodeName(origMethodWRAP, origMethod.func_name + "WRAP")
        return origMethodWRAP

    def dragLogger(loggerSelf, origMethod):
        def dragWRAP(*args, **kwargs):
            loggerSelf.logCall()
            x1, y1 = args[0]
            x2, y2 = args[1]
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            try:
                screenshotFilename = loggerSelf._device.screenshot().filename()
                highlightFilename = loggerSelf.highlightFilename(screenshotFilename)
                iC = loggerSelf._device.intCoords
                eyenfinger.drawLines(screenshotFilename, highlightFilename, [], [iC((x1, y1)), iC((x2, y2))])
                loggerSelf.logReturn(retval, img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name)
            except:
                loggerSelf.logReturn(str(retval) + " (no screenshot available)", tip=origMethod.func_name)
            return retval
        return dragWRAP

    def refreshScreenshotLogger(loggerSelf, origMethod):
        def refreshScreenshotWRAP(*args, **kwargs):
            loggerSelf._highlightCounter = 0
            logCallReturnValue = loggerSelf.logCall()
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            if retval != None:
                retval._logCallReturnValue = logCallReturnValue
                loggerSelf.logReturn(retval, img=retval, tip=origMethod.func_name)
                retval.findItemsByBitmap = loggerSelf.findItemsByBitmapLogger(retval.findItemsByBitmap, retval)
                retval.findItemsByOcr = loggerSelf.findItemsByOcrLogger(retval.findItemsByOcr, retval)
            else:
                loggerSelf.logReturn(retval, tip=origMethod.func_name)
            return retval
        return refreshScreenshotWRAP

    def tapLogger(loggerSelf, origMethod):
        def tapWRAP(*args, **kwargs):
            loggerSelf.logCall()
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            try:
                screenshotFilename = loggerSelf._device.screenshot().filename()
                highlightFilename = loggerSelf.highlightFilename(screenshotFilename)
                eyenfinger.drawClickedPoint(screenshotFilename, highlightFilename, loggerSelf._device.intCoords(args[0]))
                loggerSelf.logReturn(retval, img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name, imgTip=loggerSelf._device.screenshot()._logCallReturnValue)
            except:
                loggerSelf.logReturn(str(retval) + " (no screenshot available)", tip=origMethod.func_name)
            return retval
        return tapWRAP

    def findItemsByBitmapLogger(loggerSelf, origMethod, screenshotObj):
        def findItemsByBitmapWRAP(*args, **kwargs):
            bitmap = args[0]
            absPathBitmap = screenshotObj._paths.abspaths(bitmap)[0]
            if loggerSelf._copyBitmapsToScreenshotDir:
                screenshotDirBitmap = os.path.join(
                    os.path.dirname(screenshotObj.filename()),
                    "bitmaps",
                    bitmap.lstrip(os.sep))
                if not os.access(screenshotDirBitmap, os.R_OK):
                    # bitmap is not yet copied under screenshotDir
                    destDir = os.path.dirname(screenshotDirBitmap)
                    if not os.access(destDir, os.W_OK):
                        try:
                            os.makedirs(destDir)
                        except IOError:
                            pass # cannot make dir / dir not writable
                    try:
                        shutil.copy(absPathBitmap, destDir)
                        absPathBitmap = screenshotDirBitmap
                    except IOError:
                        pass # cannot copy bitmap

                else:
                    absPathBitmap = screenshotDirBitmap

            loggerSelf.logCall(img=absPathBitmap)
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            if len(retval) == 0:
                loggerSelf.logReturn("not found in", img=screenshotObj, tip=origMethod.func_name)
            else:
                foundItems = retval
                screenshotFilename = screenshotObj.filename()
                highlightFilename = loggerSelf.highlightFilename(screenshotFilename)
                eyenfinger.drawIcon(screenshotFilename, highlightFilename, foundItems[0]._bitmap, [i.bbox() for i in foundItems])
                loggerSelf.logReturn([str(quiItem) for quiItem in retval], img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name, imgTip=screenshotObj._logCallReturnValue)
            return retval
        return findItemsByBitmapWRAP

    def findItemsByOcrLogger(loggerSelf, origMethod, screenshotObj):
        def findItemsByOcrWRAP(*args, **kwargs):
            loggerSelf.logCall()
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            if len(retval) == 0:
                loggerSelf.logReturn("not found in words " + str(screenshotObj.dumpOcrWords()),
                                     img=screenshotObj, tip=origMethod.func_name)
            else:
                foundItem = retval[0]
                screenshotFilename = screenshotObj.filename()
                highlightFilename = loggerSelf.highlightFilename(screenshotFilename)
                eyenfinger.drawIcon(screenshotFilename, highlightFilename, args[0], foundItem.bbox())
                for appearance, foundItem in enumerate(retval[1:42]):
                    eyenfinger.drawIcon(highlightFilename, highlightFilename, str(appearance+1) + ": " + args[0], foundItem.bbox())
                loggerSelf.logReturn([str(retval[0])], img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name, imgTip=screenshotObj._logCallReturnValue)
            return retval
        return findItemsByOcrWRAP

    def relFilePath(self, fileOrDirName, fileLikeObj):
        if hasattr(fileLikeObj, "name"):
            referenceDir = os.path.dirname(fileLikeObj.name)
        else:
            return fileOrDirName # keep it absolute if there's no reference
        return os.path.relpath(fileOrDirName, referenceDir)

    def imgToHtml(self, img, width="", imgTip="", imgClass=""):
        if imgClass: imgClassAttr = 'class="%s" ' % (imgClass,)
        else: imgClassAttr = ""

        if isinstance(img, Screenshot):
            imgHtmlName = self.relFilePath(img.filename(), self._outFileObj)
            imgHtml = '<tr><td></td><td><img %stitle="%s" src="%s" width="%s" alt="%s" /></td></tr>' % (
                imgClassAttr,
                "%s refreshScreenshot() at %s:%s" % img._logCallReturnValue,
                imgHtmlName,
                self._screenshotWidth,
                imgHtmlName)
        elif img:
            if width: width = 'width="%s"' % (width,)
            if type(imgTip) == tuple and len(imgTip) == 3:
                imgTip = 'title="%s refreshScreenshot() at %s:%s"' % imgTip
            else:
                imgTip = 'title="%s"' % (imgTip,)
            imgHtmlName = self.relFilePath(img, self._outFileObj)
            imgHtml = '<tr><td></td><td><img %s%s src="%s" %s alt="%s" /></td></tr>' % (
                imgClassAttr, imgTip, imgHtmlName, width, imgHtmlName)
        else:
            imgHtml = ""
        return imgHtml

    def highlightFilename(self, screenshotFilename):
        self._highlightCounter += 1
        retval = screenshotFilename + "." + str(self._highlightCounter).zfill(5) + ".png"
        return retval

    def changeCodeName(self, func, newName):
        c = func.func_code
        func.func_name = newName
        func.func_code = types.CodeType(
            c.co_argcount, c.co_nlocals, c.co_stacksize, c.co_flags,
            c.co_code, c.co_consts, c.co_names, c.co_varnames,
            c.co_filename, newName, c.co_firstlineno, c.co_lnotab, c.co_freevars)

class ConnectionError(Exception): pass
