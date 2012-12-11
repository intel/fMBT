# fMBT, free Model Based Testing tool
# Copyright (c) 2012, Intel Corporation.
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
eyenfinger - GUI testing library based on OCR and X event generation

Configuring low-level key presses
---------------------------------

printEventsFromFile() prints input events from Linux chosen
/dev/input/eventXX file. Example:

python -c '
import eyenfinger
eyenfinger.printEventsFromFile("/dev/input/event0")
'

Alternatively, you can use device names in /proc/bus/input/devices and
printEventsFromDevice("device name").


Configuring OCR
---------------

autoconfigure() evaluates number of preprocessing filters to give the
best result on finding given words from given image. Example:

python -c '
from eyenfinger import *
autoconfigure("screenshot.png", ["Try", "to", "find", "these", "words"])
'


evaluatePreprocessFilter() highlights words detected on given image. Example:

python -c '
from eyenfinger import *
evaluatePreprocessFilter("screenshot.png", "-sharpen 5 -resize 1600x", ["File", "View"])
'

setPreprocessFilter() sets given filter to be used when reading text from images.

Debugging
---------

iClickWord() capture parameter visualises coordinates to be clicked. Example:

python -c '
from eyenfinger import *
setPreprocessFilter("-sharpen 5 -filter Mitchell -resize 1600x -level 40%,50%,3.0")
iRead(source="screenshot.png")
iClickWord("[initial", clickPos=(-2,3), capture="highlight.png", dryRun=True)
'
"""

import time
import subprocess
import re
import math
import htmlentitydefs
import sys
import os
import tempfile
import atexit
import shutil
import ctypes
import platform
import struct

_g_preprocess = "-sharpen 5 -filter Mitchell -resize 1920x1600 -level 40%%,70%%,5.0 -sharpen 5"

_g_readImage = None

_g_origImage = None

_g_hocr = ""

_g_words = None

_g_lastWindow = None

_g_defaultClickDryRun = False
_g_defaultIconMatch = 1.0
_g_defaultIconColorMatch = 1.0
_g_defaultIconOpacityLimit = 0.0
_g_defaultReadWithOCR = True

# windowsOffsets maps window-id to (x, y) pair.
_g_windowOffsets = {None: (0,0)}
# windowsSizes maps window-id to (width, height) pair.
_g_windowSizes = {None: (0,0)}
# screenSize is a (width, height) pair.
_g_screenSize = (0, 0)

_g_tempdir = tempfile.mkdtemp(prefix="eyenfinger.%s." % (os.getpid(),))

SCREENSHOT_FILENAME = _g_tempdir + "/screenshot.png"
LOG_FILENAME = _g_tempdir + "/eyenfinger.log"

MOUSEEVENT_MOVE, MOUSEEVENT_CLICK, MOUSEEVENT_DOWN, MOUSEEVENT_UP = range(4)

# This is not complete list by any means.
# See keysymdef.h.
keys = [
    "BackSpace", "Tab", "Linefeed", "Clear", "Return", "Pause",
    "Scroll_Lock", "Sys_Req", "Escape", "Delete", "Home", "Left",
    "Up", "Right", "Down", "Prior", "Page_Up", "Next", "Page_Down",
    "End", "Begin", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8",
    "F9", "F10", "F11", "F12", "Shift_L", "Shift_R", "Control_L",
    "Control_R", "Caps_Lock", "Shift_Lock", "Meta_L", "Meta_R",
    "Alt_L", "Alt_R", "space", "exclam", "quotedbl", "numbersign",
    "dollar", "percent", "ampersand", "apostrophe", "quoteright",
    "parenleft", "parenright", "asterisk", "plus", "comma", "minus",
    "period", "slash", "0", "1", "2", "3", "4", "5", "6", "7", "8",
    "9", "colon", "semicolon", "less", "equal", "greater", "question",
    "at", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L",
    "M", "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y",
    "Z", "bracketleft", "backslash", "bracketright", "asciicircum",
    "underscore", "grave", "quoteleft", "a", "b", "c", "d", "e", "f",
    "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
    "t", "u", "v", "w", "x", "y", "z", "braceleft", "bar",
    "braceright"]

# Input keys is a dictionary
#     keyName -> (input device, keycode)
#
# Input device can be either a filename (like /dev/input/event0)
# or device name (see /proc/bus/input/devices). Keycode is a
# numeric value.
_g_inputKeys = {}

class EyenfingerError(Exception):
    pass

class BadMatch (EyenfingerError):
    pass

class BadWindowName (EyenfingerError):
    pass

class BadSourceImage(EyenfingerError):
    pass

class BadIconImage(EyenfingerError):
    pass

class NoOCRResults(EyenfingerError):
    pass

try:
    import fmbt
    def _log(msg):
        fmbt.adapterlog("eyenfinger: %s" % (msg,))

except ImportError:
    def _log(msg):
        file(LOG_FILENAME, "a").write("%13.2f %s\n" %
                                      (time.time(), msg))


try:
    import ctypes
    _libpath = ["",
                "." + os.path.sep,
                "." + os.path.sep + ".libs" + os.path.sep,
                os.path.dirname(__file__) + os.path.sep,
                os.path.dirname(__file__) + os.path.sep + ".libs" + os.path.sep]
    for _dirname in _libpath:
        try:
            eye4graphics = ctypes.CDLL(_dirname + "eye4graphics.so")
            break
        except: pass
    else:
        raise ImportError("%s cannot load eye4graphics.so" % (__file__,))

    class Bbox(ctypes.Structure):
        _fields_ = [("left", ctypes.c_int32),
                    ("top", ctypes.c_int32),
                    ("right", ctypes.c_int32),
                    ("bottom", ctypes.c_int32),
                    ("error", ctypes.c_int32)]
except Exception, e:
    Bbox = None
    eye4graphics = None
    _log('Loading icon recognition library failed: "%s".' % (e,))

if platform.architecture()[0] == '64bit':
    _TimeType = ctypes.c_int64
else:
    _TimeType = ctypes.c_int

# See struct input_event in /usr/include/linux/input.h
class _InputEvent(ctypes.Structure):
    _fields_ = [('time', _TimeType),
                ('suseconds', _TimeType),
                ('type', ctypes.c_uint16),
                ('code', ctypes.c_uint16),
                ('value', ctypes.c_int32)]
_InputEventStructSpec = 'QQHHi'

_EV_KEY = 0x01

def printEventsFromFile(filename):
    fd = os.open(filename, os.O_RDONLY)

    try:
        while 1:
            evString = os.read(fd, ctypes.sizeof(_InputEvent))
            if not evString: break
            print "time: %8s, susc: %8s, type: %8s, keyCode:%8s, value:%8s" % \
                struct.unpack(_InputEventStructSpec, evString)
    finally:
        os.close(fd)

def printEventsFromDevice(deviceName):
    devices = dict(listInputDevices())
    if not deviceName in devices:
        error('Unknown device "%s". Available devices: %s' %
              (deviceName, sorted(devices.keys())))
    else:
        printEventsFromFile(devices[deviceName])

def _exitHandler():
    shutil.rmtree(_g_tempdir, ignore_errors=True)
atexit.register(_exitHandler)

def _runcmd(cmd):
    _log("runcmd: " + cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.stdout.read()
    _log("stdout: " + output)
    _log("stderr: " + p.stderr.read())
    return p.wait(), output

def setPreprocessFilter(preprocess):
    global _g_preprocess
    _g_preprocess = preprocess

def iSetDefaultClickDryRun(dryRun):
    """
    Set the default value for optional dryRun parameter for iClick*
    functions.
    """
    global _g_defaultClickDryRun
    _g_defaultClickDryRun = dryRun

def iSetDefaultIconMatch(match):
    """
    Set the default icon matching value, ranging from 0 to 1. The
    value will be used in iClickIcon and iVerifyIcon, if the optional
    match parameter is omitted. Value 1.0 will use pixel-perfect
    matching (the default), values below 1.0 will use fuzzy matching.

    Fuzzy matching is EXPERIMENTAL.
    """
    global _g_defaultIconMatch
    _g_defaultIconMatch = match

def iSetDefaultIconColorMatch(colorMatch):
    """
    Set the default color matching value, ranging from 0 to 1. When
    using pixel-perfect matching this will allow given error in pixel
    colors.

    For instance, when comparing 24 bit RGB images, value 0.97 will
    allow 256 - int(256 * .97) = 8 difference on each color channel.
    """
    global _g_defaultIconColorMatch
    _g_defaultIconColorMatch = colorMatch

def iSetDefaultIconOpacityLimit(opacityLimit):
    """
    Set the default minimum opacity for pixels to be matched. Defaults
    to 0.0, all pixels are matched independently of their opacity.
    """
    global _g_defaultIconOpacityLimit
    _g_defaultIconOpacityLimit = opacityLimit

def iSetDefaultReadWithOCR(ocr):
    """
    Set the default for using OCR when reading images or windows.
    """
    global _g_defaultReadWithOCR
    _g_defaultReadWithOCR = ocr

def iSetInputKeys(inputKeys):
    """
    Set dictionary that maps key names to pairs (input device,
    keycode) that will be used when synthesizing low-level input key
    presses with iInputKey(keyName).
    """
    global _g_inputKeys
    _g_inputKeys = inputKeys

def screenSize():
    """
    Returns the size of the screen as a pair (width, height).
    """
    return _g_screenSize

def windowSize():
    """
    Returns the size of the window as a pair (width, height).
    """
    return _g_windowSizes[_g_lastWindow]

def windowXY():
    """
    Returns screen coordinates of the top-left corner of the window as
    a pair (x, y).
    """
    return _g_windowOffsets[_g_lastWindow]

def iRead(windowId = None, source = None, preprocess = None, ocr=None, capture=None):
    """
    Read the contents of the given window or other source. If neither
    of windowId or source is given, reads the contents of active
    window. iClickWord and iVerifyWord can be used after reading with
    OCR.

    Parameters:
        windowId     id (0x....) or the title of the window to be read.
                     Defaults to None.

        source       name of the file to be read, for instance a screen
                     capture. Defaults to None.

        preprocess   preprocess specification to override the default
                     that is set using setPreprocessFilter. Defaults
                     to None. Set to "" to disable preprocessing before
                     OCR.

        ocr          words will be read using OCR if True
                     (the default). Read object can be used with
                     iClickIcon and iVerifyIcon without OCR, too.

        capture      save image with read words highlighted to this
                     file. Default: None (nothing is saved).

    Returns list of words detected by OCR from the read object.
    """

    global _g_hocr
    global _g_lastWindow
    global _g_words
    global _g_readImage
    global _g_origImage

    _g_words = None
    _g_readImage = None
    _g_origImage = None

    if ocr == None:
        ocr = _g_defaultReadWithOCR

    if not source:
        iUseWindow(windowId)

        # take a screenshot
        _runcmd("xwd -root -screen -out %s.xwd && convert %s.xwd -crop %sx%s+%s+%s '%s'" %
               (SCREENSHOT_FILENAME, SCREENSHOT_FILENAME,
                _g_windowSizes[_g_lastWindow][0], _g_windowSizes[_g_lastWindow][1],
                _g_windowOffsets[_g_lastWindow][0], _g_windowOffsets[_g_lastWindow][1],
                SCREENSHOT_FILENAME))
        source = SCREENSHOT_FILENAME
    else:
        iUseImageAsWindow(source)
    _g_origImage = source

    if not ocr:
        if capture:
            drawWords(_g_origImage, capture, [], [])
        return []

    if preprocess == None:
        preprocess = _g_preprocess

    # convert to text
    _g_readImage = _g_origImage + "-pp.png"
    _, _g_hocr = _runcmd("convert %s %s %s && tesseract %s %s -l eng hocr" % (
            _g_origImage, preprocess, _g_readImage,
            _g_readImage, SCREENSHOT_FILENAME))

    # store every word and its coordinates
    _g_words = _hocr2words(file(SCREENSHOT_FILENAME + ".html").read())

    # convert word coordinates to the unscaled pixmap
    orig_width, orig_height = _g_windowSizes[_g_lastWindow][0], _g_windowSizes[_g_lastWindow][1]

    scaled_width, scaled_height = re.findall('bbox 0 0 ([0-9]+)\s*([0-9]+)', _runcmd("grep ocr_page %s.html | head -n 1" % (SCREENSHOT_FILENAME,))[1])[0]
    scaled_width, scaled_height = float(scaled_width), float(scaled_height)

    for word in sorted(_g_words.keys()):
        for appearance, (wordid, middle, bbox) in enumerate(_g_words[word]):
            _g_words[word][appearance] = \
                (wordid,
                 (int(middle[0]/scaled_width * orig_width),
                  int(middle[1]/scaled_height * orig_height)),
                 (int(bbox[0]/scaled_width * orig_width),
                  int(bbox[1]/scaled_height * orig_height),
                  int(bbox[2]/scaled_width * orig_width),
                  int(bbox[3]/scaled_height * orig_height)))
            _log('found "' + word + '": (' + str(bbox[0]) + ', ' + str(bbox[1]) + ')')
    if capture:
        drawWords(_g_origImage, capture, _g_words, _g_words)
    return sorted(_g_words.keys())


def iVerifyWord(word, match=0.33, appearance=1, capture=None):
    """
    Verify that word can be found from previously iRead() image.

    Parameters:
        word         word that should be checked

        appearance   if word appears many times, appearance to
                     be clicked. Defaults to the first one.

        match        minimum matching score

        capture      save image with verified word highlighted
                     to this file. Default: None (nothing is saved).

    Returns pair: ((score, matchingWord), (left, top, right, bottom)), where

        score        score of found match (1.0 for perfect match)

        matchingWord corresponding word detected by OCR

        (left, top, right, bottom)
                     bounding box of the word in read image

    Throws BadMatch error if word is not found.

    Throws NoOCRResults error if there are OCR results available
    on the current screen.
    """
    if _g_words == None:
        raise NoOCRResults('iRead has not been called with ocr=True')

    score, matching_word = findWord(word)

    if capture:
        drawWords(_g_origImage, capture, [word], _g_words)

    if score < match:
        raise BadMatch('No matching word for "%s". The best candidate "%s" with score %.2f, required %.2f' %
                            (word, matching_word, score, match))
    return ((score, matching_word), _g_words[matching_word][appearance-1][2])


def iVerifyIcon(iconFilename, match=None, colorMatch=None, opacityLimit=None, capture=None, _origin="iVerifyIcon"):
    """
    Verify that icon can be found from previously iRead() image.

    Parameters:

        iconFilename   name of the icon file to be searched for

        match          minimum matching score between 0 and 1.0,
                       1.0 is perfect match (default)

        colorMatch     1.0 (default) requires exact color match. Value
                       below 1.0 defines maximum allowed color
                       difference. See iSetDefaultIconColorMatch.

        opacityLimit   0.0 (default) requires exact color values
                       independently of opacity. If lower than 1.0,
                       pixel less opaque than given value are skipped
                       in pixel perfect comparisons.

        capture        save image with verified icon highlighted
                       to this file. Default: None (nothing is saved).

    Returns pair: (score, (left, top, right, bottom)), where

        score          score of found match (1.0 for perfect match)

        (left, top, right, bottom)
                       bounding box of found icon

    Throws BadMatch error if icon is not found.
    """
    if not eye4graphics:
        _log('ERROR: %s("%s") called, but eye4graphics not loaded.' % (_origin, iconFilename))
        raise EyenfingerError("eye4graphics not available")
    if not _g_origImage:
        _log('ERROR %s("%s") called, but source not defined (iRead not called).' % (_origin, iconFilename))
        raise BadSourceImage("Source image not defined, cannot search for an icon.")
    if not (os.path.isfile(iconFilename) and os.access(iconFilename, os.R_OK)):
        _log('ERROR %s("%s") called, but the icon file is not readable.' % (_origin, iconFilename))
        raise BadIconImage('Icon "%s" is not readable.' % (iconFilename,))
    if match == None:
        match = _g_defaultIconMatch
    if match > 1.0:
        _log('ERROR %s("%s"): invalid match value, must be below 1.0. ' % (_origin, iconFilename,))
        raise ValueError("invalid match value: %s, should be 0 <= match <= 1.0" % (match,))
    if colorMatch == None:
        colorMatch = _g_defaultIconColorMatch
    if not 0.0 <= colorMatch <= 1.0:
        _log('ERROR %s("%s"): invalid colorMatch value, must be between 0 and 1. ' % (_origin, iconFilename,))
        raise ValueError("invalid colorMatch value: %s, should be 0 <= colorMatch <= 1.0" % (colorMatch,))
    if opacityLimit == None:
        opacityLimit = _g_defaultIconOpacityLimit
    if not 0.0 <= opacityLimit <= 1.0:
        _log('ERROR %s("%s"): invalid opacityLimit value, must be between 0 and 1. ' % (_origin, iconFilename,))
        raise ValueError("invalid opacityLimit value: %s, should be 0 <= opacityLimit <= 1.0" % (opacityLimit,))

    struct_bbox = Bbox(0,0,0,0,0)
    threshold = int((1.0-match)*20)
    err = eye4graphics.findSingleIcon(ctypes.byref(struct_bbox),
                                      _g_origImage, iconFilename, threshold,
                                      ctypes.c_double(colorMatch),
                                      ctypes.c_double(opacityLimit))
    bbox = (int(struct_bbox.left), int(struct_bbox.top),
            int(struct_bbox.right), int(struct_bbox.bottom))

    if err == -1 or err == -2:
        msg = '%s: "%s" not found, match=%.2f, threshold=%s, closest threshold %s.' % (
            _origin, iconFilename, match, threshold, int(struct_bbox.error))
        if capture:
            drawIcon(_g_origImage, capture, iconFilename, bbox, 'red')
        _log(msg)
        raise BadMatch(msg)
    elif err != 0:
        _log("%s: findSingleIcon returned %s" % (_origin, err,))
        raise BadMatch("%s not found, findSingleIcon returned %s." % (iconFilename, err))
    if threshold > 0:
        score = (threshold - int(struct_bbox.error)) / float(threshold)
    else:
        score = 1.0

    if capture:
        drawIcon(_g_origImage, capture, iconFilename, bbox)

    return (score, bbox)


def iClickIcon(iconFilename, clickPos=(0.5,0.5), match=None,
               colorMatch=None, opacityLimit=None,
               mouseButton=1, mouseEvent=MOUSEEVENT_CLICK, dryRun=None, capture=None):
    """
    Click coordinates relative to the given icon in previously iRead() image.

    Parameters:
        iconFilename read icon from this file

        clickPos     position to be clicked,
                     relative to word top-left corner of the bounding
                     box around the word. X and Y units are relative
                     to width and height of the box.  (0,0) is the
                     top-left corner, (1,1) is bottom-right corner,
                     (0.5, 0.5) is the middle point (default).
                     Values below 0 or greater than 1 click outside
                     the bounding box.

        match        1.0 (default) requires exact match. Value below 1.0
                     defines minimum required score for fuzzy matching
                     (EXPERIMENTAL). See iSetDefaultIconMatch.

        colorMatch   1.0 (default) requires exact color match. Value
                     below 1.0 defines maximum allowed color
                     difference. See iSetDefaultIconColorMatch.

        opacityLimit 0.0 (default) requires exact color values
                     independently of opacity. If lower than 1.0,
                     pixel less opaque than given value are skipped
                     in pixel perfect comparisons.

        mouseButton  mouse button to be synthesized on the event, default is 1.

        mouseEvent   event to be synthesized, the default is MOUSEEVENT_CLICK,
                     others: MOUSEEVENT_MOVE, MOUSEEVENT_DOWN, MOUSEEVENT_UP.

        dryRun       if True, does not synthesize events. Still returns
                     coordinates of the clicked position and illustrates
                     the clicked position on the capture image if
                     given.

        capture      name of file where image of highlighted icon and
                     clicked point are saved.

    Returns pair (score, (clickedX, clickedY)), where

        score        score of found match (1.0 for perfect match)

        (clickedX, clickedY)
                     X and Y coordinates of clicked position on the
                     screen.

    Throws BadMatch error if could not find a matching word.
    """
    score, bbox = iVerifyIcon(iconFilename, match=match,
                              colorMatch=colorMatch, opacityLimit=opacityLimit,
                              capture=capture, _origin="iClickIcon")

    clickedXY = iClickBox(bbox, clickPos, mouseButton, mouseEvent, dryRun,
                          capture, _captureText = iconFilename)

    return (score, clickedXY)


def iClickWord(word, appearance=1, clickPos=(0.5,0.5), match=0.33,
               mouseButton=1, mouseEvent=1, dryRun=None, capture=None):
    """
    Click coordinates relative to the given word in previously iRead() image.

    Parameters:

        word         word that should be clicked

        appearance   if word appears many times, appearance to
                     be clicked. Defaults to the first one.

        clickPos     position to be clicked,
                     relative to word top-left corner of the bounding
                     box around the word. X and Y units are relative
                     to width and height of the box.  (0,0) is the
                     top-left corner, (1,1) is bottom-right corner,
                     (0.5, 0.5) is the middle point (default).
                     Values below 0 or greater than 1 click outside
                     the bounding box.

        capture      name of file where image of highlighted word and
                     clicked point are saved.

    Returns pair: ((score, matchingWord), (clickedX, clickedY)), where

        score        score of found match (1.0 for perfect match)

        matchingWord corresponding word detected by OCR

        (clickedX, clickedY)
                     X and Y coordinates of clicked position on the
                     screen.

    Throws BadMatch error if could not find a matching word.

    Throws NoOCRResults error if there are OCR results available
    on the current screen.
    """
    (score, matching_word), bbox = iVerifyWord(word, appearance=appearance, match=match, capture=False)

    clickedX, clickedY = iClickBox(bbox, clickPos, mouseButton, mouseEvent, dryRun, capture=False)

    windowId = _g_lastWindow

    _log('iClickWord("%s"): word "%s", match %.2f, bbox %s, window offset %s, click %s' %
         (word, matching_word, score,
          bbox, _g_windowOffsets[windowId],
          (clickedX, clickedY)))

    if capture:
        drawWords(_g_origImage, capture, [word], _g_words)
        drawClickedPoint(capture, capture, (clickedX, clickedY))

    return ((score, matching_word), (clickedX, clickedY))


def iClickBox((left, top, right, bottom), clickPos=(0.5, 0.5),
              mouseButton=1, mouseEvent=1, dryRun=None,
              capture=None, _captureText=None):
    """
    Click coordinates relative to the given bounding box, default is
    in the middle of the box.

    Parameters:

        (left, top, right, bottom)
                     coordinates of the box inside the window.
                     (0, 0) is the top-left corner of the window.

        clickPos     (offsetX, offsetY) position to be clicked,
                     relative to the given box. (0, 0) is the
                     top-left, and (1.0, 1.0) is the lower-right
                     corner of the box.  The default is (0.5, 0.5),
                     that is, the middle point of the box. Values
                     smaller than 0 and bigger than 1 are allowed,
                     too.

        mouseButton  mouse button to be synthesized on the event, default is 1.

        mouseEvent   event to be synthesized, the default is MOUSEEVENT_CLICK,
                     others: MOUSEEVENT_MOVE, MOUSEEVENT_DOWN, MOUSEEVENT_UP.

        dryRun       if True, does not synthesize events. Still returns
                     coordinates of the clicked position and illustrates
                     the clicked position on the capture image if
                     given.

        capture      name of file where the last screenshot with
                     clicked point highlighted is saved. The default
                     is None (nothing is saved).

    Returns pair (clickedX, clickedY)
                     X and Y coordinates of clicked position on the
                     screen.

    """
    clickWinX = int(left + clickPos[0]*(right-left))
    clickWinY = int(top + clickPos[1]*(bottom-top))

    (clickedX, clickedY) = iClickWindow((clickWinX, clickWinY),
                                        mouseButton, mouseEvent,
                                        dryRun, capture=False)

    if capture:
        if _captureText == None:
            _captureText = "Box: %s, %s, %s, %s" % (left, top, right, bottom)
        drawIcon(_g_origImage, capture, _captureText, (left, top, right, bottom))
        drawClickedPoint(capture, capture, (clickedX, clickedY))

    return (clickedX, clickedY)


def iClickWindow((clickX, clickY), mouseButton=1, mouseEvent=1, dryRun=None, capture=None):
    """
    Click given coordinates in the window.

    Parameters:

        (clickX, clickY)
                     coordinates to be clicked inside the window.
                     (0, 0) is the top-left corner of the window.

        mouseButton  mouse button to be synthesized on the event, default is 1.

        mouseEvent   event to be synthesized, the default is MOUSEEVENT_CLICK,
                     others: MOUSEEVENT_MOVE, MOUSEEVENT_DOWN, MOUSEEVENT_UP.

        dryRun       if True, does not synthesize events. Still
                     illustrates the clicked position on the capture
                     image if given.

        capture      name of file where the last screenshot with
                     clicked point highlighted is saved. The default
                     is None (nothing is saved).

    Returns pair (clickedX, clickedY)
                     X and Y coordinates of clicked position on the
                     screen.
    """
    clickScrX = clickX + _g_windowOffsets[_g_lastWindow][0]
    clickScrY = clickY + _g_windowOffsets[_g_lastWindow][1]

    iClickScreen((clickScrX, clickScrY), mouseButton, mouseEvent, dryRun, capture)

    return (clickScrX, clickScrY)


def iClickScreen((clickX, clickY), mouseButton=1, mouseEvent=1, dryRun=None, capture=None):
    """
    Click given absolute coordinates on the screen.

    Parameters:

        (clickX, clickY)
                     coordinates to be clicked on the screen. (0, 0)
                     is the top-left corner of the screen.

        mouseButton  mouse button to be synthesized on the event, default is 1.

        mouseEvent   event to be synthesized, the default is MOUSEEVENT_CLICK,
                     others: MOUSEEVENT_MOVE, MOUSEEVENT_DOWN, MOUSEEVENT_UP.

        dryRun       if True, does not synthesize events. Still
                     illustrates the clicked position on the capture
                     image if given.

        capture      name of file where the last screenshot with
                     clicked point highlighted is saved. The default
                     is None (nothing is saved).
    """
    if mouseEvent == MOUSEEVENT_CLICK:
        params = "'mouseclick %s'" % (mouseButton,)
    elif mouseEvent == MOUSEEVENT_DOWN:
        params = "'mousedown %s'" % (mouseButton,)
    elif mouseEvent == MOUSEEVENT_UP:
        params = "'mouseup %s'" % (mouseButton,)
    else:
        params = ""

    if capture:
        drawClickedPoint(_g_origImage, capture, (clickX, clickY))

    if dryRun == None:
        dryRun = _g_defaultClickDryRun

    if not dryRun:
        # use xte from the xautomation package
        _runcmd("xte 'mousemove %s %s' %s" % (clickX, clickY, params))


def iType(word, delay=0.0):
    """
    Send keypress events.

    Parameters:
        word is either
            - a string containing letters and numbers.
              Each letter/number is using press and release events.
            - a list that contains
              - keys: each key is sent using press and release events.
              - (key, event)-pairs: the event (either "press" or "release")
                is sent.
              - (key1, key2, ..., keyn)-tuples. 2n events is sent:
                key1 press, key2 press, ..., keyn press,
                keyn release, ..., key2 release, key1 release.

            Keys are defined in keysymdef.h.

        delay is given as seconds between sent events

    Examples:
        iType('hello')
        iType([('Shift_L', 'press'), 'h', 'e', ('Shift_L', 'release'), 'l', 'l', 'o'])
        iType([('Control_L', 'Alt_L', 'Delete')])
    """
    args = []
    for char in word:
        if type(char) == tuple:
            if char[1].lower() == 'press':
                args.append("'keydown %s'" % (char[0],))
            elif char[1].lower() == 'release':
                args.append("'keyup %s'" % (char[0],))
            else:
                rest = []
                for key in char:
                    args.append("'keydown %s'" % (key,))
                    rest.insert(0, "'keyup %s'" % (key,))
                args = args + rest
        else:
            # char is keyname or single letter/number
            args.append("'key %s'" % (char,))
    usdelay = " 'usleep %s' " % (int(delay*1000000),)
    _runcmd("xte %s" % (usdelay.join(args),))

def iInputKey(keyName, hold=0.1, delay=0.0):
    """
    Send a keypress of keyName using Linux evdev interface
    (/dev/input/eventXX).

    Parameters:

        keyName      name of pressed key in keymap.
                     Use iSetInputKeys() to set a keymap.

        hold         time (in seconds) to hold the key before
                     releasing. The default is 0.1.

        delay        delay before returning after the keypress.

    Example:

        iSetInputKeys({'Power': ("Power Button", 106)})
        iInputKey('Power')
    """
    device, keycode = _g_inputKeys[keyName]
    writeKeyPress(deviceFilename(device), keycode, hold=hold, delay=delay)

def deviceFilename(deviceName):
    devices = dict(listInputDevices())
    if not deviceName in devices:
        return deviceName
    else:
        return devices[deviceName]

def listInputDevices():
    nameAndFile = []
    for l in file("/proc/bus/input/devices"):
        if l.startswith("N: Name="):
            nameAndFile.append([l.split('"')[1]])
        elif l.startswith("H: Handlers=") and "event" in l:
            nameAndFile[-1].append("/dev/input/event%s" % (l.rsplit("event",1)[1].rstrip(),))
    return nameAndFile

def writeKeyPress(filename, keyCode, hold=0.1, delay=0.1):
    fd = os.open(filename, os.O_WRONLY | os.O_NONBLOCK)
    bytes = os.write(fd, struct.pack(_InputEventStructSpec,
                                     int(time.time()), 0, _EV_KEY, keyCode, 1))
    if bytes > 0:
        bytes += os.write(fd, struct.pack(_InputEventStructSpec,
                                          0, 0, 0, 0, 0))
        time.sleep(hold)
        bytes += os.write(fd, struct.pack(_InputEventStructSpec,
                                          int(time.time()), 0, _EV_KEY, keyCode, 0))
        bytes += os.write(fd, struct.pack(_InputEventStructSpec,
                                          0, 0, 0, 0, 0))
        time.sleep(delay)
    os.close(fd)

def findWord(word, detected_words = None, appearance=1):
    """
    Returns pair (score, corresponding-detected-word)
    """
    if detected_words == None:
        detected_words = _g_words
        if _g_words == None:
            raise NoOCRResults()

    scored_words = []
    for w in detected_words:
        scored_words.append((_score(w, word), w))
    scored_words.sort()

    if len(scored_words) == 0:
        raise BadMatch("No words found.")

    return scored_words[-1]

def _score(w1, w2):
    closeMatch = {
        '1l': 0.1,
        '1I': 0.2,
        'Il': 0.2
        }
    def levenshteinDistance(w1, w2):
        m = [range(len(w1)+1)]
        for j in xrange(len(w2)+1):
            m.append([])
            m[-1].append(j+1)
        i, j = 0, 0
        for j in xrange(1, len(w2)+1):
            for i in xrange(1, len(w1)+1):
                if w1[i-1] == w2[j-1]:
                    m[j].append(m[j-1][i-1])
                else:
                    # This is not part of Levenshtein:
                    # if characters often look similar,
                    # don't add full edit distance (1.0),
                    # use the value in closeMatch instead.
                    chars = ''.join(sorted(w1[i-1] + w2[j-1]))
                    if chars in closeMatch:
                        m[j].append(m[j-1][i-1]+closeMatch[chars])
                    else:
                        # Standard Levenshtein continues...
                        m[j].append(min(
                                m[j-1][i] + 1,  # delete
                                m[j][i-1] + 1,  # insert
                                m[j-1][i-1] + 1 # substitute
                                ))
        return m[j][i]
    return 1 - (levenshteinDistance(w1, w2) / float(max(len(w1),len(w2))))

def _hocr2words(hocr):
    rv = {}
    hocr = hocr.replace("<strong>","").replace("</strong>","").replace("<em>","").replace("</em>","")
    hocr.replace("&#39;", "'")
    for name, code in htmlentitydefs.name2codepoint.iteritems():
        if code < 128:
            hocr = hocr.replace('&' + name + ';', chr(code))
    ocr_word = re.compile('''<span class=['"]ocr_word["'] id=['"]([^']*)["'] title=['"]bbox ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)["'][^>]*>([^<]*)</span>''')
    for word_id, bbox_left, bbox_top, bbox_right, bbox_bottom, word in ocr_word.findall(hocr):
        bbox_left, bbox_top, bbox_right, bbox_bottom = \
            int(bbox_left), int(bbox_top), int(bbox_right), int(bbox_bottom)
        if not word in rv:
            rv[word] = []
        middle_x = (bbox_right + bbox_left) / 2.0
        middle_y = (bbox_top + bbox_bottom) / 2.0
        rv[word].append((word_id, (middle_x, middle_y),
                         (bbox_left, bbox_top, bbox_right, bbox_bottom)))
    return rv

def iUseWindow(windowIdOrName = None):
    global _g_lastWindow
    global _g_screenSize

    if windowIdOrName == None:
        if _g_lastWindow == None:
            _g_lastWindow = iActiveWindow()
    elif windowIdOrName.startswith("0x"):
        _g_lastWindow = windowIdOrName
    else:
        _g_lastWindow = _runcmd("xwininfo -name '%s' | awk '/Window id: 0x/{print $4}'" %
                              (windowIdOrName,))[1].strip()
        if not _g_lastWindow.startswith("0x"):
            raise BadWindowName('Cannot find window id for "%s" (got: "%s")' %
                                (windowIdOrName, _g_lastWindow))
    _, output = _runcmd("xwininfo -id %s | awk '/Width:/{w=$NF}/Height:/{h=$NF}/Absolute upper-left X/{x=$NF}/Absolute upper-left Y/{y=$NF}END{print x\" \"y\" \"w\" \"h}'" %
                       (_g_lastWindow,))
    offset_x, offset_y, width, height = output.split(" ")
    _g_windowOffsets[_g_lastWindow] = (int(offset_x), int(offset_y))
    _g_windowSizes[_g_lastWindow] = (int(width), int(height))
    _, output = _runcmd("xwininfo -root | awk '/Width:/{w=$NF}/Height:/{h=$NF}END{print w\" \"h}'")
    s_width, s_height = output.split(" ")
    _g_screenSize = (int(s_width), int(s_height))
    return _g_lastWindow

def iUseImageAsWindow(imageFilename):
    global _g_lastWindow
    global _g_screenSize

    if not eye4graphics:
        _log('ERROR: iUseImageAsWindow("%s") called, but eye4graphics not loaded.' % (imageFilename,))
        raise EyenfingerError("eye4graphics not available")

    _g_lastWindow = imageFilename

    struct_bbox = Bbox(0,0,0,0,0)
    err = eye4graphics.imageDimensions(ctypes.byref(struct_bbox),
                                       imageFilename)
    if err != 0:
        _log('iUseImageAsWindow: Failed reading dimensions of image "%s".' % (imageFilename,))
        raise BadSourceImage('Failed to read dimensions of "%s".' % (imageFilename,))

    _g_windowOffsets[_g_lastWindow] = (0, 0)
    _g_windowSizes[_g_lastWindow] = (int(struct_bbox.right), int(struct_bbox.bottom))
    _g_screenSize = _g_windowSizes[_g_lastWindow]
    return _g_lastWindow

def iActiveWindow(windowId = None):
    """ return id of active window, in '0x1d0f14' format """
    if windowId == None:
        _, output = _runcmd("xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}'")
        windowId = output.strip()

    return windowId

def drawWords(inputfilename, outputfilename, words, detected_words):
    """
    Draw boxes around words detected in inputfilename that match to
    given words. Result is saved to outputfilename.
    """
    draw_commands = ""
    for w in words:
        score, dw = findWord(w, detected_words)
        left, top, right, bottom = detected_words[dw][0][2]
        if score < 0.33:
            color = "red"
        elif score < 0.5:
            color = "brown"
        else:
            color = "green"
        draw_commands += """ -stroke %s -fill blue -draw "fill-opacity 0.2 rectangle %s,%s %s,%s" """ % (
            color, left, top, right, bottom)
        draw_commands += """ -stroke none -fill %s -draw "text %s,%s '%s'" """ % (
            color, left, top, w)
        draw_commands += """ -stroke none -fill %s -draw "text %s,%s '%.2f'" """ % (
            color, left, bottom+10, score)
    _runcmd("convert %s %s %s" % (inputfilename, draw_commands, outputfilename))

def drawIcon(inputfilename, outputfilename, iconFilename, bbox, color='green'):
    left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
    draw_commands = """ -stroke %s -fill blue -draw "fill-opacity 0.2 rectangle %s,%s %s,%s" """ % (color, left, top, right, bottom)
    draw_commands += """ -stroke none -fill %s -draw "text %s,%s '%s'" """ % (
        color, left, top, iconFilename)
    _runcmd("convert %s %s %s" % (inputfilename, draw_commands, outputfilename))

def drawClickedPoint(inputfilename, outputfilename, clickedXY):
    """
    clickedXY contains absolute screen coordinates
    """
    x, y = clickedXY
    x -= _g_windowOffsets[_g_lastWindow][0]
    y -= _g_windowOffsets[_g_lastWindow][1]
    draw_commands = """ -stroke red -fill blue -draw "fill-opacity 0.2 circle %s,%s %s,%s" """ % (
        x, y, x + 20, y)
    draw_commands += """ -stroke none -fill red -draw "point %s,%s" """ % (x, y)
    _runcmd("convert %s %s %s" % (inputfilename, draw_commands, outputfilename))

def evaluatePreprocessFilter(imageFilename, ppfilter, words):
    """
    Visualise how given words are detected from given image file when
    using given preprocessing filter.
    """
    global _g_preprocess
    evaluatePreprocessFilter.count += 1
    preprocessed_filename = '%s-pre%s.png' % (imageFilename, evaluatePreprocessFilter.count)
    _runcmd("convert '%s' %s '%s' && tesseract %s eyenfinger.autoconfigure hocr" %
           (imageFilename, ppfilter, preprocessed_filename,
            preprocessed_filename))
    detected_words = _hocr2words(file("eyenfinger.autoconfigure.html").read())
    scored_words = []
    for w in words:
        try:
            score, word = findWord(w, detected_words)
        except BadMatch:
            return
        scored_words.append((score, word, w))
    scored_words.sort()

    avg_score = sum([s[0] for s in scored_words])/float(len(scored_words))
    evaluatePreprocessFilter.scores.append( (scored_words[0][0] + avg_score, scored_words[0][0], avg_score, ppfilter) )
    evaluatePreprocessFilter.scores.sort()
    # set the best preprocess filter so far as a default
    _g_preprocess = evaluatePreprocessFilter.scores[-1][-1]
    drawWords(preprocessed_filename, preprocessed_filename, words, detected_words)
    sys.stdout.write("%.2f %s %s %s\n" % (sum([s[0] for s in scored_words])/float(len(scored_words)), scored_words[0], preprocessed_filename, ppfilter))
    sys.stdout.flush()
evaluatePreprocessFilter.count = 0
evaluatePreprocessFilter.scores = []

def autoconfigure(imageFilename, words):
    """
    Search for image preprocessing configuration that will maximise
    the score of finding given words in the image.
    Returns configuration as a string.
    """

    # check image width
    iUseImageAsWindow(imageFilename)
    image_width = _g_windowSizes[_g_lastWindow][0]

    resize_filters = ['Mitchell', 'Catrom', 'Hermite', 'Gaussian']
    levels = [(20, 30), (20, 40), (20, 50),
              (30, 30), (30, 40), (30, 50),
              (40, 40), (40, 50), (40, 60),
              (50, 50), (50, 60), (50, 70),
              (60, 60), (60, 70), (60, 80)]

    zoom = [2]

    for f in resize_filters:
        for blevel, wlevel in levels:
            for z in zoom:
                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -filter %s -resize %sx -sharpen 5 -level %s%%,%s%%,3.0 -sharpen 5" % (f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -filter %s -resize %sx -level %s%%,%s%%,3.0 -sharpen 5" % (
                        f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -filter %s -resize %sx -level %s%%,%s%%,3.0" % (
                        f, z * image_width, blevel, wlevel),
                    words)

                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -level %s%%,%s%%,3.0 -filter %s -resize %sx -sharpen 5" % (
                        blevel, wlevel, f, z * image_width),
                    words)

                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -level %s%%,%s%%,1.0 -filter %s -resize %sx" % (
                        blevel, wlevel, f, z * image_width),
                    words)

                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -level %s%%,%s%%,10.0 -filter %s -resize %sx" % (
                        blevel, wlevel, f, z * image_width),
                    words)
