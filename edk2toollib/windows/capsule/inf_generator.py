##
# Module to generate inf files for capsule update based on INF TEMPLATE and
# supplied information (Name, Version, ESRT Guid, Rollback, etc.)
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import os
import logging
import datetime
import re
import uuid


class InfSection(object):
    def __init__(self, name) -> None:
        self.Name = name
        self.Items = []

    def __str__(self) -> str:
        return "\n".join(["[%s]" % self.Name] + self.Items)


class InfGenerator(object):

    ### INF Template ###
    TEMPLATE = r""";
; {Name}.inf
; {DriverVersion}
; Copyright (C) 2019 Microsoft Corporation.  All Rights Reserved.
;
[Version]
Signature="$WINDOWS NT$"
Class=Firmware
ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
Provider=%Provider%
DriverVer={Date},{DriverVersion}
PnpLockdown=1
CatalogFile={Name}.cat

[Manufacturer]
%MfgName% = Firmware,NT{Arch}

[Firmware.NT{Arch}]
%FirmwareDesc% = Firmware_Install,UEFI\RES_{{{EsrtGuid}}}

[Firmware_Install.NT]
CopyFiles = Firmware_CopyFiles
{Rollback}
{FirmwareCopyFilesSection}

[Firmware_Install.NT.Hw]
AddReg = Firmware_AddReg

{FirmwareAddRegSection}

[SourceDisksNames]
1 = %DiskName%

{SourceDisksFilesSection}

[DestinationDirs]
DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\Firmware

[Strings]
; localizable
Provider     = "{Provider}"
MfgName      = "{MfgName}"
FirmwareDesc = "{Description}"
DiskName     = "Firmware Update"

; non-localizable
DIRID_WINDOWS = 10
REG_DWORD     = 0x00010001
"""

    ROLLBACKTEMPLATE = r"""AddReg    = Firmware_DowngradePolicy_Addreg

;override firmware resource update policy to allow downgrade to lower version
[Firmware_DowngradePolicy_Addreg]
HKLM,SYSTEM\CurrentControlSet\Control\FirmwareResources\{{{EsrtGuid}}},Policy,%REG_DWORD%,1
"""

    SUPPORTED_ARCH = {'amd64': 'amd64',
                      'x64': 'amd64',
                      'arm': 'arm',
                      'arm64': 'ARM64',
                      'aarch64': 'ARM64'
                      }

    def __init__(self, name_string, provider, esrt_guid, arch, description_string, version_string, version_hex):
        self.Name = name_string
        self.Provider = provider
        self.EsrtGuid = esrt_guid
        self.Arch = arch
        self.Description = description_string
        self.VersionString = version_string
        self.VersionHex = version_hex
        self._manufacturer = None  # default for optional feature
        self._date = datetime.date.today()
        self._integrityfile = None

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        # test here for invalid chars
        if not (re.compile(r'[\w-]*$')).match(value):
            logging.critical("Name invalid: '%s'", value)
            raise ValueError("Name has invalid chars.")
        self._name = value

    @property
    def Provider(self):
        return self._provider

    @Provider.setter
    def Provider(self, value):
        self._provider = value

    @property
    def Manufacturer(self):
        if(self._manufacturer is None):
            return self.Provider

        return self._manufacturer

    @Manufacturer.setter
    def Manufacturer(self, value):
        self._manufacturer = value

    @property
    def Description(self):
        return self._description

    @Description.setter
    def Description(self, value):
        self._description = value

    @property
    def EsrtGuid(self):
        return self._esrt_guid

    @EsrtGuid.setter
    def EsrtGuid(self, value):
        uuid.UUID(value)  # if this works it is valid...otherwise throws exception
        # todo - make sure it is formatted exactly right
        self._esrt_guid = value

    @property
    def VersionString(self):
        return self._versionstring

    @VersionString.setter
    def VersionString(self, value):
        c = value.count(".")
        if(c < 1) or (c > 3):
            logging.critical("Version string in invalid format.")
            raise ValueError("VersionString must be in format of xx.xx -> xx.xx.xx.xx")
        self._versionstring = value

    @property
    def VersionHex(self):
        return "0x%X" % self._versionhex

    @VersionHex.setter
    def VersionHex(self, value):
        a = int(value, 0)
        if(a > 0xFFFFFFFF):
            logging.critical("VersionHex invalid: '%s'", value)
            raise ValueError("VersionHex must fit within 32bit value range for unsigned integer")
        self._versionhex = a

    @property
    def Arch(self):
        return self._arch

    @Arch.setter
    def Arch(self, value):
        key = value.lower()
        if(key not in InfGenerator.SUPPORTED_ARCH.keys()):
            logging.critical("Arch invalid: '%s'", value)
            raise ValueError("Unsupported Architecture")
        self._arch = InfGenerator.SUPPORTED_ARCH[key]

    @property
    def Date(self):
        return self._date.strftime("%m/%d/%Y")

    @Date.setter
    def Date(self, value):
        if(not isinstance(value, datetime.date)):
            raise ValueError("Date must be a datetime.date object")
        self._date = value

    @property
    def IntegrityFilename(self):
        return str(self._integrityfile) if self._integrityfile is not None else ""

    @IntegrityFilename.setter
    def IntegrityFilename(self, value):
        self._integrityfile = value

    def MakeInf(self, OutputInfFilePath, FirmwareBinFileName, Rollback=False):
        RollbackString = ""
        if(Rollback):
            RollbackString = InfGenerator.ROLLBACKTEMPLATE.format(EsrtGuid=self.EsrtGuid)

        binfilename = os.path.basename(FirmwareBinFileName)

        copy_files = InfSection('Firmware_CopyFiles')
        copy_files.Items.append(binfilename)

        add_reg = InfSection('Firmware_AddReg')
        add_reg.Items.append("HKR,,FirmwareId,,{{{guid}}}".format(guid=self.EsrtGuid))
        add_reg.Items.append("HKR,,FirmwareVersion,%REG_DWORD%,{version}".format(
            version=self.VersionHex))
        add_reg.Items.append("HKR,,FirmwareFilename,,{file_name}".format(file_name=binfilename))

        disks_files = InfSection('SourceDisksFiles')
        disks_files.Items.append("{file_name} = 1".format(file_name=binfilename))

        if self.IntegrityFilename != "":
            copy_files.Items.append(self.IntegrityFilename)
            add_reg.Items.append("HKR,,FirmwareIntegrityFilename,,{file_name}".format(file_name=self.IntegrityFilename))
            disks_files.Items.append("{file_name} = 1".format(file_name=self.IntegrityFilename))

        Content = InfGenerator.TEMPLATE.format(
            Name=self.Name,
            Date=self.Date,
            Arch=self.Arch,
            DriverVersion=self.VersionString,
            EsrtGuid=self.EsrtGuid,
            Provider=self.Provider,
            MfgName=self.Manufacturer,
            Description=self.Description,
            Rollback=RollbackString,
            FirmwareCopyFilesSection=copy_files,
            FirmwareAddRegSection=add_reg,
            SourceDisksFilesSection=disks_files)

        with open(OutputInfFilePath, "w") as f:
            f.write(Content)

        return 0
