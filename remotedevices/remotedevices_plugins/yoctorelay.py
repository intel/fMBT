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
import time
yocto_api = None
yocto_relay = None

idPrefix = "yoctorelay-"

def log(msg):
    remotedevices_server.daemon_log("yoctorelay plugin: %s" % (msg,))

class RelayInterface(object):
    def __init__(self, relay):
        self._relay = relay

    def switch_on(self, duration=None):
        """switch on, if duration is given, switch off after it"""
        self._relay.set_state(1)
        if duration != None:
            time.sleep(duration)
            self.switch_off()

    def switch_off(self, duration=None):
        """switch off, if duration is given, switch off after it"""
        self._relay.set_state(0)
        if duration != None:
            time.sleep(duration)
            self.switch_on()

    def state(self):
        """return relay state, 1 for on, 0 for off"""
        return self._relay.get_state()

class YoctoRelay(remotedevices_server.DeviceClass):
    def __init__(self):
        remotedevices_server.DeviceClass.__init__(self, maxRefCount=-1)
        global yocto_api
        global yocto_relay
        self.status = "error"
        self.relays = {}
        try:
            import yocto_api
            import yocto_relay
            self.status = "ok"

        except ImportError, e:
            log("importing Yocto Relay Python API failed,")
            log("error: %s" % (e,))
            log("make sure Yoctopuse libraries /Sources is in PYTHONPATH")

    def rescan(self):
        if self.status != "ok":
            return []
        self.relays = {}
        errmsg = yocto_api.YRefParam()
        hub_rv = yocto_api.YAPI.RegisterHub("usb", errmsg)
        if hub_rv != yocto_api.YAPI.SUCCESS:
            log("YAPI.RegisterHub returned error %s" % (hub_rv.value,))
        relay = yocto_relay.YRelay.FirstRelay()
        while relay != None:
            self.relays[idPrefix + relay.get_hardwareId()] = relay
            relay = relay.nextRelay()
        return self.relays.keys()

    def adopt(self, deviceId):
        """return pair (DeviceObject, DeviceInfo)"""
        d = RelayInterface(self.relays[deviceId])
        i = remotedevices_server.DeviceInfo(
            id=deviceId,
            type="yocto-relay",
            sw="",
            hw="",
            display="")
        return d, i

    def abandon(self, deviceInfo, deviceObj):
        pass

remotedevices_server.register_device_class(YoctoRelay())
