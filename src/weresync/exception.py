#Copyright 2016 Daniel Manila
#
#Licensed under the Apache License, Version 2.0 (the "License");
#you may not use this file except in compliance with the License.
#You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
#Unless required by applicable law or agreed to in writing, software
#distributed under the License is distributed on an "AS IS" BASIS,
#WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#See the License for the specific language governing permissions and
#limitations under the License.
"""Exceptions used by WereSync"""

class DeviceError(Exception):
    """Exception thrown to show errors caused by an issue with a specific device."""
    def __init__(self, device, message, errors=None):
        self.device = device
        self.message = message
        self.errors = errors

class CopyError(Exception):
    """Exception thrown to show errors caused by an issue copying data, usually both devices face the issue."""
    def __init__(self, message, errors=None):
        self.message = message
        self.errors = errors

class UnsupportedDeviceError(Exception):
    """Exception thrown to show that action is not supported on the partition table type of the device."""
    def __init__(self, message):
        self.message = message
