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
import fmbtandroid
import subprocess

_serialNumberPrefix = ""


class AndroidDevices(remotedevices_server.DeviceClass):
    def rescan(self):
        return ["%s%s" % (_serialNumberPrefix, sn)
                for sn in fmbtandroid.listSerialNumbers()]

    def adopt(self, deviceId):
        """return pair (DeviceObject, DeviceInfo)"""
        if not deviceId.startswith(_serialNumberPrefix):
            raise ValueError("invalid device id")
        serialNumber = deviceId[len(_serialNumberPrefix):]
        d = fmbtandroid.Device(serialNumber)
        i = remotedevices_server.DeviceInfo(id=deviceId,
                       type="android",
                       sw=d.platformVersion(),
                       hw="", # no hw data
                       display="%sx%s" % d.connection().recvScreenSize())
        def _adb(adbcmd, timeout=60):
            return subprocess.check_output(
                ["timeout", "-k", "1", str(timeout),
                 "adb", "-s", serialNumber] + adbcmd)
        d.adb = _adb
        return d, i

    def abandon(self, deviceInfo, deviceObj):
        try:
            deviceObj.close()
        except Exception:
            pass

remotedevices_server.register_device_class(AndroidDevices())
