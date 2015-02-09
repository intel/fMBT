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
eyenfinger - DEPRECATED GUI testing library based on OCR and X event generation

Use fmbtx11 instead.

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

import distutils.sysconfig
import time
import subprocess
import re
import math
import htmlentitydefs
import sys
import os
import tempfile
import atexit
import shlex
import shutil
import ctypes
import platform
import struct
import warnings

import fmbt_config

def _DEPRECATED():
    warnings.warn("eyenfinger.py API is deprecated, use fmbtx11 instead.",
                  DeprecationWarning, stacklevel=2)

_g_preprocess = "-sharpen 5 -filter Mitchell -resize 1920x1600 -level 40%%,70%%,5.0 -sharpen 5"

_g_readImage = None

_g_origImage = None

_g_hocr = ""

_g_words = None

_g_lastWindow = None

_g_defaultClickDryRun = False
_g_defaultDelayedDrawing = False
_g_defaultIconMatch = 1.0
_g_defaultIconColorMatch = 1.0
_g_defaultIconOpacityLimit = 0.0
_g_defaultInputKeyDevice = None
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

# Xkeys contains key names known to X11, see keysymdef.h.
Xkeys = [
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

# InputKeys contains key names known to input devices, see
# linux/input.h or http://www.usb.org/developers/hidpage. The order is
# significant, because keyCode = InputKeys.index(keyName).
InputKeys = [
    "RESERVED", "ESC","1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
    "MINUS", "EQUAL", "BACKSPACE", "TAB",
    "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P",
    "LEFTBRACE", "RIGHTBRACE", "ENTER", "LEFTCTRL",
    "A", "S", "D", "F", "G", "H", "J", "K", "L",
    "SEMICOLON", "APOSTROPHE", "GRAVE", "LEFTSHIFT", "BACKSLASH",
    "Z", "X", "C", "V", "B", "N", "M",
    "COMMA", "DOT", "SLASH", "RIGHTSHIFT", "KPASTERISK", "LEFTALT",
    "SPACE", "CAPSLOCK",
    "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10",
    "NUMLOCK", "SCROLLLOCK",
    "KP7", "KP8", "KP9", "KPMINUS",
    "KP4", "KP5", "KP6", "KPPLUS",
    "KP1", "KP2", "KP3", "KP0", "KPDOT",
    "undefined0",
    "ZENKAKUHANKAKU", "102ND", "F11", "F12", "RO",
    "KATAKANA", "HIRAGANA", "HENKAN", "KATAKANAHIRAGANA", "MUHENKAN",
    "KPJPCOMMA", "KPENTER", "RIGHTCTRL", "KPSLASH", "SYSRQ", "RIGHTALT",
    "LINEFEED", "HOME", "UP", "PAGEUP", "LEFT", "RIGHT", "END", "DOWN",
    "PAGEDOWN", "INSERT", "DELETE", "MACRO",
    "MUTE", "VOLUMEDOWN", "VOLUMEUP",
    "POWER",
    "KPEQUAL", "KPPLUSMINUS", "PAUSE", "SCALE", "KPCOMMA", "HANGEUL",
    "HANGUEL", "HANJA", "YEN", "LEFTMETA", "RIGHTMETA", "COMPOSE"]

_inputKeyShorthands = {
    "-": "MINUS", "=": "EQUAL",
    "[": "LEFTBRACE", "]": "RIGHTBRACE", "\n": "ENTER",
    ";": "SEMICOLON",
    ",": "COMMA", ".": "DOT", "/": "SLASH",
    " ": "SPACE" }

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
    _libpath = ["", ".",
            os.path.dirname(os.path.abspath(__file__)),
            distutils.sysconfig.get_python_lib(plat_specific=1)]
    _suffix = ".so"
    if os.name == "nt":
        _suffix = ".dll"
    for _dirname in _libpath:
        try:
            eye4graphics = ctypes.CDLL(os.path.join(_dirname , "eye4graphics"+_suffix))
            break
        except: pass
    else:
        raise ImportError("%s cannot load eye4graphics%s" % (__file__, _suffix))

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

# See struct input_event in /usr/include/linux/input.h
if platform.architecture()[0] == "32bit":
    _InputEventStructSpec = 'IIHHi'
else:
    _InputEventStructSpec = 'QQHHi'
# Event and keycodes are in input.h, too.
_EV_KEY = 0x01

# _inputKeyNameCodeMap is a dictionary keyName -> keyCode
_inputKeyNameCodeMap = {}
for code, name in enumerate(InputKeys):
    _inputKeyNameCodeMap[name] = code
def _inputKeyNameToCode(keyName):
    if keyName in _inputKeyNameCodeMap:
        return _inputKeyNameCodeMap[keyName]
    elif keyName in _inputKeyShorthands:
        return _inputKeyNameCodeMap[_inputKeyShorthands[keyName]]
    else:
        raise ValueError('Invalid key name "%s"' % (keyName,))

def error(msg, exitstatus=1):
    sys.stderr.write("eyenfinger: %s\n" % (msg,))
    sys.exit(1)

def printEventsFromFile(filename):
    fd = os.open(filename, os.O_RDONLY)

    try:
        while 1:
            evString = os.read(fd, struct.calcsize(_InputEventStructSpec))
            if not evString: break
            tim, tus, typ, cod, val = struct.unpack(_InputEventStructSpec, evString)
            if cod < len(InputKeys):
                nam = InputKeys[cod]
            else:
                nam = "N/A"
            print "time: %8s, susc: %8s, type: %8s, keyCode: %5s name: %10s value: %8s" % \
                (tim, tus, typ, cod, nam, val)

    finally:
        os.close(fd)

def printEventsFromDevice(deviceName):
    devices = dict(_listInputDevices())
    if not deviceName in devices:
        error('Unknown device "%s". Available devices: %s' %
              (deviceName, sorted(devices.keys())))
    else:
        printEventsFromFile(devices[deviceName])

def _exitHandler():
    shutil.rmtree(_g_tempdir, ignore_errors=True)
atexit.register(_exitHandler)

def _runcmd(cmd):
    global _g_last_runcmd_error
    p = subprocess.Popen(cmd, shell=isinstance(cmd, basestring),
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output = p.stdout.read()
    exit_status = p.wait()
    _g_last_runcmd_error = p.stderr.read()
    if exit_status != 0:
        _log("runcmd: %s" % (cmd,))
        _log("exit status: " + str(exit_status))
        _log("stdout: " + output)
        _log("stderr: " + _g_last_runcmd_error)
    else:
        p.stderr.read()
    return exit_status, output

def _runDrawCmd(inputfilename, cmd, outputfilename):
    if not _g_defaultDelayedDrawing:
        return _runcmd([fmbt_config.imagemagick_convert,
                        inputfilename] + cmd + [outputfilename])
    # Do delayed drawing to save test execution time. If the output
    # file does not exist, just copy inputfile to outputfile and start
    # logging delayed draw commands to
    # outputfile.delayeddraw. Otherwise append latest command to
    # outputfile.delayeddraw.
    delayedCmd = '%s "%s" "%s" "%s"\n' % (
        fmbt_config.imagemagick_convert,
        outputfilename, '%s' % ('" "'.join(cmd)), outputfilename)
    delayedDrawFilename = outputfilename + ".delayeddraw"
    try:
        if os.access(outputfilename, os.R_OK) == False:
                shutil.copy(inputfilename, outputfilename)
                file(delayedDrawFilename, "w").write(delayedCmd)
        else:
            file(delayedDrawFilename, "a").write(delayedCmd)
    except:
        _log("error on delayed drawing: %s" % (delayedCmd,))
        raise
    _log("delayed drawing: %s" % (delayedCmd,))
    return (0, "")

def _safeForShell(s):
    # convert all non-ascii and bad chars to _
    try: s = unicode(s, "utf-8")
    except: pass
    return ''.join([(c, "_")[ord(c)>128 or c in "'\"\\`"] for c in s])

def _coordsToInt((x,y), (width, height)=(None, None)):
    """
    Convert percentages to screen coordinates
    """
    if (width == None or height == None):
        width, height = screenSize()

    if 0.0 <= x <= 1.0 and type(x) == float:
        x = int(round(x * width))
    else:
        x = int(x)

    if 0.0 <= y <= 1.0 and type(y) == float:
        y = int(round(y * height))
    else:
        y = int(y)

    return (x, y)

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

def iSetDefaultDelayedDrawing(delayedDrawing):
    """
    Set the default for delaying drawing operations on captured
    screenshots.

    If delayedDrawing == False, drawing actions on screenshots (like
    highlighting icon and clicked coordinates) takes place during the
    function execution (like iClickIcon).

    If delayedDrawing == True, the screenshot is saved without
    highlighted areas, and <screenshot filename>.delayeddraw file
    contains all draw commands that can be executed after the test
    run. This may save a lot test execution time and CPU on the device
    that runs eyenfinger.

    The default is False.
    """
    global _g_defaultDelayedDrawing
    _g_defaultDelayedDrawing = delayedDrawing

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

def iSetDefaultInputKeyDevice(deviceName):
    """
    Use deviceName as a default input device for iInputKey.
    iSetDefaultInputKeyDevice("/dev/input/event0")
    iInputKey(["enter"])
    """
    global _g_defaultInputKeyDevice
    _g_defaultInputKeyDevice = deviceName

def iSetDefaultReadWithOCR(ocr):
    """
    Set the default for using OCR when reading images or windows.
    """
    global _g_defaultReadWithOCR
    _g_defaultReadWithOCR = ocr

def screenSize():
    """
    Returns the size of the screen as a pair (width, height).
    """
    if _g_screenSize == (0, 0):
        _getScreenSize()
    return _g_screenSize

def windowSize():
    """
    Returns the size of the window as a pair (width, height).
    Choose a window first, for instance with iRead() or iUseWindow().
    """
    if _g_lastWindow == None:
        raise BadWindowName("undefined window")
    return _g_windowSizes[_g_lastWindow]

def windowXY():
    """
    Returns screen coordinates of the top-left corner of the window as
    a pair (x, y).
    Choose a window first, for instance with iRead() or iUseWindow().
    """
    if _g_lastWindow == None:
        raise BadWindowName("undefined window")
    return _g_windowOffsets[_g_lastWindow]

def imageSize(imageFilename):
    """
    Returns image size as pair (width, height).
    """
    struct_bbox = Bbox(0,0,0,0,0)
    err = eye4graphics.imageDimensions(ctypes.byref(struct_bbox),
                                       imageFilename)
    if err != 0:
        return None, None
    return struct_bbox.right, struct_bbox.bottom

def iRead(windowId = None, source = None, preprocess = None, ocr=None, capture=None, ocrArea=(0, 0, 1.0, 1.0), ocrPageSegModes=(3,), lang="eng", configfile=None):
    """
    DEPRECATED - use fmbtx11.Screen.refreshScreenshot instead.

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

        ocrArea      (top, left, right, bottom) coordinates -
                     area of the image to be read with OCR.

        ocrPageSegModes
                     tuple of integers, see tesseract -pagesegmodes

        lang         Tesseract language setting, the default is "eng".
                     Refer to LANGUAGES in Tesseract documentation or
                     man page.

        configfile   Tesseract configuration file.

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
        import fmbtx11
        fmbtx11.Screen().refreshScreenshot().save(SCREENSHOT_FILENAME + ".png")
        _runcmd("%s %s.png -crop %sx%s+%s+%s +repage '%s'" %
               (fmbt_config.imagemagick_convert, SCREENSHOT_FILENAME,
                _g_windowSizes[_g_lastWindow][0], _g_windowSizes[_g_lastWindow][1],
                _g_windowOffsets[_g_lastWindow][0], _g_windowOffsets[_g_lastWindow][1],
                SCREENSHOT_FILENAME))
        source = SCREENSHOT_FILENAME
    else:
        iUseImageAsWindow(source)
    _g_origImage = source
    orig_width, orig_height = _g_windowSizes[_g_lastWindow][0], _g_windowSizes[_g_lastWindow][1]
    x1, y1 = _coordsToInt(ocrArea[:2], (orig_width, orig_height))
    x2, y2 = _coordsToInt(ocrArea[2:], (orig_width, orig_height))

    if x2 <= x1 or y2 <= y1:
        raise EyenfingerError("Invalid area size: %s => %s" % (ocrArea, (x1, y1, x2, y2)))

    if orig_width <= 0 or orig_height <= 0:
        raise EyenfingerError("Invalid image size: %sx%s" % (orig_width, orig_height))

    if not ocr:
        if capture:
            drawWords(_g_origImage, capture, [], [])
        return []

    if preprocess == None:
        preprocess = _g_preprocess

    # convert to text
    _g_readImage = _g_origImage + "-pp.png"
    if ocrArea == (0, 0, 1.0, 1.0):
        croparea = []
        wordXOffset = 0
        wordYOffset = 0
    else:
        croparea = ["-crop", "%sx%s+%s+%s" % (x2-x1, y2-y1, x1, y1), "+repage"]
        wordXOffset = x1
        wordYOffset = y1
        # rescale possible resize preprocessing parameter
        resize_m = re.search('-resize ([0-9]+)x([0-9]*)', preprocess)
        if resize_m:
            origXResize = int(resize_m.group(1))
            newXResize = int(origXResize/float(orig_width) * (x2-x1))
            preprocess = (preprocess[:resize_m.start()] +
                          ("-resize %sx" % (newXResize,)) +
                          preprocess[resize_m.end():])
    _g_words = {}
    for psm in ocrPageSegModes:
        convert_cmd = ([fmbt_config.imagemagick_convert, _g_origImage] +
                       croparea +
                       shlex.split(preprocess) +
                       [_g_readImage])
        tesseract_cmd = ["tesseract", _g_readImage, SCREENSHOT_FILENAME,
                         "-l", lang, "-psm", str(psm), "hocr"]
        if isinstance(configfile, basestring):
            tesseract_cmd += [configfile]
        elif isinstance(configfile, list) or isinstance(configfile, tuple):
            tesseract_cmd += configfile
        exit_status, output = _runcmd(convert_cmd)
        if exit_status != 0:
            raise NoOCRResults("Convert returned exit status (%s): %s"
                               % (exit_status, _g_last_runcmd_error))

        exit_status, output = _runcmd(tesseract_cmd)
        if exit_status != 0:
            raise NoOCRResults("Tesseract returned exit status (%s): %s"
                               % (exit_status, _g_last_runcmd_error))

        hocr_filename = SCREENSHOT_FILENAME + ".html" # Tesseract 3.02

        if not os.access(hocr_filename, os.R_OK):
            hocr_filename = SCREENSHOT_FILENAME + ".hocr" # Tesseract 3.03
            if not os.access(hocr_filename, os.R_OK):
                raise NoOCRResults("HOCR output missing. Tesseract OCR 3.02 or greater required.\n")

        # store every word and its coordinates
        _g_words.update(_hocr2words(file(hocr_filename).read()))

    # convert word coordinates to the unscaled pixmap
    try:
        ocr_page_line = [line for line in file(hocr_filename).readlines() if "class='ocr_page'" in line][0]
    except IndexError:
        raise NoOCRResults("Could not read ocr_page class information from %s" % (hocr_filename,))

    scaled_width, scaled_height = re.findall('bbox 0 0 ([0-9]+)\s*([0-9]+)', ocr_page_line)[0]
    scaled_width, scaled_height = float(scaled_width) / (float(x2-x1)/orig_width), float(scaled_height) / (float(y2-y1)/orig_height)

    for word in sorted(_g_words.keys()):
        for appearance, (wordid, middle, bbox) in enumerate(_g_words[word]):
            _g_words[word][appearance] = \
                (wordid,
                 (int(middle[0]/scaled_width * orig_width) + wordXOffset,
                  int(middle[1]/scaled_height * orig_height) + wordYOffset),
                 (int(bbox[0]/scaled_width * orig_width) + wordXOffset,
                  int(bbox[1]/scaled_height * orig_height) + wordYOffset,
                  int(bbox[2]/scaled_width * orig_width) + wordXOffset,
                  int(bbox[3]/scaled_height * orig_height) + wordYOffset))
            _log('found "' + word + '": (' + str(bbox[0]) + ', ' + str(bbox[1]) + ')')
    if capture:
        drawWords(_g_origImage, capture, _g_words, _g_words)
    return sorted(_g_words.keys())


def iVerifyWord(word, match=0.33, appearance=1, capture=None):
    """
    DEPRECATED - use fmbtx11.Screen.verifyOcrText instead.

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

def iVerifyText(text, match=0.33, capture=None):
    """
    DEPRECATED - use fmbtx11.Screen.verifyOcrText instead.

    Verify that text can be found from previously iRead() image.

    Parameters:
        text         multiple words that should be checked

        match        minimum matching score

        capture      save image with verified text highlighted
                     to this file. Default: None (nothing is saved).

    Returns pair:
        ((score, matchingText), (left, top, right, bottom)), where

        score        score of found match (1.0 for perfect match)

        matchingText corresponding text detected by OCR

        (left, top, right, bottom)
                     bounding box of the text in read image

    Throws BadMatch error if text is not found.

    Throws NoOCRResults error if there are OCR results available
    on the current screen.
    """
    if _g_words == None:
        raise NoOCRResults('iRead has not been called with ocr=True')

    score_text_bbox_list = findText(text, match)
    if len(score_text_bbox_list) == 0:
        raise BadMatch('No match >= %s for text "%s"' % (score, text))

    score, text, bbox = score_text_box_list[0]

    if capture:
        drawBbox(_g_origImage, capture, bbox, "%.2f %s" % (score, text))

    return ((score, matching_text), bbox)

def iVerifyIcon(iconFilename, match=None, colorMatch=None, opacityLimit=None, capture=None, area=(0.0, 0.0, 1.0, 1.0), _origin="iVerifyIcon"):
    """
    DEPRECATED - use fmbtx11.Screen.verifyBitmap instead.

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

        area           rectangle (left, top, right, bottom). Search
                       icon inside this rectangle only. Values can be
                       absolute coordinates, or floats in range [0.0,
                       1.0] that will be scaled to image dimensions.
                       The default is (0.0, 0.0, 1.0, 1.0), that is
                       full rectangle.

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

    if area[0] > area[2] or area[1] >= area[3]:
        raise ValueError("invalid area: %s, should be rectangle (left, top, right, bottom)" % (area,))

    leftTopRightBottomZero = (_coordsToInt((area[0], area[1]), windowSize()) +
                               _coordsToInt((area[2], area[3]), windowSize()) +
                               (0,))
    struct_area_bbox = Bbox(*leftTopRightBottomZero)
    struct_bbox = Bbox(0,0,0,0,0)
    threshold = int((1.0-match)*20)
    err = eye4graphics.findSingleIcon(ctypes.byref(struct_bbox),
                                      _g_origImage, iconFilename, threshold,
                                      ctypes.c_double(colorMatch),
                                      ctypes.c_double(opacityLimit),
                                      ctypes.byref(struct_area_bbox))
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
        drawIcon(_g_origImage, capture, iconFilename, bbox, area=leftTopRightBottomZero[:4])

    return (score, bbox)


def iClickIcon(iconFilename, clickPos=(0.5,0.5), match=None,
               colorMatch=None, opacityLimit=None,
               mouseButton=1, mouseEvent=MOUSEEVENT_CLICK, dryRun=None, capture=None):
    """
    DEPRECATED - use fmbtx11.Screen.tapBitmap instead.

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
    _DEPRECATED()
    score, bbox = iVerifyIcon(iconFilename, match=match,
                              colorMatch=colorMatch, opacityLimit=opacityLimit,
                              capture=capture, _origin="iClickIcon")

    clickedXY = iClickBox(bbox, clickPos, mouseButton, mouseEvent, dryRun,
                          capture, _captureText = iconFilename)

    return (score, clickedXY)


def iClickWord(word, appearance=1, clickPos=(0.5,0.5), match=0.33,
               mouseButton=1, mouseEvent=1, dryRun=None, capture=None):
    """
    DEPRECATED - use fmbtx11.Screen.tapOcrText instead.

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
    _DEPRECATED()
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
    DEPRECATED - use fmbtx11.Screen.tapItem instead.

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
    DEPRECATED - use fmbtx11.Screen.tap instead.

    Click given coordinates in the window.

    Parameters:

        (clickX, clickY)
                     coordinates to be clicked inside the window.
                     (0, 0) is the top-left corner of the window.
                     Integer values are window coordinates. Floating
                     point values from 0.0 to 1.0 are scaled to window
                     coordinates: (0.5, 0.5) is the middle of the
                     window, and (1.0, 1.0) the bottom-right corner of
                     the window.

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

    # Get the size of the window
    wndSize = windowSize()

    (clickX, clickY) = _coordsToInt((clickX, clickY), wndSize)

    # Get the position of the window
    wndPos = windowXY()

    # If coordinates are given as percentages, convert to window coordinates
    clickScrX = clickX + wndPos[0]
    clickScrY = clickY + wndPos[1]

    iClickScreen((clickScrX, clickScrY), mouseButton, mouseEvent, dryRun, capture)
    return (clickScrX, clickScrY)


def iClickScreen((clickX, clickY), mouseButton=1, mouseEvent=1, dryRun=None, capture=None):
    """
    DEPRECATED - use fmbtx11.Screen.tap instead.

    Click given absolute coordinates on the screen.

    Parameters:

        (clickX, clickY)
                     coordinates to be clicked on the screen. (0, 0)
                     is the top-left corner of the screen. Integer
                     values are screen coordinates. Floating point
                     values from 0.0 to 1.0 are scaled to screen
                     coordinates: (0.5, 0.5) is the middle of the
                     screen, and (1.0, 1.0) the bottom-right corner of
                     the screen.

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
    _DEPRECATED()
    if mouseEvent == MOUSEEVENT_CLICK:
        params = "'mouseclick %s'" % (mouseButton,)
    elif mouseEvent == MOUSEEVENT_DOWN:
        params = "'mousedown %s'" % (mouseButton,)
    elif mouseEvent == MOUSEEVENT_UP:
        params = "'mouseup %s'" % (mouseButton,)
    else:
        params = ""

    clickX, clickY = _coordsToInt((clickX, clickY))

    if capture:
        drawClickedPoint(_g_origImage, capture, (clickX, clickY))

    if dryRun == None:
        dryRun = _g_defaultClickDryRun

    if not dryRun:
        # use xte from the xautomation package
        _runcmd("xte 'mousemove %s %s' %s" % (clickX, clickY, params))

def iGestureScreen(listOfCoordinates, duration=0.5, holdBeforeGesture=0.0, holdAfterGesture=0.0, intermediatePoints=0, capture=None, dryRun=None):
    """
    DEPRECATED - use fmbtx11.Screen.drag instead.

    Synthesizes a gesture on the screen.

    Parameters:

        listOfCoordinates
                     The coordinates through which the cursor moves.
                     Integer values are screen coordinates. Floating
                     point values from 0.0 to 1.0 are scaled to screen
                     coordinates: (0.5, 0.5) is the middle of the
                     screen, and (1.0, 1.0) the bottom-right corner of
                     the screen.

        duration     gesture time in seconds, excluding
                     holdBeforeGesture and holdAfterGesture times.

        holdBeforeGesture
                     time in seconds to keep mouse down before the
                     gesture.

        holdAfterGesture
                     time in seconds to keep mouse down after the
                     gesture.

        intermediatePoints
                     the number of intermediate points to be added
                     between each of the coordinates. Intermediate
                     points are added to straight lines between start
                     and end points.

        capture      name of file where the last screenshot with
                     the points through which the cursors passes is
                     saved. The default is None (nothing is saved).

        dryRun       if True, does not synthesize events. Still
                     illustrates the coordinates through which the cursor
                     goes.
    """
    _DEPRECATED()
    # The params list to be fed to xte
    params = []

    # The list of coordinates through which the cursor has to go
    goThroughCoordinates = []

    for pos in xrange(len(listOfCoordinates)):
        x, y = _coordsToInt(listOfCoordinates[pos])
        goThroughCoordinates.append((x,y))

        if pos == len(listOfCoordinates) - 1:
            break # last coordinate added

        nextX, nextY = _coordsToInt(listOfCoordinates[pos+1])
        (x,y), (nextX, nextY) = (x, y), (nextX, nextY)

        for ip in range(intermediatePoints):
            goThroughCoordinates.append(
                (int(round(x + (nextX-x)*(ip+1)/float(intermediatePoints+1))),
                 int(round(y + (nextY-y)*(ip+1)/float(intermediatePoints+1)))))

    # Calculate the time (in micro seconds) to sleep between moves.
    if len(goThroughCoordinates) > 1:
        moveDelay = 1000000 * float(duration) / (len(goThroughCoordinates)-1)
    else:
        moveDelay = 0

    if not dryRun:
        # Build the params list.
        params.append("'mousemove %d %d'" % goThroughCoordinates[0])
        params.append("'mousedown 1 '")

        if holdBeforeGesture > 0:
            params.append("'usleep %d'" % (holdBeforeGesture * 1000000,))

        for i in xrange(1, len(goThroughCoordinates)):
            params.append("'usleep %d'" % (moveDelay,))
            params.append("'mousemove %d %d'" % goThroughCoordinates[i])

        if holdAfterGesture > 0:
            params.append("'usleep %d'" % (holdAfterGesture * 1000000,))

        params.append("'mouseup 1'")

        # Perform the gesture
        _runcmd("xte %s" % (" ".join(params),))

    if capture:
        intCoordinates = [ _coordsToInt(point) for point in listOfCoordinates ]
        drawLines(_g_origImage, capture, intCoordinates, goThroughCoordinates)

    return goThroughCoordinates

def iGestureWindow(listOfCoordinates, duration=0.5, holdBeforeGesture=0.0, holdAfterGesture=0.0, intermediatePoints=0, capture=None, dryRun=None):
    """
    DEPRECATED - use fmbtx11.Screen.drag instead.

    Synthesizes a gesture on the window.

    Parameters:

        listOfCoordinates
                     The coordinates through which the cursor moves.
                     Integer values are window coordinates. Floating
                     point values from 0.0 to 1.0 are scaled to window
                     coordinates: (0.5, 0.5) is the middle of the
                     window, and (1.0, 1.0) the bottom-right corner of
                     the window.

        duration     gesture time in seconds, excluding
                     holdBeforeGesture and holdAfterGesture times.

        holdBeforeGesture
                     time in seconds to keep mouse down before the
                     gesture.

        holdAfterGesture
                     time in seconds to keep mouse down after the
                     gesture.

        intermediatePoints
                     the number of intermediate points to be added
                     between each of the coordinates. Intermediate
                     points are added to straight lines between start
                     and end points.

        capture      name of file where the last screenshot with
                     the points through which the cursors passes is
                     saved. The default is None (nothing is saved).

        dryRun       if True, does not synthesize events. Still
                     illustrates the coordinates through which the cursor
                     goes.
    """
    screenCoordinates = [ _windowToScreen(*_coordsToInt((x,y),windowSize())) for (x,y) in listOfCoordinates ]
    return iGestureScreen(screenCoordinates, duration, holdBeforeGesture, holdAfterGesture, intermediatePoints, capture, dryRun)

def iType(word, delay=0.0):
    """
    DEPRECATED - use fmbtx11.Screen.type instead.

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

            Keys are defined in eyenfinger.Xkeys, for complete list
            see keysymdef.h.

        delay is given as seconds between sent events

    Examples:
        iType('hello')
        iType([('Shift_L', 'press'), 'h', 'e', ('Shift_L', 'release'), 'l', 'l', 'o'])
        iType([('Control_L', 'Alt_L', 'Delete')])
    """
    _DEPRECATED()
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


def iInputKey(*args, **kwargs):
    """
    DEPRECATED - use fmbtx11.Screen.pressKey instead.

    Send keypresses using Linux evdev interface
    (/dev/input/eventXX).

    iInputKey(keySpec[, keySpec...], hold=<float>, delay=<float>, device=<str>)

    Parameters:

        keySpec      is one of the following:
                     - a string of one-character-long key names:
                       "aesc" will send four keypresses: A, E, S and C.

                     - a list of key names:
                       ["a", "esc"] will send two keypresses: A and ESC.
                       Key names are listed in eyenfinger.InputKeys.

                     - an integer:
                       116 will press the POWER key.

                     - "_" or "^":
                       only press or release event will be generated
                       for the next key, respectively.

                     If a key name inside keySpec is prefixed by "_"
                     or "^", only press or release event is generated
                     for that key.

        hold         time (in seconds) to hold the key before
                     releasing. The default is 0.1.

        delay        delay (in seconds) after key release. The default
                     is 0.1.

        device       name of the input device or input event file to
                     which all key presses are sent. The default can
                     be set with iSetDefaultInputKeyDevice().  For
                     instance, "/dev/input/event0" or a name of a
                     device in /proc/bus/input/devices.
    """
    _DEPRECATED()
    hold = kwargs.get("hold", 0.1)
    delay = kwargs.get("delay", 0.1)
    device = kwargs.get("device", _g_defaultInputKeyDevice)
    inputKeySeq = []
    press, release = 1, 1
    for a in args:
        if a == "_": press, release = 1, 0
        elif a == "^": press, release = 0, 1
        elif type(a) == str:
            for char in a:
                if char == "_": press, release = 1, 0
                elif char == "^": press, release = 0, 1
                else:
                    inputKeySeq.append((press, release, _inputKeyNameToCode(char.upper())))
                    press, release = 1, 1
        elif type(a) in (tuple, list):
            for keySpec in a:
                if type(keySpec) == int:
                    inputKeySeq.append((press, release, keySpec))
                    press, release = 1, 1
                else:
                    if keySpec.startswith("_"):
                        press, release = 1, 0
                        keySpec = keySpec[1:]
                    elif keySpec.startswith("^"):
                        press, release = 0, 1
                        keySpec = keySpec[1:]
                    if keySpec:
                        inputKeySeq.append((press, release, _inputKeyNameToCode(keySpec.upper())))
                        press, release = 1, 1
        elif type(a) == int:
            inputKeySeq.append((press, release, a))
            press, release = 1, 1
        else:
            raise ValueError('Invalid keySpec "%s"' % (a,))
    if inputKeySeq:
        _writeInputKeySeq(_deviceFilename(device), inputKeySeq, hold=hold, delay=delay)

def _deviceFilename(deviceName):
    if not _deviceFilename.deviceCache:
        _deviceFilename.deviceCache = dict(_listInputDevices())
    if not deviceName in _deviceFilename.deviceCache:
        return deviceName
    else:
        return _deviceFilename.deviceCache[deviceName]
_deviceFilename.deviceCache = {}

def _listInputDevices():
    nameAndFile = []
    for l in file("/proc/bus/input/devices"):
        if l.startswith("N: Name="):
            nameAndFile.append([l.split('"')[1]])
        elif l.startswith("H: Handlers=") and "event" in l:
            try:
                eventFilename = re.findall("(event[0-9]+)", l)[0]
                nameAndFile[-1].append("/dev/input/%s" % (eventFilename,))
            except:
                _log('WARNING: Could not recognise event[0-9] filename from row "%s".' % (l.strip(),))
    return nameAndFile

def _writeInputKeySeq(filename, keyCodeSeq, hold=0.1, delay=0.1):
    if type(filename) != str or len(filename) == 0:
        raise ValueError('Invalid input device "%s"' % (filename,))
    fd = os.open(filename, os.O_WRONLY | os.O_NONBLOCK)
    for press, release, keyCode in keyCodeSeq:
        if press:
            bytes = os.write(fd, struct.pack(_InputEventStructSpec,
                                             int(time.time()), 0, _EV_KEY, keyCode, 1))
            if bytes > 0:
                bytes += os.write(fd, struct.pack(_InputEventStructSpec,
                                                  0, 0, 0, 0, 0))
            time.sleep(hold)
        if release:
            bytes += os.write(fd, struct.pack(_InputEventStructSpec,
                                              int(time.time()), 0, _EV_KEY, keyCode, 0))
            if bytes > 0:
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

def findText(text, detected_words = None, match=-1):
    def biggerBox(bbox_list):
        left, top, right, bottom = bbox_list[0]
        for l, t, r, b in bbox_list[1:]:
            left = min(left, l)
            top = min(top, t)
            right = max(right, r)
            bottom = max(bottom, b)
        return (left, top, right, bottom)
    words = text.split()
    word_count = len(words)
    detected_texts = [] # strings of <word_count> words

    if detected_words == None:
        detected_words = _g_words
        if _g_words == None:
            raise NoOCRResults()

    # sort by numeric word id
    words_by_id = []
    for word in detected_words:
        for wid, middle, bbox in detected_words[word]:
            # change word id from "word_2_42" to (2, 42)
            int_wid = [int(n) for n in wid[5:].split("_")]
            words_by_id.append(
                (int_wid, word, bbox))
    words_by_id.sort()

    for i in xrange(len(words_by_id)-word_count+1):
        detected_texts.append(
            (" ".join([w[1] for w in words_by_id[i:i+word_count]]),
             biggerBox([w[2] for w in words_by_id[i:i+word_count]])))

    norm_text = " ".join(words) # normalize whitespace
    scored_texts = []
    for t in detected_texts:
        scored_texts.append((_score(t[0], norm_text), t[0], t[1]))
    scored_texts.sort()
    return [st for st in scored_texts if st[0] >= match]

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
    ocr_word = re.compile('''<span class=['"]ocrx?_word["'] id=['"]([^']*)["'] title=['"]bbox ([0-9]+) ([0-9]+) ([0-9]+) ([0-9]+)["';][^>]*>([^<]*)</span>''')
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

def _getScreenSize():
    global _g_screenSize
    _, output = _runcmd("xwininfo -root | awk '/Width:/{w=$NF}/Height:/{h=$NF}END{print w\" \"h}'")
    s_width, s_height = output.split(" ")
    _g_screenSize = (int(s_width), int(s_height))

def iUseWindow(windowIdOrName = None):
    global _g_lastWindow

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
    _getScreenSize()
    return _g_lastWindow

def iUseImageAsWindow(imageFilename):
    global _g_lastWindow
    global _g_screenSize

    if not eye4graphics:
        _log('ERROR: iUseImageAsWindow("%s") called, but eye4graphics not loaded.' % (imageFilename,))
        raise EyenfingerError("eye4graphics not available")

    if not os.access(imageFilename, os.R_OK):
        raise BadSourceImage("The input file could not be read or not present.")

    _g_lastWindow = imageFilename

    imageWidth, imageHeight = imageSize(imageFilename)

    if imageWidth == None:
        _log('iUseImageAsWindow: Failed reading dimensions of image "%s".' % (imageFilename,))
        raise BadSourceImage('Failed to read dimensions of "%s".' % (imageFilename,))

    _g_windowOffsets[_g_lastWindow] = (0, 0)
    _g_windowSizes[_g_lastWindow] = (imageWidth, imageHeight)
    _g_screenSize = _g_windowSizes[_g_lastWindow]
    return _g_lastWindow

def iActiveWindow(windowId = None):
    """ return id of active window, in '0x1d0f14' format """
    if windowId == None:
        _, output = _runcmd("xprop -root | awk '/_NET_ACTIVE_WINDOW\(WINDOW\)/{print $NF}'")
        windowId = output.strip()

    return windowId

def drawBboxes(inputfilename, outputfilename, bboxes):
    """
    Draw bounding boxes
    """
    if inputfilename == None:
        return

    draw_commands = []
    for bbox in bboxes:
        left, top, right, bottom = bbox
        color = "green"
        draw_commands += ["-stroke", color, "-fill", "blue", "-draw", "fill-opacity 0.2 rectangle %s,%s %s,%s" % (
            left, top, right, bottom)]
    _runDrawCmd(inputfilename, draw_commands, outputfilename)

def drawBbox(inputfilename, outputfilename, bbox, caption):
    """
    Draw bounding box
    """
    if inputfilename == None:
        return

    draw_commands = []

    left, top, right, bottom = bbox
    color = "green"
    draw_commands += ["-stroke", color, "-fill", "blue", "-draw", "fill-opacity 0.2 rectangle %s,%s %s,%s" % (
        left, top, right, bottom)]
    draw_commands += ["-stroke", "none", "-fill", color, "-draw", "text %s,%s '%s'" % (
        left, top, _safeForShell(caption))]
    _runDrawCmd(inputfilename, draw_commands, outputfilename)

def drawWords(inputfilename, outputfilename, words, detected_words):
    """
    Draw boxes around words detected in inputfilename that match to
    given words. Result is saved to outputfilename.
    """
    if inputfilename == None:
        return

    draw_commands = []
    for w in words:
        score, dw = findWord(w, detected_words)
        left, top, right, bottom = detected_words[dw][0][2]
        if score < 0.33:
            color = "red"
        elif score < 0.5:
            color = "brown"
        else:
            color = "green"
        draw_commands += ["-stroke", color, "-fill", "blue", "-draw", "fill-opacity 0.2 rectangle %s,%s %s,%s" % (
            left, top, right, bottom)]
        draw_commands += ["-stroke", "none", "-fill", color, "-draw", "text %s,%s '%s'" % (
            left, top, _safeForShell(w))]
        draw_commands += ["-stroke", "none", "-fill", color, "-draw", "text %s,%s '%.2f'" % (
            left, bottom+10, score)]
    _runDrawCmd(inputfilename, draw_commands, outputfilename)

def drawIcon(inputfilename, outputfilename, iconFilename, bboxes, color='green', area=None):
    if inputfilename == None:
        return
    if type(bboxes) == tuple:
        bboxes = [bboxes]
        show_number = False
    else:
        show_number = True
    draw_commands = []
    for index, bbox in enumerate(bboxes):
        left, top, right, bottom = bbox[0], bbox[1], bbox[2], bbox[3]
        draw_commands += ["-stroke", color, "-fill", "blue", "-draw", "fill-opacity 0.2 rectangle %s,%s %s,%s" % (left, top, right, bottom)]
        if show_number:
            caption = "%s %s" % (index+1, iconFilename)
        else:
            caption = iconFilename
        draw_commands += ["-stroke", "none", "-fill", color, "-draw", "text %s,%s '%s'" % (
            left, top, _safeForShell(caption))]
    if area != None:
        draw_commands += ["-stroke", "yellow", "-draw", "fill-opacity 0.0 rectangle %s,%s %s,%s" % (area[0]-1, area[1]-1, area[2], area[3])]
    _runDrawCmd(inputfilename, draw_commands, outputfilename)

def drawClickedPoint(inputfilename, outputfilename, clickedXY):
    """
    clickedXY contains absolute screen coordinates
    """
    if inputfilename == None:
        return

    x, y = clickedXY
    x -= _g_windowOffsets[_g_lastWindow][0]
    y -= _g_windowOffsets[_g_lastWindow][1]
    draw_commands = ["-stroke", "red", "-fill", "blue", "-draw", "fill-opacity 0.2 circle %s,%s %s,%s" % (
        x, y, x + 20, y)]
    draw_commands += ["-stroke", "none", "-fill", "red", "-draw", "point %s,%s" % (x, y)]
    _runDrawCmd(inputfilename, draw_commands, outputfilename)

def _screenToWindow(x,y):
    """
    Converts from absolute coordinats to window coordinates
    """
    offsetX = _g_windowOffsets[_g_lastWindow][0]
    offsetY = _g_windowOffsets[_g_lastWindow][1]

    return (x-offsetX, y-offsetY)

def _windowToScreen(x,y):
    """
    Converts from window coordinates to screen coordinates
    """
    offsetX = _g_windowOffsets[_g_lastWindow][0]
    offsetY = _g_windowOffsets[_g_lastWindow][1]

    return (x+offsetX, y+offsetY)

def drawLines(inputfilename, outputfilename, orig_coordinates, final_coordinates):
    """
    coordinates contains the coordinates connected by lines
    """
    if inputfilename == None:
        return

    # The command which will be run
    draw_commands = []

    for pos in xrange(len(final_coordinates)-1):
        # Get the pair coordinates
        (x, y) = (final_coordinates[pos][0], final_coordinates[pos][1])
        (nextX, nextY) = (final_coordinates[pos+1][0], final_coordinates[pos+1][1])

        # Convert to window coordinates
        (drawX, drawY) = _screenToWindow(x,y)
        (drawnextX, drawnextY) = _screenToWindow(nextX, nextY)

        # Draw a pair of circles. User-given points are blue
        if (x, y) in orig_coordinates:
            draw_commands +=  ["-fill", "blue", "-stroke", "red", "-draw", "fill-opacity 0.2 circle %d, %d %d, %d" % (drawX, drawY, drawX-5, drawY-5)]
        # Computer-generated points are white
        else:
            draw_commands +=  ["-fill", "white", "-stroke", "red", "-draw", "fill-opacity 0.2 circle %d, %d %d, %d" % (drawX, drawY, drawX-5, drawY-5)]

        # Draw the line between the points
        draw_commands += ["-stroke", "red", "-draw", "line %d, %d, %d, %d" % (drawX, drawY, drawnextX, drawnextY)]
        draw_commands += ["-stroke", "black", "-draw", "line %d, %d, %d, %d" % (drawX+1, drawY+1, drawnextX+1, drawnextY+1)]

    if len(final_coordinates) > 0:
        lastIndex = len(final_coordinates)-1
        (finalX, finalY) = _screenToWindow(final_coordinates[lastIndex][0], final_coordinates[lastIndex][1])
        draw_commands += ["-fill", "blue", "-stroke", "red", "-draw", "fill-opacity 0.2 circle %d, %d %d, %d" % (finalX, finalY, finalX-5, finalY-5)]

    _runDrawCmd(inputfilename, draw_commands, outputfilename)

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
    levels = [(20, 20), (50, 50), (80, 80), (5, 5), (95, 95),
              (30, 30), (40, 40), (60, 60), (70, 70), (60, 60),
              (10, 30), (30, 50), (50, 70), (70, 90), (80, 100)]

    zoom = [1, 2]

    for f in resize_filters:
        for z in zoom:
            for blevel, wlevel in levels:
                evaluatePreprocessFilter(
                    imageFilename,
                    "-sharpen 5 -level %s%%,%s%%,3.0 -sharpen 5" % (blevel, wlevel),
                    words)

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
