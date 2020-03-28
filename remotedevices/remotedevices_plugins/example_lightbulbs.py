# fMBT, free Model Based Testing tool
# Copyright (c) Intel Corporation.
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

import remotedevices_server

class LightBulb(object):
    def __init__(self):
        self.state = "off"
    def switchOn(self):
        """switch lights on"""
        self.state = "on"
        return True
    def switchOff(self, *args):
        """switch lights off"""
        self.state = "off"
        return "switchOff got parameters " + str(args)
    def status(self):
        """get lights status, 'on' or 'off'"""
        return self.state

class ExampleLightBulbDevices(remotedevices_server.DeviceClass):
    # Lightbulbs are stateful, read-write devices. The constructor
    # of the base class will set maxRefCount=1, that is, each
    # user much acquire the device exclusively.
    def rescan(self):
        return ["example-lightbulb-0", "example-lightbulb-1"]

    def adopt(self, deviceId):
        """return pair (DeviceObject, DeviceInfo)"""
        d = LightBulb()
        i = remotedevices_server.DeviceInfo(
            id=deviceId,
            type="example-lightbulb",
            sw="",
            hw="",
            display="")
        return d, i

    def abandon(self, deviceInfo, deviceObj):
        pass

class Sensor(object):
    def value(self):
        return 42

class ExampleSensorDevices(remotedevices_server.DeviceClass):
    def __init__(self):
        # Sensors are read-only devices and therefore limiting the
        # number of simultaneous users is unnecessary. Disable
        # reference count limit:
        remotedevices_server.DeviceClass.__init__(self, maxRefCount=-1)

    def rescan(self):
        return ["example-sensor-0"]

    def adopt(self, deviceId):
        """return pair (DeviceObject, DeviceInfo)"""
        d = Sensor()
        i = remotedevices_server.DeviceInfo(
            id=deviceId,
            type="example-sensor",
            sw="",
            hw="",
            display="")
        return d, i

    def abandon(self, deviceInfo, deviceObj):
        pass

remotedevices_server.register_device_class(ExampleLightBulbDevices())
remotedevices_server.register_device_class(ExampleSensorDevices())
