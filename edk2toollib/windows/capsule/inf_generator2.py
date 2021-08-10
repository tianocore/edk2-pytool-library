##
# Module to generate inf files for capsule update. Supports targeting
# multiple ESRT nodes with the same INF.
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import textwrap


class InfHeader(object):
    def __init__(self, name, versionStr, date, arch, provider, mfgname, infstrings):
        self.name = name
        self.versionStr = versionStr
        self.date = date
        self.arch = arch
        infstrings.addLocalizableString("Provider", provider)
        infstrings.addLocalizableString("MfgName", mfgname)

    def __str__(self):
        return textwrap.dedent(f"""\
            ;
            ; {self.name}
            ; {self.versionStr}
            ; Copyright (C) Microsoft Corporation. All Rights Reserved.
            ;
            [Version]
            Signature="$WINDOWS NT$"
            Class=Firmware
            ClassGuid={{f2e7dd72-6468-4e36-b6f1-6488f42c1b52}}
            Provider=%Provider%
            DriverVer={self.date},{self.versionStr}
            PnpLockdown=1
            CatalogFile={self.name}.cat

            [Manufacturer]
            %MfgName% = Firmware,NT{self.arch}

            """)


class InfFirmware(object):
    def __init__(self, tag, desc, esrtGuid, versionInt, firmwareFile, infStrings, infSourceFiles,
                 rollback=False, integrityFile=None):
        self.tag = tag
        self.desc = desc
        self.esrtGuid = esrtGuid
        self.versionInt = int(versionInt, base=0)
        self.firmwareFile = firmwareFile
        infSourceFiles.addFile(firmwareFile)
        self.rollback = rollback
        self.integrityFile = integrityFile
        if (self.integrityFile is not None):
            infSourceFiles.addFile(integrityFile)
        infStrings.addNonlocalizableString("REG_DWORD", "0x00010001")

    def __str__(self):
        # build rollback string, if required.
        if (self.rollback):
            rollbackStr = textwrap.dedent(f"""\
                AddReg = {self.tag}_DowngradePolicy_AddReg

                [{self.tag}_DowngradePolicy_AddReg]
                HKLM,SYSTEM\\CurrentControlSet\\Control\\FirmwareResources\\{{{self.esrtGuid}}},Policy,%REG_DWORD%,1
                """)
        else:
            rollbackStr = ""

        # build integrity file string, if required.
        if (self.integrityFile is not None):
            integrityFile = f"{self.integrityFile}\n"
            integrityFileReg = f"HKR,,FirmwareIntegrityFilename,,{self.integrityFile}\n"
        else:
            integrityFile = ""
            integrityFileReg = ""

        outstr = textwrap.dedent(f"""\
            [{self.tag}_Install.NT]
            CopyFiles = {self.tag}_CopyFiles
            """)
        outstr += rollbackStr
        outstr += textwrap.dedent(f"""
            [{self.tag}_CopyFiles]
            {self.firmwareFile}
            """)
        outstr += integrityFile
        outstr += textwrap.dedent(f"""
            [{self.tag}_Install.NT.Hw]
            AddReg = {self.tag}_AddReg

            [{self.tag}_AddReg]
            HKR,,FirmwareId,,{{{self.esrtGuid}}}
            HKR,,FirmwareVersion,%REG_DWORD%,0x{self.versionInt:X}
            HKR,,FirmwareFilename,,{self.firmwareFile}
            """)
        outstr += integrityFileReg + "\n"
        return outstr


class InfFirmwareSections(object):
    def __init__(self, arch, infstrings):
        self.arch = arch
        self.sections = {}
        self.infstrings = infstrings

    def AddSection(self, infFirmware):
        self.sections[infFirmware.tag] = infFirmware
        self.infstrings.addLocalizableString(f"{infFirmware.tag}Desc", infFirmware.desc)

    def __str__(self):
        firmwareStr = f"[Firmware.NT{self.arch}]\n"
        for (infFirmware) in self.sections.values():
            firmwareStr += f"%{infFirmware.tag}Desc% = {infFirmware.tag}_Install,UEFI\\RES_{{{infFirmware.esrtGuid}}}\n"
        firmwareStr += "\n"
        for (infFirmware) in self.sections.values():
            firmwareStr += str(infFirmware)

        return firmwareStr


class InfSourceFiles(object):
    def __init__(self, diskname, infstrings):
        self.files = []
        infstrings.addLocalizableString('DiskName', diskname)
        infstrings.addNonlocalizableString('DIRID_WINDOWS', "10")

    def addFile(self, filename):
        if (filename not in self.files):
            self.files.append(filename)

    def __str__(self):
        files = ''.join("{0} = 1\n".format(file) for file in self.files)
        outstr = textwrap.dedent("""\
            [SourceDisksNames]
            1 = %DiskName%

            [SourceDisksFiles]
            """)
        outstr += files
        outstr += textwrap.dedent("""
            [DestinationDirs]
            DefaultDestDir = %DIRID_WINDOWS%,Firmware ; %SystemRoot%\\Firmware

            """)
        return outstr


class InfStrings(object):
    def __init__(self):
        self.localizableStrings = {}
        self.nonlocalizableStrings = {}

    def addLocalizableString(self, key, value):
        self.localizableStrings[key] = value

    def addNonlocalizableString(self, key, value):
        self.nonlocalizableStrings[key] = value

    def __str__(self):
        localizedStrings = ""
        longestKey = max(len(key) for key in self.localizableStrings.keys())
        for (key, value) in self.localizableStrings.items():
            localizedStrings += '{0:{width}} = "{1}"\n'.format(key, value, width=longestKey)

        nonlocalizedStrings = ""
        longestKey = max(len(key) for key in self.nonlocalizableStrings.keys())
        for (key, value) in self.nonlocalizableStrings.items():
            nonlocalizedStrings += "{0:{width}} = {1}\n".format(key, value, width=longestKey)

        outstr = textwrap.dedent("""\
            [Strings]
            ; localizable
            """)
        outstr += localizedStrings
        outstr += textwrap.dedent("""
            ; non-localizable
            """)
        outstr += nonlocalizedStrings
        return outstr


class InfFile(object):
    def __init__(self, name, versionStr, date, provider, mfgname, arch='amd64', diskname="Firmware Update"):
        self.infStrings = InfStrings()
        self.infSourceFiles = InfSourceFiles(diskname, self.infStrings)
        self.infHeader = InfHeader(name, versionStr, date, arch, provider, mfgname, self.infStrings)
        self.infFirmwareSections = InfFirmwareSections(arch, self.infStrings)

    def addFirmware(self, tag, desc, esrtGuid, versionInt, firmwareFile, rollback=False, integrityFile=None):
        firmwareSection = InfFirmware(tag, desc, esrtGuid, versionInt, firmwareFile,
                                      self.infStrings, self.infSourceFiles, rollback, integrityFile)
        self.infFirmwareSections.AddSection(firmwareSection)

    def __str__(self):
        return str(self.infHeader) + str(self.infFirmwareSections) + str(self.infSourceFiles) + str(self.infStrings)
