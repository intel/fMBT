# fMBT, free Model Based Testing tool
# Copyright (c) 2013, Intel Corporation.
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

import cgi
import datetime
import inspect
import os
import shutil
import sys
import time
import traceback
import types

import eyenfinger
import fmbt

_OCRPREPROCESS =  [
    '-sharpen 5 -filter Mitchell %(zoom)s -sharpen 5 -level 60%%,60%%,3.0 -sharpen 5',
    '-sharpen 5 -level 90%%,100%%,3.0 -filter Mitchell -sharpen 5'
    ]

def _fmbtLog(msg):
    fmbt.fmbtlog("fmbtandroid: %s" % (msg,))

def _filenameTimestamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")

def _bitmapKwArgs(colorMatch=None, opacityLimit=None, area=None):
    bitmapKwArgs = {}
    if colorMatch != None: bitmapKwArgs['colorMatch'] = colorMatch
    if opacityLimit != None: bitmapKwArgs['opacityLimit'] = opacityLimit
    if area != None: bitmapKwArgs['area'] = area
    return bitmapKwArgs

def _bitmapPathSolver(rootDirForRelativePaths, bitmapPath):
    def _solver(bitmap, checkReadable=True):
        if bitmap.startswith("/"):
            path = [os.path.dirname(bitmap)]
            bitmap = os.path.basename(bitmap)
        else:
            path = []

            for singleDir in bitmapPath.split(":"):
                if not singleDir.startswith("/"):
                    path.append(os.path.join(rootDirForRelativePaths, singleDir))
                else:
                    path.append(singleDir)

        for singleDir in path:
            retval = os.path.join(singleDir, bitmap)
            if not checkReadable or os.access(retval, os.R_OK):
                break

        if checkReadable and not os.access(retval, os.R_OK):
            raise ValueError('Bitmap "%s" not readable in bitmapPath %s' % (bitmap, ':'.join(path)))
        return retval
    return _solver

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
        raise NotImplementedError('sendPress("%s") needed but not implemented.' % (keyName,))
    def sendKeyDown(self, keyName):
        raise NotImplementedError('sendKeyDown("%s") needed but not implemented.' % (keyName,))
    def sendKeyUp(self, keyName):
        raise NotImplementedError('sendKeyUp("%s") needed but not implemented.' % (keyName,))
    def sendTap(self, x, y):
        raise NotImplementedError('sendTap(%d, %d) needed but not implemented.' % (x, y))
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
    def target(self):
        """
        Returns a string that is unique to each test target. For
        instance, Android device serial number.
        """
        return "GUITestConnectionTarget"

class GUITestInterface(object):
    def __init__(self):
        self._bitmapPath = ""
        self._bitmapPathRootForRelativePaths = ""
        self._conn = None
        self._lastScreenshot = None
        self._longPressHoldTime = 2.0
        self._longTapHoldTime = 2.0
        self._screenshotDir = None
        self._screenshotDirDefault = "screenshots"
        self._screenSize = None
        self._visualLog = None
        self._visualLogFileObj = None

    def bitmapPath(self):
        """
        Returns bitmapPath from which bitmaps are searched for.
        """
        return self._bitmapPath

    def bitmapPathRoot(self):
        """
        Returns the path that prefixes all relative directories in
        bitmapPath.
        """
        return self._bitmapPathRootForRelativePaths

    def close(self):
        self._lastScreenshot = None
        if self._visualLog:
            self._visualLog.close()
            if self._visualLogFileObj:
                self._visualLogFileObj.close()
            self._visualLog = None

    def connection(self):
        """
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

        delayBetweenMoves (float, optional):
                seconds to wait when moving between points when
                dragging.

        delayAfterMoves (float, optional):
                seconds to wait after dragging, before raising
                fingertip.

        movePoints (integer, optional):
                the number of intermediate move points between end
                points of the line.

        Returns True on success, False if sending input failed.
        """
        x1, y1 = self.intCoords((x1, y1))
        x2, y2 = self.intCoords((x2, y2))
        if not self._conn.sendTouchDown(x1, y1): return False
        if delayBeforeMoves > 0:
            time.sleep(delayBeforeMoves)
        else:
            time.sleep(delayBetweenMoves)
        for i in xrange(0, movePoints):
            nx = x1 + int(round(((x2 - x1) / float(movePoints+1)) * (i+1)))
            ny = y1 + int(round(((y2 - y1) / float(movePoints+1)) * (i+1)))
            if not self._conn.sendTouchMove(nx, ny): return False
            time.sleep(delayBetweenMoves)
        if delayAfterMoves > 0:
            self._conn.sendTouchMove(x2, y2)
            time.sleep(delayAfterMoves)
        if self._conn.sendTouchUp(x2, y2): return True
        return False

    def enableVisualLog(self, filenameOrObj,
                        screenshotWidth="240", thumbnailWidth="",
                        timeFormat="%s.%f", delayedDrawing=False):
        """
        Start writing visual HTML log on this device object.

        Parameters:

          filenameOrObj (string or a file object)
                  The file to which the log is written.

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
        self._visualLog = _VisualLog(self, outFileObj, screenshotWidth, thumbnailWidth, timeFormat, delayedDrawing)

    def intCoords(self, (x, y)):
        """
        Convert floating point coordinate values in range [0.0, 1.0] to
        screen coordinates.
        """
        width, height = self.screenSize()
        if 0 <= x <= 1 and type(x) == float: x = x * width
        if 0 <= y <= 1 and type(y) == float: y = y * height
        return (int(round(x)), int(round(y)))

    def pressKey(self, keyName, long=False, hold=0.0):
        """
        Press a key.

        Parameters:

          keyName (string):
                  the name of the key, like KEYCODE_HOME.

          long (boolean, optional):
                  if True, press the key for long time.

          hold (float, optional):
                  time in seconds to hold the key down.
        """
        if not keyName.upper().startswith("KEYCODE_"):
            keyName = "KEYCODE_" + keyName
        keyName = keyName.upper()
        if long and hold == 0.0:
            hold = self._longPressHoldTime
        if hold > 0.0:
            try:
                assert self._conn.sendKeyDown(keyName)
                time.sleep(hold)
                assert self._conn.sendKeyUp(keyName)
            except AssertionError:
                return False
            return True
        return self._conn.sendPress(keyName)

    def refreshScreenshot(self, forcedScreenshot=None):
        """
        Takes new screenshot and updates the latest screenshot object.

        Parameters:

          forcedScreenshot (Screenshot or string, optional):
                  use given screenshot object or image file, do not
                  take new screenshot.

        Returns new latest Screenshot object.
        """
        if forcedScreenshot != None:
            if type(forcedScreenshot) == str:
                self._lastScreenshot = Screenshot(
                    screenshotFile=forcedScreenshot,
                    pathSolver=_bitmapPathSolver(self._bitmapPathRootForRelativePaths, self._bitmapPath))
            else:
                self._lastScreenshot = forcedScreenshot
        else:
            if self.screenshotDir() == None:
                self.setScreenshotDir(self._screenshotDirDefault)
            screenshotFile = self.screenshotDir() + os.sep + _filenameTimestamp() + "-" + self._conn.target() + '.png'
            if self._conn.recvScreenshot(screenshotFile):
                self._lastScreenshot = Screenshot(
                    screenshotFile=screenshotFile,
                    pathSolver=_bitmapPathSolver(self._bitmapPathRootForRelativePaths, self._bitmapPath))
            else:
                self._lastScreenshot = None
        return self._lastScreenshot

    def screenshot(self):
        """
        Returns the latest Screenshot object.

        Use refreshScreenshot() to get a new screenshot.
        """
        return self._lastScreenshot

    def screenshotDir(self):
        return self._screenshotDir

    def screenSize(self):
        """
        Returns screen size in pixels in tuple (width, height).
        """
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
        Set new bitmapPath.

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
        self._bitmapPath = bitmapPath
        if rootForRelativePaths != None:
            self._bitmapPathRootForRelativePaths = rootForRelativePaths

    def setConnection(self, conn):
        """
        Set the connection object that performs actions on real target.

        Parameters:

          conn (GUITestConnection object):
                  The connection to be used.
        """
        self._conn = conn

    def setScreenshotDir(self, screenshotDir):
        self._screenshotDir = screenshotDir
        if not os.path.isdir(self.screenshotDir()):
            try:
                os.makedirs(self.screenshotDir())
            except Exception, e:
                _fmbtLog('creating directory "%s" for screenshots failed: %s' % (self.screenshotDir(), e))
                raise

    def swipe(self, (x, y), direction, **dragKwArgs):
        """
        swipe starting from coordinates (x, y) to direction ("n", "s",
        "e" or "w"). Swipe ends to the edge of the screen.

        Coordinates and keyword arguments are the same as for the drag
        function.

        Returns True on success, False if sending input failed.
        """
        d = direction.lower()
        if d in ["n", "north"]: x2, y2 = self.intCoords((x, 0.0))
        elif d in ["s", "south"]: x2, y2 = self.intCoords((x, 1.0))
        elif d in ["e", "east"]: x2, y2 = self.intCoords((1.0, y))
        elif d in ["w", "west"]: x2, y2 = self.intCoords((0.0, y))
        else:
            msg = 'Illegal direction "%s"' % (direction,)
            raise Exception(msg)
        return self.drag((x, y), (x2, y2), **dragKwArgs)

    def swipeBitmap(self, bitmap, direction, colorMatch=None, opacityLimit=None, area=None, **dragKwArgs):
        """
        swipe starting from bitmap to direction ("n", "s", "e", or
        "w"). Swipe ends to the edge of the screen.

        Parameters:

          bitmap (string)
                  bitmap from which swipe starts

          direction (string)
                  "n", "s", "e" or "w"

          colorMatch, opacityLimit, area (optional)
                  refer to verifyBitmap documentation.

          delayBeforeMoves, delayBetweenMoves, delayAfterMoves,
          movePoints
                  refer to drag documentation.

        Returns True on success, False if sending input failed.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByBitmap(bitmap, **_bitmapKwArgs(colorMatch, opacityLimit, area))
        if len(items) == 0:
            return False
        return self.swipeItem(items[0], direction, **dragKwArgs)

    def swipeItem(self, viewItem, direction, **dragKwArgs):
        """
        swipe starting from viewItem to direction ("n", "s", "e" or
        "w"). Swipe ends to the edge of the screen.

        Keyword arguments are the same as for the drag function.

        Returns True on success, False if sending input failed.
        """
        return self.swipe(viewItem.coords(), direction, **dragKwArgs)

    def tap(self, (x, y), long=False, hold=0.0):
        """
        Tap screen on coordinates (x, y).

        Parameters:

          coordinates (floats in range [0.0, 1.0] or integers):
                  floating point coordinates in range [0.0, 1.0] are
                  scaled to full screen width and height, others are
                  handled as absolute coordinate values.

          long (boolean, optional):
                  if True, touch the screen for a long time.

          hold (float, optional):
                  time in seconds to touch the screen.

        Returns True if successful, otherwise False.
        """
        x, y = self.intCoords((x, y))
        if long and hold == 0.0:
            hold = self._longTapHoldTime
        if hold > 0.0:
            try:
                assert self._conn.sendTouchDown(x, y)
                time.sleep(hold)
                assert self._conn.sendTouchUp(x, y)
            except AssertionError:
                return False
            return True
        else:
            return self._conn.sendTap(x, y)

    def tapBitmap(self, bitmap, colorMatch=None, opacityLimit=None, area=None, **tapKwArgs):
        """
        Find a bitmap from the latest screenshot, and tap it.

        Parameters:

          bitmap (string):
                  filename of the bitmap to be tapped.

          colorMatch, opacityLimit, area (optional):
                  refer to verifyBitmap documentation.

          tapPos (pair of floats (x,y)):
                  refer to tapItem documentation.

          long, hold (optional):
                  refer to tap documentation.

        Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByBitmap(bitmap, **_bitmapKwArgs(colorMatch, opacityLimit, area))
        if len(items) == 0:
            return False
        return self.tapItem(items[0], **tapKwArgs)

    def tapItem(self, viewItem, **tapKwArgs):
        """
        Tap the center point of viewItem.

        Parameters:

          viewItem (GUIItem object):
                  item to be tapped, possibly returned by
                  findItemsBy... methods in Screenshot or View.

          tapPos (pair of floats (x,y)):
                  position to tap, relational to the bitmap.
                  (0.0, 0.0) is the top-left corner,
                  (1.0, 0.0) is the top-right corner,
                  (1.0, 1.0) is the lower-right corner.
                  Values < 0 and > 1 tap coordinates outside the item.

          long, hold (optional):
                  refer to tap documentation.
        """
        if "tapPos" in tapKwArgs:
            posX, posY = tapKwArgs["tapPos"]
            del tapKwArgs["tapPos"]
            x1, y1, x2, y2 = viewItem.bbox()
            tapCoords = (x1 + (x2-x1) * posX,
                         y1 + (y2-y1) * posY)
        else:
            tapCoords = viewItem.coords()
        return self.tap(tapCoords, **tapKwArgs)

    def tapOcrText(self, word, match=1.0, preprocess=None, area=(0, 0, 1.0, 1.0), **tapKwArgs):
        """
        Find the given word from the latest screenshot using OCR, and
        tap it.

        Parameters:

          word (string):
                  the word to be tapped.

          match (float, optional):
                  minimum match score in range [0.0, 1.0].
                  The default is 1.0 (exact match).

          preprocess (string, optional):
                  preprocess filter to be used in OCR for better
                  result. Refer to eyenfinger.autoconfigure to search
                  for a good one.

          area ((left, top, right, bottom), optional):
                  search from the given area only. Left, top
                  right and bottom are either absolute coordinates
                  (integers) or floats in range [0.0, 1.0]. In the
                  latter case they are scaled to screenshot
                  dimensions. The default is (0.0, 0.0, 1.0, 1.0),
                  that is, search everywhere in the screenshot.

          long, hold (optional):
                  refer to tap documentation.

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        items = self._lastScreenshot.findItemsByOcr(word, match=match, preprocess=preprocess, area=area)
        if len(items) == 0: return False
        return self.tapItem(items[0], **tapKwArgs)

    def type(self, text):
        """
        Type text.
        """
        return self._conn.sendType(text)

    def verifyOcrText(self, word, match=1.0, preprocess=None, area=(0, 0, 1.0, 1.0)):
        """
        Verify using OCR that the last screenshot contains the given word.

        Parameters:

          word (string):
                  the word to be searched for.

          match (float, optional):
                  minimum match score in range [0.0, 1.0].
                  The default is 1.0 (exact match).

          preprocess (string, optional):
                  preprocess filter to be used in OCR for better
                  result. Refer to eyenfinger.autoconfigure to search
                  for a good one.

          area ((left, top, right, bottom), optional):
                  search from the given area only. Left, top
                  right and bottom are either absolute coordinates
                  (integers) or floats in range [0.0, 1.0]. In the
                  latter case they are scaled to screenshot
                  dimensions. The default is (0.0, 0.0, 1.0, 1.0),
                  that is, search everywhere in the screenshot.

          long, hold (optional):
                  refer to tap documentation.

          Returns True if successful, otherwise False.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        return self._lastScreenshot.findItemsByOcr(word, match=match, preprocess=preprocess, area=area) != []

    def verifyBitmap(self, bitmap, colorMatch=None, opacityLimit=None, area=None):
        """
        Verify that bitmap is present in the last screenshot.

        Parameters:

          bitmap (string):
                  filename of the bitmap file to be searched for.

          colorMatch (float, optional):
                  required color matching accuracy. The default is 1.0
                  (exact match). For instance, 0.75 requires that
                  every pixel's every RGB component value on the
                  bitmap is at least 75 % match with the value of
                  corresponding pixel's RGB component in the
                  screenshot.

          opacityLimit (float, optional):
                  threshold for comparing pixels with non-zero alpha
                  channel. 0.0 requires exact match independently of
                  the opacity. Pixels less opaque than the given
                  threshold are skipped in match comparison. The
                  default is 0.95, that is, almost any non-zero alpha
                  channel value on a pixel makes it always match to a
                  whatever color on the screenshot.

          area ((left, top, right, bottom), optional):
                  search bitmap from the given area only. Left, top
                  right and bottom are either absolute coordinates
                  (integers) or floats in range [0.0, 1.0]. In the
                  latter case they are scaled to screenshot
                  dimensions. The default is (0.0, 0.0, 1.0, 1.0),
                  that is, search everywhere in the screenshot.
        """
        assert self._lastScreenshot != None, "Screenshot required."
        if self._lastScreenshot == None:
            return False
        return self._lastScreenshot.findItemsByBitmap(bitmap, **_bitmapKwArgs(colorMatch, opacityLimit, area)) != []

    def wait(self, refreshFunc, waitFunc, waitFuncArgs=(), waitFuncKwargs={}, waitTime = 5.0, pollDelay = 1.0):
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

        Returns True if waitFunc returns True - either immediately or
        before waitTime has expired - otherwise False.
        """
        if waitFunc(*waitFuncArgs, **waitFuncKwargs):
            return True
        startTime = time.time()
        endTime = startTime + waitTime
        now = startTime
        while now < endTime:
            time.sleep(min(pollDelay, (endTime - now)))
            now = time.time()
            refreshFunc()
            if waitFunc(*waitFuncArgs, **waitFuncKwargs):
                return True
        return False

    def waitBitmap(self, bitmap, colorMatch=None, opacityLimit=None, area=None, **waitKwArgs):
        """
        Wait until bitmap appears on screen.

        Parameters:

          bitmap (string):
                  filename of the bitmap to be waited for.

          colorMatch, opacityLimit, area (optional):
                  refer to verifyBitmap documentation.

          waitTime, pollDelay (float, optional):
                  refer to wait documentation.

        Returns True if bitmap appeared within given time limit,
        otherwise False.

        Updates the last screenshot.
        """
        if not self._lastScreenshot: self.refreshScreenshot()
        return self.wait(self.refreshScreenshot,
                         self.verifyBitmap, (bitmap,), _bitmapKwArgs(colorMatch, opacityLimit, area),
                         **waitKwArgs)

    def waitOcrText(self, text, match=None, preprocess=None, area=None, **waitKwArgs):
        """
        Wait until OCR detects text on the screen.

        Parameters:

          text (string):
                  text to be waited for.

          match, preprocess (float and string, optional)
                  refer to verifyOcrText documentation.

          area ((left, top, right, bottom), optional):
                  refer to verifyOcrText documentation.

          waitTime, pollDelay (float, optional):
                  refer to wait documentation.

        Returns True if the text appeared within given time limit,
        otherwise False.

        Updates the last screenshot.
        """
        ocrKwArgs = {}
        if match != None: ocrKwArgs["match"] = match
        if preprocess != None: ocrKwArgs["preprocess"] = preprocess
        if area != None: ocrKwArgs["area"] = area
        if not self._lastScreenshot: self.refreshScreenshot()
        return self.wait(self.refreshScreenshot,
                         self.verifyOcrText, (text,), ocrKwArgs,
                         **waitKwArgs)

class Screenshot(object):
    """
    Screenshot class takes and holds a screenshot (bitmap) of device
    display, or a forced bitmap file if device connection is not given.
    """
    def __init__(self, screenshotFile=None, pathSolver=None):
        self._filename = screenshotFile
        self._pathSolver = pathSolver
        self._screenSize = eyenfinger.imageSize(self._filename)
        # The bitmap held inside screenshot object is never updated.
        # If new screenshot is taken, this screenshot object disappears.
        # => cache all search hits
        self._cache = {}
        self._ocrPreprocess = _OCRPREPROCESS
        self._ocrWords = None
        self._ocrWordsArea = None
        self._ocrWordsPreprocess = None

    def size(self):
        return self._screenSize

    def dumpOcrWords(self, preprocess=None, area=None):
        if preprocess == None: preprocess = self._ocrWordsPreprocess
        if area == None: area = self._ocrWordsArea
        self._assumeOcrWords(preprocess=preprocess, area=area)
        w = []
        for ppfilter in self._ocrWords:
            for word in self._ocrWords[ppfilter]:
                for appearance, (wid, middle, bbox) in enumerate(self._ocrWords[ppfilter][word]):
                    (x1, y1, x2, y2) = bbox
                    w.append((word, x1, y1))
        return sorted(set(w), key=lambda i:(i[2]/8, i[1]))

    def filename(self):
        return self._filename

    def findItemsByBitmap(self, bitmap, colorMatch=1.0, opacityLimit=.95, area=(0.0, 0.0, 1.0, 1.0)):
        bitmap = self._pathSolver(bitmap)
        if (bitmap, colorMatch, opacityLimit, area) in self._cache:
            return self._cache[(bitmap, colorMatch, opacityLimit, area)]
        eyenfinger.iRead(source=self._filename, ocr=False)
        try:
            score, bbox = eyenfinger.iVerifyIcon(bitmap, colorMatch=colorMatch, opacityLimit=opacityLimit, area=area)
            foundItem = GUIItem("bitmap", bbox, self._filename, bitmap=bitmap)
            self._cache[(bitmap, colorMatch, opacityLimit, area)] = [foundItem]
        except eyenfinger.BadMatch:
            self._cache[(bitmap, colorMatch, opacityLimit, area)] = []
        return self._cache[(bitmap, colorMatch, opacityLimit, area)]

    def findItemsByOcr(self, text, preprocess=None, match=1.0, area=(0, 0, 1.0, 1.0)):
        self._assumeOcrWords(preprocess=preprocess, area=area)
        for ppfilter in self._ocrWords.keys():
            try:
                eyenfinger._g_words = self._ocrWords[ppfilter]
                (score, word), bbox = eyenfinger.iVerifyWord(text, match=match)
                break
            except eyenfinger.BadMatch:
                continue
        else:
            return []
        return [GUIItem("OCR word", bbox, self._filename, ocrFind=text, ocrFound=word)]

    def save(self, fileOrDirName):
        shutil.copy(self._filename, fileOrDirName)

    def _assumeOcrWords(self, preprocess=None, area=None):
        if preprocess == None:
            preprocess = self._ocrPreprocess
        if area == None:
            area = (0, 0, 1.0, 1.0)
        if self._ocrWords == None or self._ocrWordsPreprocess != preprocess or self._ocrWordsArea != area:
            if not type(preprocess) in (list, tuple):
                preprocess = [preprocess]
            self._ocrWords = {}
            self._ocrWordsPreprocess = preprocess
            self._ocrWordsArea = area
            for ppfilter in preprocess:
                pp = ppfilter % { "zoom": "-resize %sx" % (self._screenSize[0] * 2) }
                eyenfinger.iRead(source=self._filename, ocr=True, preprocess=pp, ocrArea=area)
                self._ocrWords[ppfilter] = eyenfinger._g_words

    def __str__(self):
        return 'Screenshot(filename="%s")' % (self._filename,)

class GUIItem(object):
    """
    GUIItem holds the information of a single GUI item.
    """
    def __init__(self, name, bbox, screenshot, bitmap=None, ocrFind=None, ocrFound=None):
        self._name = name
        self._bbox = bbox
        self._bitmap = bitmap
        self._screenshot = screenshot
        self._ocrFind = ocrFound
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
            extras += ', find="%s", found="%s"' % (self._ocrFind, self._ocrFound)
        if self._screenshot:
            extras += ', screenshot="%s"' % (self._screenshot,)
        return ('GUIItem("%s", bbox=%s%s)'  % (
                self.name(), self.bbox(), extras))

class _VisualLog:
    def __init__(self, device, outFileObj,
                 screenshotWidth, thumbnailWidth,
                 timeFormat, delayedDrawing):
        self._device = device
        self._outFileObj = outFileObj
        self._testStep = -1
        self._actionName = None
        self._callDepth = 0
        self._highlightCounter = 0
        self._screenshotWidth = screenshotWidth
        self._thumbnailWidth = thumbnailWidth
        self._timeFormat = timeFormat
        eyenfinger.iSetDefaultDelayedDrawing(delayedDrawing)
        device.refreshScreenshot = self.refreshScreenshotLogger(device.refreshScreenshot)
        device.tap = self.tapLogger(device.tap)
        device.drag = self.dragLogger(device.drag)
        attrs = ['callContact', 'callNumber', 'close',
                 'loadConfig', 'platformVersion',
                 'pressAppSwitch', 'pressBack', 'pressHome',
                 'pressKey', 'pressMenu', 'pressPower',
                 'pressVolumeUp', 'pressVolumeDown',
                 'reboot', 'reconnect', 'refreshView',
                 'shell', 'shellSOE', 'smsNumber',
                 'supportsView', 'swipe',
                 'swipeBitmap', 'swipeItem', 'systemProperty',
                 'tapBitmap', 'tapId', 'tapItem', 'tapOcrText',
                 'tapText', 'topApp', 'topWindow', 'type',
                 'verifyOcrText', 'verifyText', 'verifyBitmap',
                  'waitBitmap', 'waitOcrText', 'waitText']
        for a in attrs:
            if hasattr(device, a):
                m = getattr(device, a)
                setattr(device, m.func_name, self.genericLogger(m))
        self.logHeader()
        self._blockId = 0

    def close(self):
        if self._outFileObj != None:
            html = []
            for c in xrange(self._callDepth):
                html.append('</table></tr>') # end call
            html.append('</table></div></td></tr></table></ul>') # end step
            html.append('</body></html>') # end html
            self.write('\n'.join(html))
            # File instance should be closed by the opener
            self._outFileObj = None

    def write(self, s):
        if self._outFileObj != None:
            self._outFileObj.write(s)
            self._outFileObj.flush()

    def timestamp(self, t=None):
        if t == None: t = datetime.datetime.now()
        return t.strftime(self._timeFormat)

    def epochTimestamp(self, t=None):
        if t == None: t = datetime.datetime.now()
        return t.strftime("%s.%f")

    def htmlTimestamp(self, t=None):
        if t == None: t = datetime.datetime.now()
        retval = '<div class="time" id="%s"><a id="time%s">%s</a></div>' % (
            self.epochTimestamp(t), self.epochTimestamp(t), self.timestamp(t))
        return retval

    def logBlock(self):
        ts = fmbt.getTestStep()
        an = fmbt.getActionName()
        if self._testStep != ts or self._actionName != an:
            if self._blockId != 0: self.write('</table></div></td></tr></table></ul>')
            actionHtml = '''\n\n<ul><li><table><tr><td>%s</td><td><div class="step"><a id="blockId%s" href="javascript:showHide('S%s')">%s. %s</a></div><div class="funccalls" id="S%s"><table>\n''' % (
                self.htmlTimestamp(), self._blockId, self._blockId, ts, an, self._blockId)
            self.write(actionHtml)
            self._testStep = ts
            self._actionName = an
            self._blockId += 1

    def logCall(self, img=None, width="", imgTip=""):
        self.logBlock()
        callee = inspect.currentframe().f_back.f_code.co_name[:-4] # cut "WRAP"
        argv = inspect.getargvalues(inspect.currentframe().f_back)
        calleeArgs = str(argv.locals['args']) + " " + str(argv.locals['kwargs'])
        callerFilename = inspect.currentframe().f_back.f_back.f_code.co_filename
        callerLineno = inspect.currentframe().f_back.f_back.f_lineno
        imgHtml = self.imgToHtml(img, width, imgTip)
        t = datetime.datetime.now()
        callHtml = '''
             <tr><td></td><td><table><tr>
                 <td>%s</td><td><a title="%s:%s"><div class="call">%s%s</div></a></td>
             </tr>
             %s''' % (self.htmlTimestamp(t), cgi.escape(callerFilename), callerLineno, cgi.escape(callee), cgi.escape(str(calleeArgs)), imgHtml)
        self.write(callHtml)
        self._callDepth += 1
        return (self.timestamp(t), callerFilename, callerLineno)

    def logReturn(self, retval, img=None, width="", imgTip="", tip=""):
        imgHtml = self.imgToHtml(img, width, imgTip)
        self._callDepth -= 1
        returnHtml = '''
             <tr>
                 <td>%s</td><td><div class="returnvalue"><a title="%s">== %s</a></div></td>
             </tr>%s
             </table></tr>\n''' % (self.htmlTimestamp(), tip, cgi.escape(str(retval)), imgHtml)
        self.write(returnHtml)

    def logException(self):
        einfo = sys.exc_info()
        self._callDepth -= 1
        excHtml = '''
             <tr>
                 <td>%s</td><td><div class="exception"><a title="%s">!! %s</a></div></td>
             </tr>
             </table></tr>\n''' % (self.htmlTimestamp(), cgi.escape(traceback.format_exception(*einfo)[-2].replace('"','').strip()), cgi.escape(str(traceback.format_exception_only(einfo[0], einfo[1])[0])))
        self.write(excHtml)

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
        loggerSelf.changeCodeName(origMethodWRAP, origMethod.func_code.co_name + "WRAP")
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
                loggerSelf.logReturn(retval, img=loggerSelf._device.screenshot(), tip=origMethod.func_name)
            except:
                loggerSelf.logReturn(str(retval) + " (no screenshot available)", tip=origMethod.func_name)
            return retval
        return dragWRAP

    def refreshScreenshotLogger(loggerSelf, origMethod):
        def refreshScreenshotWRAP(*args, **kwargs):
            loggerSelf._highlightCounter = 0
            logCallReturnValue = loggerSelf.logCall()
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            retval._logCallReturnValue = logCallReturnValue
            loggerSelf.logReturn(retval, img=retval, tip=origMethod.func_name)
            retval.findItemsByBitmap = loggerSelf.findItemsByBitmapLogger(retval.findItemsByBitmap, retval)
            retval.findItemsByOcr = loggerSelf.findItemsByOcrLogger(retval.findItemsByOcr, retval)
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
            loggerSelf.logCall(img=screenshotObj._pathSolver(bitmap))
            retval = loggerSelf.doCallLogException(origMethod, args, kwargs)
            if len(retval) == 0:
                loggerSelf.logReturn("not found in", img=screenshotObj, tip=origMethod.func_name)
            else:
                foundItem = retval[0]
                screenshotFilename = screenshotObj.filename()
                highlightFilename = loggerSelf.highlightFilename(screenshotFilename)
                eyenfinger.drawIcon(screenshotFilename, highlightFilename, bitmap, foundItem.bbox())
                loggerSelf.logReturn(retval, img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name, imgTip=screenshotObj._logCallReturnValue)
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
                loggerSelf.logReturn([str(retval[0])], img=highlightFilename, width=loggerSelf._screenshotWidth, tip=origMethod.func_name, imgTip=screenshotObj._logCallReturnValue)
            return retval
        return findItemsByOcrWRAP

    def imgToHtml(self, img, width="", imgTip=""):
        if isinstance(img, Screenshot):
            imgHtml = '<tr><td></td><td><img title="%s" src="%s" width="%s" alt="%s" /></td></tr>' % (
                "%s refreshScreenshot() at %s:%s" % img._logCallReturnValue,
                img.filename(),
                self._screenshotWidth,
                img.filename())
        elif img:
            if width: width = 'width="%s"' % (width,)
            if type(imgTip) == tuple and len(imgTip) == 3:
                imgTip = 'title="%s refreshScreenshot() at %s:%s"' % imgTip
            else:
                imgTip = 'title="%s"' % (imgTip,)
            imgHtml = '<tr><td></td><td><img %s src="%s" %s alt="%s" /></td></tr>' % (
                imgTip, img, width, img)
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
