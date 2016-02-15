# CMSIS-DAP Interface Firmware
# Copyright (c) 2009-2013 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from __future__ import absolute_import
import os
import info
import re
import firmware


def load_bundle_from_release(directory):
    """ Return a bundle representing the given build"""
    return ReleaseFirmwareBundle(directory)


def load_bundle_from_project(tool='uvision'):
    """
    Return a bundle for the given tool

    Note - This does not build the project.  It only returns the
    firmware that has already been built.
    """
    self_path = os.path.abspath(__file__)
    test_dir = os.path.dirname(self_path)
    daplink_dir = os.path.dirname(test_dir)
    assert os.path.basename(test_dir) == 'test', 'The script "%s" must be ' \
        'located in the "test" directory of daplink to work correctly.'
    return ProjectFirmwareBundle(daplink_dir, tool)


class ReleaseFirmwareBundle(firmware.FirmwareBundle):
    """Class to abstract access a formal build as a bundle"""

    def __init__(self, directory):
        bundle_contents = os.listdir(directory)
        firmware_list = []
        for name in bundle_contents:
            path = directory + os.sep + name
            if os.path.isdir(path):
                daplink_firmware = DAPLinkFirmware(name, self, path)
                if daplink_firmware.valid:
                    firmware_list.append(daplink_firmware)
            elif os.path.isfile(path):
                # Parse relevent info
                pass
            else:
                assert False
        self._firmware_list = firmware_list

    def get_firmware_list(self):
        return self._firmware_list

    @property
    def build_sha(self):
        raise NotImplementedError()

    @property
    def build_local_mods(self):
        raise NotImplementedError()


class ProjectFirmwareBundle(firmware.FirmwareBundle):
    """Class to abstract access to daplink's build directory as a bundle"""

    def __init__(self, directory, tool):
        tool_dir = os.path.abspath(directory + os.sep + 'projectfiles' +
                                   os.sep + tool)
        project_dir_list = os.listdir(tool_dir)
        firmware_list = []
        for name in project_dir_list:
            build_dir = tool_dir + os.sep + name + os.sep + 'build'
            daplink_firmware = DAPLinkFirmware(name, self, build_dir)
            if daplink_firmware.valid:
                firmware_list.append(daplink_firmware)
        self._firmware_list = firmware_list

    def get_firmware_list(self):
        return self._firmware_list

    @property
    def build_sha(self):
        raise NotImplementedError()

    @property
    def build_local_mods(self):
        raise NotImplementedError()


class DAPLinkFirmware(firmware.Firmware):
    """Class to abstract access to a daplink firmware image"""

    _IF_RE = re.compile("^([a-z0-9]+)_([a-z0-9_]+)_if$")
    _BL_RE = re.compile("^([a-z0-9]+)_bl$")

    def __init__(self, name, bundle, directory):
        self._name = name
        self._bundle = bundle
        self._directory = directory
        self._valid = False

        # Set type
        self._type = None
        string_hdk = None
        match = self._IF_RE.match(name)
        if match:
            string_hdk = match.group(1)
            self._type = self.TYPE.INTERFACE
        match = self._BL_RE.match(name)
        if match:
            string_hdk = match.group(1)
            self._type = self.TYPE.BOOTLOADER
        if self._type is None:
            assert False, 'Bad project name "%s"' % name

        # Set HDK
        assert string_hdk in info.HDK_STRING_TO_ID, 'Unknown HDK "%s" must ' \
            'be added to HDK_STRING_TO_ID in info.py' % string_hdk
        self._hdk_id = info.HDK_STRING_TO_ID[string_hdk]

        # Set board ID
        self._board_id = None
        if name in info.FIRMWARE_NAME_TO_BOARD_ID:
            self._board_id = info.FIRMWARE_NAME_TO_BOARD_ID[name]
        else:
            assert self._type is not self.TYPE.INTERFACE, 'Unknown board ' \
                '"%s" must be added to FIRMWARE_NAME_TO_BOARD_ID in '      \
                'info.py' % name

        # Set file paths
        self._bin_path = self._directory + os.sep + '%s_crc.bin' % name
        self._hex_path = self._directory + os.sep + '%s_crc.hex' % name
        self._elf_path = self._directory + os.sep + '%s.axf' % name
        self._bin_path = os.path.abspath(self._bin_path)
        self._hex_path = os.path.abspath(self._hex_path)
        self._elf_path = os.path.abspath(self._elf_path)
        if not os.path.isfile(self._bin_path):
            return  # Failure
        if not os.path.isfile(self._hex_path):
            return  # Failure
        if not os.path.isfile(self._elf_path):
            return  # Failure

        self._valid = True

    def __str__(self):
        board_id = self.board_id
        if board_id is None:
            board_id = 0
        return "Name=%s Board ID=0x%04x HDK ID=0x%08x" % (self.name,
                                                          board_id,
                                                          self.hdk_id)

    @property
    def valid(self):
        """Set to True if the firmware is valid"""
        return self._valid

    @property
    def name(self):
        return self._name

    @property
    def hdk_id(self):
        return self._hdk_id

    @property
    def board_id(self):
        return self._board_id

    @property
    def type(self):
        return self._type

    @property
    def bin_path(self):
        return self._bin_path

    @property
    def hex_path(self):
        return self._hex_path

    @property
    def elf_path(self):
        return self._elf_path