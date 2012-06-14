# Test step implementations
import camera
import time
import os
from os.path import exists

P = {'resolution': '640x480',
     'photo': 'noname.jpg'}

def iCaptureImage():
    if exists(P['photo']):
        os.remove(P['photo'])
    camera.capture(P)
    assert exists(P['photo']), "No file."

def iPreview():
    assert camera.previewFrameCount() == 0
    assert camera.previewing() == False
    camera.startPreview(P)
    time.sleep(1)
    frames = camera.previewFrameCount()
    assert camera.previewing() == True
    camera.stopPreview()
    return frames

def iStartVideocapt():
    camera.startVideoCapture()

def iStopVideocapt():
    camera.stopVideoCapture()
