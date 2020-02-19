## @file
# Script to generate Cat files for capsule update based on supplied inf file.
# This uses the winsdk and the command line tool Inf2Cat.exe
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import logging
from edk2toollib.utility_functions import RunCmd
from edk2toollib.windows.locate_tools import FindToolInWinSdk


class CatGenerator(object):
    SUPPORTED_OS = {'win10': '10',
                    '10': '10',
                    '10_au': '10_AU',
                    '10_rs2': '10_RS2',
                    '10_rs3': '10_RS3',
                    '10_rs4': '10_RS4',
                    'server10': 'Server10',
                    'server2016': 'Server2016',
                    'serverrs2': 'ServerRS2',
                    'serverrs3': 'ServerRS3',
                    'serverrs4': 'ServerRS4'
                    }

    def __init__(self, arch, os):
        self.Arch = arch
        self.OperatingSystem = os

    @property
    def Arch(self):
        return self._arch

    @Arch.setter
    def Arch(self, value):
        value = value.lower()
        if(value == "x64") or (value == "amd64"):  # support amd64 value so INF and CAT tools can use same arch value
            self._arch = "X64"
        elif(value == "arm"):
            self._arch = "ARM"
        elif(value == "arm64") or (value == "aarch64"):  # support UEFI defined aarch64 value as well
            self._arch = "ARM64"
        else:
            logging.critical("Unsupported Architecture: %s", value)
            raise ValueError("Unsupported Architecture")

    @property
    def OperatingSystem(self):
        return self._operatingsystem

    @OperatingSystem.setter
    def OperatingSystem(self, value):
        key = value.lower()
        if(key not in CatGenerator.SUPPORTED_OS.keys()):
            logging.critical("Unsupported Operating System: %s", key)
            raise ValueError("Unsupported Operating System")
        self._operatingsystem = CatGenerator.SUPPORTED_OS[key]

    def MakeCat(self, OutputCatFile, PathToInf2CatTool=None):
        # Find Inf2Cat tool
        if(PathToInf2CatTool is None):
            PathToInf2CatTool = FindToolInWinSdk("Inf2Cat.exe")
        # check if exists
        if PathToInf2CatTool is None or not os.path.exists(PathToInf2CatTool):
            raise Exception("Can't find Inf2Cat on this machine.  Please install the Windows 10 WDK - "
                            "https://developer.microsoft.com/en-us/windows/hardware/windows-driver-kit")

        OutputFolder = os.path.dirname(OutputCatFile)
        # Make Cat file
        cmd = "/driver:. /os:" + self.OperatingSystem + "_" + self.Arch + " /verbose /uselocaltime"
        ret = RunCmd(PathToInf2CatTool, cmd, workingdir=OutputFolder)
        if(ret != 0):
            raise Exception("Creating Cat file Failed with errorcode %d" % ret)
        if(not os.path.isfile(OutputCatFile)):
            raise Exception("CAT file (%s) not created" % OutputCatFile)

        return 0
