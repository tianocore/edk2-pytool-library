##
# Module to generate inf files for capsule update. Supports targeting
# multiple ESRT nodes with the same INF.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import textwrap
import re
import uuid
from datetime import datetime
from typing import Optional

SUPPORTED_ARCH = {'amd64': 'amd64',
                  'x64': 'amd64',
                  'arm': 'arm',
                  'arm64': 'ARM64',
                  'aarch64': 'ARM64'
                  }


class InfHeader(object):
    def __init__(self, Name: str, VersionStr: str, CreationDate: str, Arch: str, Provider: str, Manufacturer: str,
                 InfStrings: 'InfStrings') -> None:
        '''Instantiate an INF header object.
        This object represents the INF header at the start of the INF file.

        Name         - specifies the name for the INF package
        VersionStr   - specifies the version as string in dot-tuple format (e.g. "4.15.80.0")
        CreationDate - specifies the INF date as a string in MM/DD/YYYY format (e.g "01/01/2021")
        Arch         - specifies the architecture as a string (e.g. "amd64")
        Provider     - specifies the provider as a string (e.g. "Firmware Provider")
        Manufacturer - Specifies the manufacturer as a string (e.g. "Firmware Manufacturer")
        InfStrings   - An InfStrings object representing the "Strings" section of this INF file.
        '''
        self.Name = Name
        self.VersionStr = VersionStr
        self.Date = CreationDate
        self.Arch = Arch
        InfStrings.AddLocalizableString("Provider", Provider)
        InfStrings.AddLocalizableString("MfgName", Manufacturer)

    @property
    def Name(self):
        return self._name

    @Name.setter
    def Name(self, value):
        # test here for invalid chars
        if not (re.compile(r'[\w-]*$')).match(value):
            raise ValueError("Name has invalid chars.")
        self._name = value

    @property
    def VersionStr(self):
        return self._versionstr

    @VersionStr.setter
    def VersionStr(self, value):
        c = value.count(".")
        if (c < 1) or (c > 3):
            raise ValueError("VersionString must be in format of xx.xx -> xx.xx.xx.xx")
        self._versionstr = value

    @property
    def Date(self):
        return self._date

    @Date.setter
    def Date(self, value):
        self._date = datetime.strptime(value, "%m/%d/%Y").strftime("%m/%d/%Y")

    @property
    def Arch(self):
        return self._arch

    @Arch.setter
    def Arch(self, value):
        key = value.lower()
        if (key not in SUPPORTED_ARCH.keys()):
            raise ValueError("Unsupported Architecture")
        self._arch = SUPPORTED_ARCH[key]

    def __str__(self) -> str:
        '''Return the string representation of this InfHeader object'''
        return textwrap.dedent(f"""\
            ;
            ; {self.Name}
            ; {self.VersionStr}
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer={self.Date},{self.VersionStr}
            PnpLockdown=1
            CatalogFile={self.Name}.cat

            [Manufacturer]
            %MfgName% = Firmware,NT{self.Arch}

            """)


class InfFirmware(object):
    def __init__(self, Tag: str, Description: str, EsrtGuid: str, VersionInt: str, FirmwareFile: str,
                 InfStrings: 'InfStrings', InfSourceFiles: 'InfSourceFiles', Rollback: Optional[bool] = False,
                 IntegrityFile: Optional[str] = None) -> None:
        '''Instantiate an INF firmware object.
        This object represents individual firmware sections within the INF.

        Tag             - A string that uniquely identifies this firmware (e.g. "Firmware0")
        Description     - A description of the firmware (e.g. "UEFI Firmware")
        EsrtGuid        - ESRT GUID for this firmware in string format. (e.g. "34e094e9-4079-44cd-9450-3f2cb7824c97")
        VersionInt      - Version as an integer in string format (e.g. "1234" or "0x04158000")
        FirmwareFile    - Filename (basename only) of the firmware payload file (e.g. "Firmware1234.bin")
        InfStrings      - An InfStrings object representing the "Strings" section of this INF file.
        InfSourceFiles  - An InfSourceFiles object representing the "SourceDisks*" sections of this INF file.
        Rollback        - Specifies whether this firmware should be enabled for rollback (optional, default: False)
        IntegrityFile   - Filename (basename only) of the integrity file associated with this firmware (e.g.
                          "integrity123.bin"). Optional - if not specified, no integrity file will be included.
        '''
        self.Tag = Tag
        self.Description = Description
        self.EsrtGuid = EsrtGuid
        self.VersionInt = VersionInt
        self.FirmwareFile = FirmwareFile
        InfSourceFiles.AddFile(FirmwareFile)
        self.Rollback = Rollback
        self.IntegrityFile = IntegrityFile
        if (self.IntegrityFile is not None):
            InfSourceFiles.AddFile(IntegrityFile)
        InfStrings.AddNonLocalizableString("REG_DWORD", "0x00010001")

    @property
    def Tag(self):
        return self._tag

    @Tag.setter
    def Tag(self, value):
        # test here for invalid chars
        if not (re.compile(r'[\w-]*$')).match(value):
            raise ValueError("Tag has invalid chars.")
        self._tag = value

    @property
    def EsrtGuid(self):
        return self._esrt_guid

    @EsrtGuid.setter
    def EsrtGuid(self, value):
        uuid.UUID(value)
        self._esrt_guid = value

    @property
    def VersionInt(self):
        return self._version_int

    @VersionInt.setter
    def VersionInt(self, value):
        self._version_int = int(value, base=0)

    def __str__(self) -> str:
        '''Return the string representation of this InfFirmware object'''
        # build rollback string, if required.
        if (self.Rollback):
            RollbackStr = textwrap.dedent(f"""\
                AddReg = {self.Tag}_DowngradePolicy_AddReg

                [{self.Tag}_DowngradePolicy_AddReg]
                HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{{self.EsrtGuid}}},Policy,%REG_DWORD%,1
                """)
        else:
            RollbackStr = ""

        # build integrity file string, if required.
        if (self.IntegrityFile is not None):
            IntegrityFile = f"{self.IntegrityFile}\n"
            IntegrityFileReg = f"HKR,,FirmwareIntegrityFilename,,{self.IntegrityFile}\n"
        else:
            IntegrityFile = ""
            IntegrityFileReg = ""

        outstr = textwrap.dedent(f"""\
            [{self.Tag}_Install.NT]
            CopyFiles = {self.Tag}_CopyFiles
            """)
        outstr += RollbackStr
        outstr += textwrap.dedent(f"""
            [{self.Tag}_CopyFiles]
            {self.FirmwareFile}
            """)
        outstr += IntegrityFile
        outstr += textwrap.dedent(f"""
            [{self.Tag}_Install.NT.Hw]
            AddReg = {self.Tag}_AddReg

            [{self.Tag}_AddReg]
            HKR,,FirmwareId,,{{{self.EsrtGuid}}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x{self.VersionInt:X}
            HKR,,FirmwareFilename,,{self.FirmwareFile}
            """)
        outstr += IntegrityFileReg + "\n"
        return outstr


class InfFirmwareSections(object):
    def __init__(self, Arch: str, InfStrings: 'InfStrings') -> None:
        '''Instantiate an INF firmware sections object.
        This object represents a collection of firmware sections and associated common metadata.

        Arch        - specifies the architecture as a string (e.g. "amd64")
        InfStrings  - An InfStrings object representing the "Strings" section of this INF file.
        '''
        self.Arch = Arch
        self.Sections = {}
        self.InfStrings = InfStrings

    @property
    def Arch(self):
        return self._arch

    @Arch.setter
    def Arch(self, value):
        key = value.lower()
        if (key not in SUPPORTED_ARCH.keys()):
            raise ValueError("Unsupported Architecture")
        self._arch = SUPPORTED_ARCH[key]

    def AddSection(self, InfFirmware: InfFirmware) -> None:
        '''Adds an InfFirmware section object to the set of firmware sections in this InfFirmwareSections object.

        InfFirmware - an InfFirmware object representing a firmware section to be added to this collection of sections.
        '''
        self.Sections[InfFirmware.Tag] = InfFirmware
        self.InfStrings.AddLocalizableString(f"{InfFirmware.Tag}Desc", InfFirmware.Description)

    def __str__(self) -> str:
        '''
        Return the string representation of this InfFirmwareSections object (including any InfFirmware objects in it)
        '''
        firmwareStr = f"[Firmware.NT{self.Arch}]\n"
        for InfFirmware in self.Sections.values():
            firmwareStr += f"%{InfFirmware.Tag}Desc% = {InfFirmware.Tag}_Install,UEFI\\RES_{{{InfFirmware.EsrtGuid}}}\n"
        firmwareStr += "\n"
        for InfFirmware in self.Sections.values():
            firmwareStr += str(InfFirmware)
        return firmwareStr


class InfSourceFiles(object):
    def __init__(self, DiskName: str, InfStrings: 'InfStrings') -> None:
        '''Instantiate an INF source files object.
        This object represents the collection of source files that are referenced by other sections of the INF.

        DiskName    - Specifies the DiskName as a string (e.g. "FirmwareUpdate")
        InfStrings  - An InfStrings object representing the "Strings" section of this INF file.
        '''
        self.Files = []
        InfStrings.AddLocalizableString('DiskName', DiskName)
        InfStrings.AddNonLocalizableString('DIRID_WINDOWS', "10")

    def AddFile(self, Filename: str) -> None:
        '''Adds a new file to this InfSourceFiles object

        Filename - Filename (basename only) of the file to be added. (e.g. "Firmware1234.bin")
        '''
        # test here for invalid chars. For filenames, this permits a-z, A-Z, 0-9, _, -, and . characters.
        if not (re.compile(r'[\.\w-]*$')).match(Filename):
            raise ValueError("Filename has invalid chars.")

        if (Filename not in self.Files):
            self.Files.append(Filename)

    def __str__(self) -> str:
        '''Return the string representation of this InfSourceFIles object'''
        Files = ''.join("{0} = 1\n".format(file) for file in self.Files)
        outstr = textwrap.dedent("""\
            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            """)
        outstr += Files
        outstr += textwrap.dedent("""
            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

            """)
        return outstr


class InfStrings(object):
    def __init__(self) -> None:
        '''Instantiate an INF strings object.
        This object represents the collection of strings (localizable or non-localizable) that are referenced by other
        sections of the INF.
        '''
        self.LocalizableStrings = {}
        self.NonLocalizableStrings = {}

    def AddLocalizableString(self, Key: str, Value: str) -> None:
        '''Add a Localizable string to the collection of strings for this INF.

        Key     - the name of this string as it is used in the INF (e.g. "MfgName"). Note: the INF will typically
                  reference this string using % as delimiters (e.g. "%MfgName%"). Do not include the % characters
                  when calling this routine.
        Value   - the value of the localizable string as a string (e.g. "Firmware Manufacturer")
        '''
        # The inf spec says keys here should be "letters, digits, and/or other explicitly visible characters".
        # for simplicity, this just enforces that it must be a string that matches \w+
        if not (re.compile(r'\w+$')).match(Key):
            raise ValueError("Key has invalid chars.")
        self.LocalizableStrings[Key] = Value

    def AddNonLocalizableString(self, Key: str, Value: str) -> None:
        '''Add a Non-Localizable string to the collection of strings for this INF.

        Key     - the name of this string as it is used in the INF (e.g. "REG_DWORD"). Note: the INF will typically
                  reference this string using % as delimiters (e.g. "%REG_DWORD%"). Do not include the % characters
                  when calling this routine.
        Value   - the value of the non-localizable string as a string (e.g. "0x00010001")
        '''
        # The inf spec says keys here should be "letters, digits, and/or other explicitly visible characters".
        # for simplicity, this just enforces that it must be a string that matches \w+
        if not (re.compile(r'\w+$')).match(Key):
            raise ValueError("Key has invalid chars.")
        self.NonLocalizableStrings[Key] = Value

    def __str__(self) -> str:
        '''Return the string representation of this InfStrings object'''
        LocalizedStrings = ""
        LongestKey = max(len(Key) for Key in self.LocalizableStrings.keys())
        for (Key, Value) in self.LocalizableStrings.items():
            LocalizedStrings += '{0:{width}} = "{1}"\n'.format(Key, Value, width=LongestKey)

        NonLocalizedStrings = ""
        LongestKey = max(len(Key) for Key in self.NonLocalizableStrings.keys())
        for (Key, Value) in self.NonLocalizableStrings.items():
            NonLocalizedStrings += "{0:{width}} = {1}\n".format(Key, Value, width=LongestKey)

        outstr = textwrap.dedent("""\
            [Strings]
            ; localizable
            """)
        outstr += LocalizedStrings
        outstr += textwrap.dedent("""
            ; non-localizable
            """)
        outstr += NonLocalizedStrings
        return outstr


class InfFile(object):
    def __init__(self, Name: str, VersionStr: str, CreationDate: str, Provider: str, ManufacturerName: str,
                 Arch: Optional[str] = 'amd64', DiskName: Optional[str] = "Firmware Update") -> None:
        '''Instantiate an INF file object.
        This object represents the entire INF file.

        Users of this implementation are primarily expected to interact with instances of this class.

        Name         - specifies the name for the INF package
        VersionStr   - specifies the version as string in dot-tuple format (e.g. "4.15.80.0")
        CreationDate - specifies the INF date as a string in MM/DD/YYYY format (e.g "01/01/2021")
        Provider     - specifies the provider as a string (e.g. "Firmware Provider")
        Manufacturer - Specifies the manufacturer as a string (e.g. "Firmware Manufacturer")
        Arch         - specifies the architecture as a string. Optional, defaults to "amd64".
        DiskName     - specifies the "Disk Name" for this update. Optional, defaults to "Firmware Update".
        '''
        self.InfStrings = InfStrings()
        self.InfSourceFiles = InfSourceFiles(DiskName, self.InfStrings)
        self.InfHeader = InfHeader(Name, VersionStr, CreationDate, Arch, Provider, ManufacturerName, self.InfStrings)
        self.InfFirmwareSections = InfFirmwareSections(Arch, self.InfStrings)

    def AddFirmware(self, Tag: str, Description: str, EsrtGuid: str, VersionInt: str, FirmwareFile: str,
                    Rollback: Optional[bool] = False, IntegrityFile: Optional[str] = None) -> None:
        '''Adds a firmware target to the INF.

        Tag             - A string that uniquely identifies this firmware (e.g. "Firmware0")
        Description     - A description of the firmware (e.g. "UEFI Firmware")
        EsrtGuid        - ESRT GUID for this firmware in string format. (e.g. "34e094e9-4079-44cd-9450-3f2cb7824c97")
        VersionInt      - Version as an integer in string format (e.g. "1234" or "0x04158000")
        FirmwareFile    - Filename (basename only) of the firmware payload file (e.g. "Firmware1234.bin")
        Rollback        - Specifies whether this firmware should be enabled for rollback (optional, default: False)
        IntegrityFile   - Filename (basename only) of the integrity file associated with this firmware (e.g.
                          "integrity123.bin"). Optional - if not specified, no integrity file will be included.
        '''
        firmwareSection = InfFirmware(Tag, Description, EsrtGuid, VersionInt, FirmwareFile,
                                      self.InfStrings, self.InfSourceFiles, Rollback, IntegrityFile)
        self.InfFirmwareSections.AddSection(firmwareSection)

    def __str__(self) -> str:
        '''
        Returns the string representation of this InfFile object. The resulting string is suitable for writing to an
        INF file for inclusion in a capsule package.'''
        return str(self.InfHeader) + str(self.InfFirmwareSections) + str(self.InfSourceFiles) + str(self.InfStrings)
