#!/usr/bin/env python

from PySide import QtCore
from PySide import QtGui

import getopt
import math
import sys
import time

class GestureEvent(object):
    __slots__ = ["time", "event", "key", "pos"]
    def __init__(self, event, key, pos):
        self.time = time.time()
        self.event = event
        self.key = key
        self.pos = pos
    def __str__(self):
        return 'GestureEvent(time=%s, event="%s", key=%s, pos=%s)' % (
            self.time, self.event, self.key, self.pos)

class MyScaleEvents(QtCore.QObject):
    """
    Catch scaling events: Ctrl++, Ctrl+-, Ctrl+wheel. Change
    attrowner's attribute "wheel_scale" accordingly. Finally call
    attrowner's wheel_scale_changed().
    """
    def __init__(self, mainwindow, attrowner, min_scale, max_scale):
        QtCore.QObject.__init__(self, mainwindow)
        self.min_scale  = min_scale
        self.max_scale  = max_scale
        self.attrowner  = attrowner
        self.mainwindow = mainwindow
        self.visibleTip = None
    def changeScale(self, coefficient):
        self.attrowner.wheel_scale *= coefficient
        if self.attrowner.wheel_scale < self.min_scale: self.attrowner.wheel_scale = self.min_scale
        elif self.attrowner.wheel_scale > self.max_scale: self.attrowner.wheel_scale = self.max_scale
        self.attrowner.wheel_scale_changed()
    def eventFilter(self, obj, event):
        def posToRel(pos):
            sbY = self.attrowner.verticalScrollBar().value()
            sbX = self.attrowner.horizontalScrollBar().value()
            wS = self.attrowner.wheel_scale
            x = (pos().x() + sbX) / wS / float(self.mainwindow.screenshotImage.width())
            y = (pos().y() + sbY) / wS / float(self.mainwindow.screenshotImage.height())
            return (x, y)
        if event.type() == QtCore.QEvent.MouseMove:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mousemove", None, posToRel(event.pos)))
        elif event.type() == QtCore.QEvent.MouseButtonPress:
            if not self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = True
                self.mainwindow.gestureEvents = [
                    GestureEvent("mousedown", 0, posToRel(event.pos))]
        elif event.type() == QtCore.QEvent.MouseButtonRelease:
            if self.mainwindow.gestureStarted:
                self.mainwindow.gestureStarted = False
                self.mainwindow.gestureEvents.append(
                    GestureEvent("mouseup", 0, posToRel(event.pos)))

                s = gestureToGti(self.mainwindow.gestureEvents)
                cmd = "gti" + s
                if True: # if interact...
                    print s
                    eval(cmd)
                self.mainwindow.gestureEvents = []
                QtCore.QTimer.singleShot(1000, self.mainwindow.updateScreenshot)

        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Q:
                self.mainwindow.close()
        if event.type() == QtCore.QEvent.ToolTip:
            if not hasattr(self.attrowner, 'cursorForPosition'):
                return False
            cursor = self.attrowner.cursorForPosition(event.pos())
            pos = cursor.positionInBlock()
            lineno = cursor.blockNumber()
            cursor.select(QtGui.QTextCursor.LineUnderCursor)
            l = cursor.selectedText()
            start = l.rfind('"', 0, pos)
            end = l.find('"', pos)
            if -1 < start < end:
                quotedString = l[start+1:end]
                if self.visibleTip == (lineno, quotedString):
                    return True
                QtGui.QToolTip.hideText()
                if quotedString.lower().rsplit(".")[-1] in ["png", "jpg"]:
                    # tooltip for an image file
                    filename = quotedString
                    path = ':'.join([s.strip() for s in GT_IMAGEPATHRE.findall(self.mainwindow._modelSources())])
                    for d in path.split(':'):
                        filepath = os.path.join(d, filename)
                        if os.access(filepath, os.R_OK):
                            QtGui.QToolTip.showText(event.globalPos(), '%s<br><img src="%s">' % (filepath, filepath))
                            break
                    else:
                        QtGui.QToolTip.showText(event.globalPos(), '%s<br>not in found in<br># preview-image-path:...' % (filename,))
                    self.visibleTip = (lineno, quotedString)
            else:
                self.visibleTip = None
                QtGui.QToolTip.hideText()
            return True

        if event.type() == QtCore.QEvent.Wheel and event.modifiers() == QtCore.Qt.ControlModifier:
            coefficient = 1.0 + event.delta() / 1440.0
            self.changeScale(coefficient)
        return False


def quantify(item, quantum):
    if not isinstance(item, tuple) and not isinstance(item, list):
        return int(item * (1/quantum)) * quantum
    else:
        return tuple([int(i * (1/quantum)) * quantum for i in item])

def gestureToGti(gestureEventList):
    timeQuantum = 0.2 # seconds
    locQuantum = 0.025 # 1.0 = full display height/width
    distQuantum = 0.1  # 1.0 = full dist from point to edge

    quantL = lambda v: quantify(v, locQuantum)
    quantT = lambda v: quantify(v, timeQuantum)

    el = gestureEventList

    firstEvent = el[0].event
    lastEvent = el[-1].event
    duration = el[-1].time - el[0].time
    distance = 0
    xDistance = 0
    yDistance = 0
    lastX, lastY = el[0].pos
    for e in el[1:]:
        xDistance += abs(lastX - e.pos[0])
        yDistance += abs(lastY - e.pos[1])
        distance += math.sqrt((lastX - e.pos[0])**2 +
                              (lastY - e.pos[1])**2)
        lastX, lastY = e.pos

    if firstEvent == "mousedown" and lastEvent == "mouseup":
        between_events = set([e.event for e in el[1:-1]])
        if between_events in (set(), set(["mousemove"])):
            # event sequence: mousedown, mousemove..., mouseup
            if duration < timeQuantum:
                # very quick event, make it single tap
                return ".tap((%s, %s))" % quantL(el[0].pos)
            elif distance < locQuantum:
                # neglible move, make it long tap
                return ".tap((%s, %s), hold=%s)" % (
                    quantL(el[0].pos) + quantT([duration]))
            elif xDistance < locQuantum:
                if el[-1].pos[1] < el[0].pos[1]:
                    direction = "north"
                else:
                    direction = "south"
                # only y axis changed, we've got a swipe
                return '.swipe((%s, %s), "%s", distance=%s)' % (
                    quantL(el[0].pos) + (direction,) +
                    quantL([yDistance]))
            elif yDistance < locQuantum:
                if el[-1].pos[0] < el[0].pos[0]:
                    direction = "west"
                else:
                    direction = "east"
                # only y axis changed, we've got a swipe
                return '.swipe((%s, %s), "%s", distance=%s)' % (
                    quantL(el[0].pos) + (direction,) +
                    quantL([xDistance]))
            else:
                return "TODO: drag..."
        else:
            return "unknown between events"
    else:
        return "unknown gesture"


class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.mainwidget = QtGui.QWidget()
        self.layout = QtGui.QVBoxLayout()
        self.mainwidget.setLayout(self.layout)

        self.screenshotButtons = QtGui.QWidget(self.mainwidget)
        self.screenshotButtonsL = QtGui.QHBoxLayout()
        self.screenshotButtons.setLayout(self.screenshotButtonsL)
        self.screenshotButtonRefresh = QtGui.QPushButton(self.screenshotButtons,
                                                         text="Refresh")
        self.screenshotButtonsL.addWidget(self.screenshotButtonRefresh)
        self.screenshotButtonRecord = QtGui.QPushButton(self.screenshotButtons,
                                                        text="Record",
                                                        checkable = True)
        self.screenshotButtonsL.addWidget(self.screenshotButtonRecord)
        self.screenshotButtonInteract = QtGui.QPushButton(self.screenshotButtons,
                                                        text="Interact",
                                                        checkable = True)
        self.screenshotButtonsL.addWidget(self.screenshotButtonInteract)
        self.layout.addWidget(self.screenshotButtons)


        def makeScalableImage(parent, qlabel):
            container = QtGui.QWidget(parent)
            layout = QtGui.QHBoxLayout()
            container.setLayout(layout)
            container.setStyleSheet("background-color:white;")

            qlabel.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)
            qlabel.setScaledContents(True)
            qlabel.resize(QtCore.QSize(0,0))

            area = QtGui.QScrollArea(container)
            area.setWidget(qlabel)
            qlabel._scaleevents = MyScaleEvents(self, area, 0.1, 1.0)
            area.wheel_scale = 1.0
            area.wheel_scale_changed = lambda: qlabel.resize(area.wheel_scale * qlabel.pixmap().size())
            area.installEventFilter(qlabel._scaleevents)
            layout.addWidget(area)
            container.area = area
            container._layout = layout # protect from garbage collector
            return container

        self.screenshotQLabel = QtGui.QLabel(self.mainwidget)
        self.screenshotContainer = makeScalableImage(self.mainwidget, self.screenshotQLabel)
        # self.screenshotContainer = QtGui.QLabel(self.mainwidget)
        self.layout.addWidget(self.screenshotContainer)
        self.screenshotImage = QtGui.QImage()

        self.screenshotQLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                self.screenshotImage))

        self.setCentralWidget(self.mainwidget)

        self.gestureEvents = []
        self.gestureStarted = False

    def updateScreenshot(self):
        gti.refreshScreenshot().save("screen2gti.png")
        self.screenshotImage = QtGui.QImage()
        self.screenshotImage.load("screen2gti.png")
        self.screenshotQLabel.setPixmap(
            QtGui.QPixmap.fromImage(
                self.screenshotImage))
        self.screenshotContainer.update()
        self.screenshotContainer.repaint()
        self.screenshotContainer.show()
        self.screenshotContainer.area.setWidget(self.screenshotQLabel)
        self.screenshotContainer.area.wheel_scale_changed()
        self.show()
        self.repaint()

if __name__ == "__main__":

    opt_connect = None
    opt_gti = None
    supported_platforms = ['android', 'tizen', 'x11', 'vnc']

    opts, remainder = getopt.getopt(
        sys.argv[1:], 'hd:p:',
        ['help', 'device=', 'platform='])

    for opt, arg in opts:
        if opt in ['-h', '--help']:
            print __doc__
            sys.exit(0)
        elif opt in ['-d', '--device']:
            opt_connect = arg
        elif opt in ['-p', '--platform']:
            opt_gti = arg
            if not arg in ['android', 'tizen', 'x11', 'vnc']:
                error('unknown platform: "%s". Use one of "%s"' % (
                    arg, '", "'.join(supported_platforms)))

    l = __import__("fmbt" + opt_gti)
    gti = l.Device(opt_connect)

    _app = QtGui.QApplication(sys.argv)
    _win = MainWindow()
    _win.resize(640, 480)
    _win.updateScreenshot()
    _win.show()
    _app.exec_()
