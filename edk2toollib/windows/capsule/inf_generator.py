##
# Module to generate inf files for capsule update based on INF TEMPLATE and
# supplied information (Name, Version, ESRT Guid, Rollback, etc.)
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module to generate inf files for capsule update based on an INF template.

Uses supplied information such as Name, Version, ESRT Guid, Rollback, etc.
"""
import datetime
import logging
import os
import re
import uuid


class InfSection(object):
    """Object representing an INF Section."""
    def __init__(self, name) -> None:
        """Inits the object."""
        self.Name = name
        self.Items = []

    def __str__(self) -> str:
        """Returns the string representation of the object.

        Returns:
            (str): string representation of the object.
        """
        return "\n".join(["[%s]" % self.Name] + self.Items)


class InfGenerator(object):
    """An object that generates an INF file from data it is initialized with."""
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
%MfgName% = Firmware,NT{Arch}.10.0...16299

[Firmware.NT{Arch}.10.0...16299]
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
DefaultDestDir = 13

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
        """Inits the object with data necessary to generate an INF file.

        Args:
            name_string (str): Name
            provider (str): Provider
            esrt_guid (str): stringified guid, will be converted
            arch (str): architecture
            description_string (str): description
            version_string (str): version
            version_hex (int): version
        """
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
        """Getter for the Name Attribute."""
        return self._name

    @Name.setter
    def Name(self, value):
        """Setter for the Name Attribute.

        Raises:
            (ValueError): Invalid Characters in name
        """
        # test here for invalid chars
        if not (re.compile(r'[\w-]*$')).match(value):
            logging.critical("Name invalid: '%s'", value)
            raise ValueError("Name has invalid chars.")
        self._name = value

    @property
    def Provider(self):
        """Getter for the Provider Attribute."""
        return self._provider

    @Provider.setter
    def Provider(self, value):
        """Setter for the Provider Attribute."""
        self._provider = value

    @property
    def Manufacturer(self):
        """Getter for the Manufacturer Attribute.

        NOTE: Returns Provider attribute if Manufacturer attribute is not set.
        """
        if (self._manufacturer is None):
            return self.Provider

        return self._manufacturer

    @Manufacturer.setter
    def Manufacturer(self, value):
        """Setter for the Manufacturer Attribute."""
        self._manufacturer = value

    @property
    def Description(self):
        """Getter for the Description Attribute."""
        return self._description

    @Description.setter
    def Description(self, value):
        """Setter for the Description Attribute."""
        self._description = value

    @property
    def EsrtGuid(self):
        """Getter for the EsrtGuid Attribute."""
        return self._esrt_guid

    @EsrtGuid.setter
    def EsrtGuid(self, value):
        """Setter for the EsrtGuid Attribute.

        Raises:
            (Exception): Invalid value
        """
        uuid.UUID(value)  # if this works it is valid...otherwise throws exception
        # todo - make sure it is formatted exactly right
        self._esrt_guid = value

    @property
    def VersionString(self):
        """Getter for VersionString attribute."""
        return self._versionstring

    @VersionString.setter
    def VersionString(self, value):
        """Setter for the VersionString attribute.

        Raises:
            (ValueError): Invalid format
        """
        c = value.count(".")
        if (c < 1) or (c > 3):
            logging.critical("Version string in invalid format.")
            raise ValueError("VersionString must be in format of xx.xx -> xx.xx.xx.xx")
        self._versionstring = value

    @property
    def VersionHex(self):
        """Getter for the VersionHex attribute."""
        return "0x%X" % self._versionhex

    @VersionHex.setter
    def VersionHex(self, value):
        """Setter for the VersionHex attribute.

        Raises:
            (ValueError): hex does not fit in a 32but uint
        """
        a = int(value, 0)
        if (a > 0xFFFFFFFF):
            logging.critical("VersionHex invalid: '%s'", value)
            raise ValueError("VersionHex must fit within 32bit value range for unsigned integer")
        self._versionhex = a

    @property
    def Arch(self):
        """Getter for the Arch property."""
        return self._arch

    @Arch.setter
    def Arch(self, value):
        """Setter for the Arch Attribute.

        Raises:
            (ValueError): Unsupported Arch
        """
        key = value.lower()
        if (key not in InfGenerator.SUPPORTED_ARCH.keys()):
            logging.critical("Arch invalid: '%s'", value)
            raise ValueError("Unsupported Architecture")
        self._arch = InfGenerator.SUPPORTED_ARCH[key]

    @property
    def Date(self):
        """Getter for the date attribute.

        Formats to a m/d/y str before returning
        """
        return self._date.strftime("%m/%d/%Y")

    @Date.setter
    def Date(self, value):
        """Setter for the Date attribute.

        Raises:
            (ValueError): not a datetime.date object
        """
        if (not isinstance(value, datetime.date)):
            raise ValueError("Date must be a datetime.date object")
        self._date = value

    @property
    def IntegrityFilename(self):
        """Getter for the Integrity File Name.

        Transforms value into string.
        """
        return str(self._integrityfile) if self._integrityfile is not None else ""

    @IntegrityFilename.setter
    def IntegrityFilename(self, value):
        """Setter for the IntegrityFile name."""
        self._integrityfile = value

    def MakeInf(self, OutputInfFilePath, FirmwareBinFileName, Rollback=False):
        """Generates the INF with provided information.

        Args:
            OutputInfFilePath (PathLike): Path to existing file
            FirmwareBinFileName (str): File Name
            Rollback (:obj:`bool`, optional): Generate with Rollback template
        """
        RollbackString = ""
        if (Rollback):
            RollbackString = InfGenerator.ROLLBACKTEMPLATE.format(EsrtGuid=self.EsrtGuid)

        binfilename = os.path.basename(FirmwareBinFileName)

        copy_files = InfSection('Firmware_CopyFiles')
        copy_files.Items.append(binfilename)

        add_reg = InfSection('Firmware_AddReg')
        add_reg.Items.append("HKR,,FirmwareId,,{{{guid}}}".format(guid=self.EsrtGuid))
        add_reg.Items.append("HKR,,FirmwareVersion,%REG_DWORD%,{version}".format(
            version=self.VersionHex))
        add_reg.Items.append("HKR,,FirmwareFilename,,%13%\\{file_name}".format(file_name=binfilename))

        disks_files = InfSection('SourceDisksFiles')
        disks_files.Items.append("{file_name} = 1".format(file_name=binfilename))

        if self.IntegrityFilename != "":
            copy_files.Items.append(self.IntegrityFilename)
            add_reg.Items.append("HKR,,FirmwareIntegrityFilename,,%13%\\{file_name}".format(file_name=self.IntegrityFilename))
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
