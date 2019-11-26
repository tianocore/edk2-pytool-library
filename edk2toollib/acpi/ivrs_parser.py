##
# Copyright (C) Microsoft Corporation. All rights reserved.
# SPDX-License-Identifier: BSD-2-Clause-Patent
#
# Python script that converts a raw IVRS table into a struct, the spec version is based on
# https://www.amd.com/system/files/TechDocs/48882_IOMMU.pdf
##

import sys
import struct
import xml.etree.ElementTree as ET
from enum import IntEnum

IVRSParserVersion = '1.00'


class IVRS_TABLE(object):

    def __init__(self, data=None):
        self.acpi_header = None
        self.SubStructs = list()
        self.IVMDlist = list()

        if data is not None:
            self.Decode(data)

    def Decode(self, data):
        self.acpi_header = IVRS_TABLE.ACPI_TABLE_HEADER(data[:IVRS_TABLE.ACPI_TABLE_HEADER.struct_format_size])

        # Start from the end of ACPI header, but store the parsed length for verification
        t_length = self.acpi_header.Length
        self.acpi_header.Length = IVRS_TABLE.ACPI_TABLE_HEADER.struct_format_size
        t_data = data[IVRS_TABLE.ACPI_TABLE_HEADER.struct_format_size:]

        # sanity check on incoming data
        Checksum8 = IVRS_TABLE.validateChecksum8(data)
        if (Checksum8 != 0):
            raise Exception('Incoming data checksum does not add up: checksum field %x, calculated is %x' %
                            (self.acpi_header.Checksum, Checksum8))

        while len(t_data) > 0:
            # Get type and length of remapping struct
            remapping_header = self.REMAPPING_STRUCT_HEADER(t_data)

            # Parse remapping struct
            if(remapping_header.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_10H) or\
              (remapping_header.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_11H) or\
              (remapping_header.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_40H):
                remapping_header = self.IVHD_STRUCT(t_data)
                self.addIVHDEntry(remapping_header)
            elif (remapping_header.Type == IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_20H) or\
                 (remapping_header.Type == IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_21H) or\
                 (remapping_header.Type == IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_22H):
                remapping_header = self.IVMD_STRUCT(t_data[:IVRS_TABLE.IVMD_STRUCT.struct_format_size])
                self.addIVMDEntry(remapping_header)
                if (remapping_header.Type == IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_20H):
                    self.IVRSBit = 0
            else:
                print('Reserved remapping struct found in IVRS table %d' % remapping_header.Type)
                sys.exit(-1)

            # Update data position
            t_data = t_data[remapping_header.Length:]

        if (self.acpi_header.Length != t_length) or (len(t_data) != 0):
            raise Exception("IVRS length does not add up. Parsed len: %d, reported len: %d" %
                            (t_length, self.acpi_header.Length))

    def Encode(self):
        bytes_str = b''

        # Append ACPI header
        bytes_str += self.acpi_header.Encode()

        # All IVHD/IVMD entries
        for ivxd in self.SubStructs:
            bytes_str += ivxd.Encode()
        return bytes_str

    def ToXmlElementTree(self):
        root = ET.Element('IVRSTable')
        root.append(self.acpi_header.ToXmlElementTree())
        for sub in self.SubStructs:
            root.append(sub.ToXmlElementTree())

        return root

    def DumpInfo(self):
        self.acpi_header.DumpInfo()

        for sub in self.SubStructs:
            sub.DumpInfo()

    @staticmethod
    def validateChecksum8(data):
        return sum(data) & 0xFF

    def updateACPISum(self):
        temp_sum = 0
        # Clear the checksum before calculating sum
        self.acpi_header.Checksum = 0
        temp_str = self.Encode()
        temp_sum = sum(temp_str)
        self.acpi_header.Checksum = (0x100 - (temp_sum & 0xFF)) & 0xFF

    def addIVHDEntry(self, ivhd):
        # append entry to the list, update length and checksum
        self.acpi_header.Length += len(ivhd.Encode())
        self.SubStructs.append(ivhd)
        self.updateACPISum()

    def addIVMDEntry(self, ivmd):
        # append entry to the list, update length and checksum
        self.acpi_header.Length += len(ivmd.Encode())
        # IVMD has to follow the corresponding IVHD, thus the list records all entries to maintain order
        self.SubStructs.append(ivmd)
        self.IVMDlist.append(ivmd)
        self.updateACPISum()

    def IVRSBitEnabled(self):
        return bool(self.acpi_header.IVRSBit)

    class ACPI_TABLE_HEADER(object):
        struct_format = '=4sIBB6s8sI4sIIQ'
        struct_format_size = struct.calcsize(struct_format)

        def __init__(self, data=None):
            self.Signature = None
            self.Length = 0
            self.Revision = 0
            self.Checksum = 0
            self.OEMID = 0
            self.OEMTableID = 0
            self.OEMRevision = 0
            self.CreatorID = 0
            self.CreatorRevision = 0
            self.IVinfo = None
            self.Reserved = 0

            self.IVRSBit = 0

            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Signature,
             self.Length,
             self.Revision,
             self.Checksum,
             self.OEMID,
             self.OEMTableID,
             self.OEMRevision,
             self.CreatorID,
             self.CreatorRevision,
             self.IVinfo,
             self.Reserved) = struct.unpack(IVRS_TABLE.ACPI_TABLE_HEADER.struct_format, header_byte_array)

            self.IVRSBit = self.IVinfo & 0x02
            if (self.IVinfo & 0x1E) == 0:
                sys.exit(-1)

        def Encode(self):
            return struct.pack(self.struct_format,
                               self.Signature,
                               self.Length,
                               self.Revision,
                               self.Checksum,
                               self.OEMID,
                               self.OEMTableID,
                               self.OEMRevision,
                               self.CreatorID,
                               self.CreatorRevision,
                               self.IVinfo,
                               self.Reserved)

        def DumpInfo(self):
            print('  ACPI Table Header')
            print('------------------------------------------------------------------')
            print('Signature          : {Signature:s}'.format(Signature=self.Signature.decode()))
            print('Length             : 0x{Length:08X}'.format(Length=self.Length))
            print('Revision           : 0x{Revision:02X}'.format(Revision=self.Revision))
            print('Checksum           : 0x{Checksum:02X}'.format(Checksum=self.Checksum))
            print('OEM ID             : {OEMID:s}'.format(OEMID=self.OEMID.decode()))
            print('OEM Table ID       : {OEMTableID:s}'.format(OEMTableID=self.OEMTableID.decode()))
            print('OEM Revision       : 0x{OEMRevision:08X}'.format(OEMRevision=self.OEMRevision))
            print('Creator ID         : {CreatorID:s}'.format(CreatorID=self.CreatorID.decode()))
            print('Creator Revision   : 0x{CreatorRevision:08X}'.format(CreatorRevision=self.CreatorRevision))
            print('IVinfo             : 0x{IVinfo:08X}'.format(IVinfo=self.IVinfo))

        def ToXmlElementTree(self):
            xml_repr = ET.Element('AcpiTableHeader')
            xml_repr.set('Signature', '%s' % self.Signature)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Revision', '0x%X' % self.Revision)
            xml_repr.set('Checksum', '0x%X' % self.Checksum)
            xml_repr.set('OEMID', '%s' % self.OEMID)
            xml_repr.set('OEMTableID', '%s' % self.OEMTableID)
            xml_repr.set('OEMRevision', '0x%X' % self.OEMRevision)
            xml_repr.set('CreatorID', '%s' % self.CreatorID)
            xml_repr.set('CreatorRevision', '0x%X' % self.CreatorRevision)
            xml_repr.set('IVinfo', '0x%X' % self.IVinfo)
            return xml_repr

    class REMAPPING_STRUCT_HEADER(object):
        struct_format = '=B'
        struct_format_size = struct.calcsize(struct_format)

        def __init__(self, header_byte_array):
            (self.Type, ) = struct.unpack(IVRS_TABLE.REMAPPING_STRUCT_HEADER.struct_format,
                                          header_byte_array[:IVRS_TABLE.REMAPPING_STRUCT_HEADER.struct_format_size])

    class IVHD_STRUCT(REMAPPING_STRUCT_HEADER):
        struct_format = '=BBHHHQHHI'
        struct_format_size = struct.calcsize(struct_format)
        ex_format = "=QQ"
        ex_format_size = struct.calcsize(ex_format)

        class IVHD_TYPE(IntEnum):
            TYPE_10H = 0x10
            TYPE_11H = 0x11
            TYPE_40H = 0x40

        def __init__(self, data=None):
            self.Type = None
            self.Flags = None
            self.Length = 0
            self.DeviceID = 0
            self.CapabilityOffset = 0
            self.IOMMUBaseAddress = 0
            self.SegmentGroup = 0
            self.IOMMUInfo = None
            self.IOMMUFeatureInfo = None
            self.IOMMUEFRImage = None
            self.Reserved = 0

            self.DeviceTableEntries = list()

            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.Flags,
             t_Length,
             self.DeviceID,
             self.CapabilityOffset,
             self.IOMMUBaseAddress,
             self.SegmentGroup,
             self.IOMMUInfo,
             self.IOMMUFeatureInfo) = struct.unpack(IVRS_TABLE.IVHD_STRUCT.struct_format,
                                                    header_byte_array[:IVRS_TABLE.IVHD_STRUCT.struct_format_size])

            self.Length = 0

            if (self.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_11H) or\
               (self.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_40H):
                ivhd_hdr_size = (IVRS_TABLE.IVHD_STRUCT.struct_format_size + IVRS_TABLE.IVHD_STRUCT.ex_format_size)
                (self.IOMMUEFRImage, self.Reserved) =\
                    struct.unpack(IVRS_TABLE.IVHD_STRUCT.ex_format,
                                  header_byte_array[IVRS_TABLE.IVHD_STRUCT.struct_format_size:ivhd_hdr_size])
            else:
                ivhd_hdr_size = IVRS_TABLE.IVHD_STRUCT.struct_format_size

            header_byte_array = header_byte_array[ivhd_hdr_size:]
            bytes_left = t_Length - ivhd_hdr_size
            self.Length += ivhd_hdr_size

            # Get Sub Structs
            while bytes_left > 0:
                device_scope = IVRS_TABLE.DEVICE_TABLE_ENTRY.Factory(header_byte_array)
                header_byte_array = header_byte_array[device_scope.Length:]
                bytes_left -= device_scope.Length
                if (device_scope.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END):
                    self.addDTEEntry(device_scope)

            if (t_Length != self.Length) or (bytes_left != 0):
                raise Exception("IVHD length does not add up. Parsed len: %d, reported len: %d" %
                                (self.Length, t_Length))

        def Encode(self):
            byte_str = b''
            byte_str += struct.pack(IVRS_TABLE.IVHD_STRUCT.struct_format,
                                    self.Type,
                                    self.Flags,
                                    self.Length,
                                    self.DeviceID,
                                    self.CapabilityOffset,
                                    self.IOMMUBaseAddress,
                                    self.SegmentGroup,
                                    self.IOMMUInfo,
                                    self.IOMMUFeatureInfo)

            if self.IOMMUEFRImage is not None:
                byte_str += struct.pack(IVRS_TABLE.IVHD_STRUCT.ex_format, self.IOMMUEFRImage, self.Reserved)

            for dte in self.DeviceTableEntries:
                byte_str += dte.Encode()

            return byte_str

        def addDTEEntry(self, dte):
            # append raw data, update length. checksum will be left untouched
            self.Length += len(dte.Encode())
            self.DeviceTableEntries.append(dte)

        def ToXmlElementTree(self):
            xml_repr = ET.Element('IVHD')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Flags', '0x%X' % self.Flags)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('IOMMUDeviceID', '0x%X' % self.DeviceID)
            xml_repr.set('CapabilityOffset', '0x%X' % self.CapabilityOffset)
            xml_repr.set('IOMMUBaseAddress', '0x%X' % self.IOMMUBaseAddress)
            xml_repr.set('SegmentGroup', '0x%X' % self.SegmentGroup)
            xml_repr.set('IOMMUInfo', '0x%X' % self.IOMMUInfo)
            xml_repr.set('IOMMUFeatureInfo', '0x%X' % self.IOMMUFeatureInfo)

            if (self.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_11H) or\
               (self.Type == IVRS_TABLE.IVHD_STRUCT.IVHD_TYPE.TYPE_40H):
                xml_repr.set('IOMMUEFRImage', '0x%X' % self.IOMMUEFRImage)

            # Add SubStructs
            for item in self.DeviceTableEntries:
                xml_repr.append(item.ToXmlElementTree())

            return xml_repr

        def DumpInfo(self):
            print("\t  IVHD")
            print("\t----------------------------------------------------------------")
            print('\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\tFlags                 : 0x{Flags:02X}'.format(Flags=self.Flags))
            print('\tLength                : 0x{Length:04X}'.format(Length=self.Length))
            print('\tIOMMU Device ID       : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\tCapability Offset     : 0x{CapabilityOffset:04X}'.format(CapabilityOffset=self.CapabilityOffset))
            print('\tIOMMU Base Address    : 0x{IOMMUBaseAddress:016X}'.format(IOMMUBaseAddress=self.IOMMUBaseAddress))
            print('\tSegment Group         : 0x{SegmentGroup:04X}'.format(SegmentGroup=self.SegmentGroup))
            print('\tIOMMU Info            : 0x{IOMMUInfo:04X}'.format(IOMMUInfo=self.IOMMUInfo))
            print('\tIOMMU Feature Info    : 0x{IOMMUFeatureInfo:08X}'.format(IOMMUFeatureInfo=self.IOMMUFeatureInfo))

            for item in self.DeviceTableEntries:
                item.DumpInfo()

    class IVMD_STRUCT(REMAPPING_STRUCT_HEADER):
        struct_format = '=BBHHHQQQ'
        struct_format_size = struct.calcsize(struct_format)

        class IVMD_TYPE(IntEnum):
            TYPE_20H = 0x20  # All peripherals
            TYPE_21H = 0x21  # Specified peripheral
            TYPE_22H = 0x22  # Peripheral range

        def __init__(self, data=None):
            self.Type = None
            self.Flags = None
            self.Length = 0
            self.DeviceID = 0
            self.AuxiliaryData = None
            self.Reserved = 0
            self.IVMDStartAddress = 0
            self.IVMDMemoryBlockLength = 0

            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.Flags,
             self.Length,
             self.DeviceID,
             self.AuxiliaryData,
             self.Reserved,
             self.IVMDStartAddress,
             self.IVMDMemoryBlockLength) = struct.unpack(IVRS_TABLE.IVMD_STRUCT.struct_format, header_byte_array)
            # IVMD is simple, the length is fixed, so assert if not
            if (self.Length != len(header_byte_array)):
                raise Exception("Bad IVMD entry size %d, expecting %d" % (self.Length, len(header_byte_array)))

        def Encode(self):
            return struct.pack(IVRS_TABLE.IVMD_STRUCT.struct_format,
                               self.Type,
                               self.Flags,
                               self.Length,
                               self.DeviceID,
                               self.AuxiliaryData,
                               self.Reserved,
                               self.IVMDStartAddress,
                               self.IVMDMemoryBlockLength)

        def ToXmlElementTree(self):
            xml_repr = ET.Element('IVMD')

            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Flags', '0x%X' % self.Flags)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('DeviceID', '0x%X' % self.DeviceID)
            if (self.Type != IVRS_TABLE.IVMD_STRUCT.IVMD_TYPE.TYPE_22H):
                xml_repr.set('AuxiliaryData', '0x%X' % self.AuxiliaryData)
            else:
                xml_repr.set('EndofRange', '0x%X' % self.AuxiliaryData)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('IVMDStartAddress', '0x%X' % self.IVMDStartAddress)
            xml_repr.set('IVMDMemoryBlockLength', '0x%X' % self.IVMDMemoryBlockLength)

            return xml_repr

        def DumpInfo(self):
            print("\t  IVMD")
            print("\t----------------------------------------------------------------")
            print('\tType                                 : 0x{Type:02X}'.format(Type=self.Type))
            print('\tFlags                                : 0x{Flags:02X}'.format(Flags=self.Flags))
            print('\tLength                               : 0x{Length:04X}'.format(Length=self.Length))
            print('\tDeviceID                             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\tAuxiliaryData                        : 0x{AuxiliaryData:04X}'.
                  format(AuxiliaryData=self.AuxiliaryData))
            print('\tReserved                             : 0x{Reserved:016X}'.format(Reserved=self.Reserved))
            print('\tIVMD Start Address                   : 0x{IVMDStartAddress:016X}'.
                  format(IVMDStartAddress=self.IVMDStartAddress))
            print('\tIVMD Memory Block Length             : 0x{IVMDMemoryBlockLength:016X}'.
                  format(IVMDMemoryBlockLength=self.Type))

    class DEVICE_TABLE_ENTRY(object):
        struct_format = '=BHB'
        struct_format_size = struct.calcsize(struct_format)
        dte_var_ext_format = "=8s8sBB"
        dte_var_len = struct_format_size + struct.calcsize(dte_var_ext_format)

        class DTE_TYPE(IntEnum):
            RESERVED = 0
            ALL = 1
            SELECT = 2
            RANGE_START = 3
            RANGE_END = 4
            ALIAS_SELECT = 66
            ALIAS_RANGE_START = 67
            EX_SELECT = 70
            EX_RANGE_START = 71
            SPECIAL = 72
            ACPI = 240

        #
        # this method is a factory
        #
        @staticmethod
        def Factory(data):
            if(data is None):
                raise Exception("Invalid File stream")

            RemapHeader = IVRS_TABLE.REMAPPING_STRUCT_HEADER(data)
            Type = RemapHeader.Type

            if(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RESERVED):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_RESERVED(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALL):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_ALL(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SELECT):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_SELECT(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_START):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_RANGE_START(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_SELECT):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_ALIAS_SELECT(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_RANGE_START):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_ALIAS_RANGE_START(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_SELECT):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_EX_SELECT(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_RANGE_START):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_EX_RANGE_START(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SPECIAL):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_SPECIAL(data)
            elif(Type == IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI):
                return IVRS_TABLE.DEVICE_TABLE_ENTRY_ACPI(data)
            else:
                return None

    class DEVICE_TABLE_ENTRY_RESERVED(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RESERVED):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RESERVED, self.Type)

            self.TypeString = "Reserved"
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            return struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            xml_item.set('Type', '0x%X' % self.Type)
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))

    class DEVICE_TABLE_ENTRY_ALL(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALL):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALL, self.Type)

            self.TypeString = "All"
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            return struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))

    class DEVICE_TABLE_ENTRY_SELECT(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SELECT):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SELECT, self.Type)

            self.TypeString = "Reserved"
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            return struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))

    class DEVICE_TABLE_ENTRY_RANGE_START(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_START):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_START, self.Type)

            self.TypeString = "Range"
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (Type,
            self.EndDeviceID,
            _) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                            header_byte_array[self.Length:
                                                (self.Length + IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size)])
            if Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END:
                print("Start of range does not follow end of range")
                sys.exit(-1)
            self.Length += IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END, self.EndDeviceID, 0)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('StartofRange', '0x%X' % self.DeviceID)
            xml_item.set('EndofRange', '0x%X' % (self.EndDeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tStart of Range        : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tEnd of Range          : 0x{EndDeviceID:04X}'.format(EndDeviceID=self.EndDeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))

    class DEVICE_TABLE_ENTRY_ALIAS_SELECT(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.SourceDeviceID = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_SELECT):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_SELECT, self.Type)

            self.TypeString = "Alias Select"
            # Two DevID, one for alias, one for source
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size +\
                IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (_, self.SourceDeviceID, _) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:self.Length])

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format, 0, self.SourceDeviceID, 0)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            xml_item.set('SourceDeviceID', '0x%X' % (self.SourceDeviceID))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))
            print('\t\tSource Device ID      : 0x{SourceDeviceID:04X}'.format(SourceDeviceID=self.SourceDeviceID))

    class DEVICE_TABLE_ENTRY_ALIAS_RANGE_START(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.SourceDeviceID = 0
            self.EndDeviceID = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_RANGE_START):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ALIAS_RANGE_START, self.Type)

            self.TypeString = "Alias Range"
            # Two DevID, one for alias start, one for source start
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size +\
                IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (_, self.SourceDeviceID, _) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:self.Length])
            (Type, self.EndDeviceID, _) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                header_byte_array[self.Length:
                                                (self.Length + IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size)])
            if Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END:
                print("Start of range does not follow end of range")
                sys.exit(-1)
            self.Length += IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format, 0, self.SourceDeviceID, 0)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format, IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END, self.EndDeviceID, 0)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('StartofRange', '0x%X' % self.DeviceID)
            xml_item.set('EndofRange', '0x%X' % (self.EndDeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            xml_item.set('SourceDeviceID', '0x%X' % (self.SourceDeviceID))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tStart of Range        : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tEnd of Range          : 0x{EndDeviceID:04X}'.format(EndDeviceID=self.EndDeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))
            print('\t\tSource Device ID      : 0x{SourceDeviceID:04X}'.format(SourceDeviceID=self.SourceDeviceID))

    class DEVICE_TABLE_ENTRY_EX_SELECT(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.ExtendedDTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_SELECT):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_SELECT, self.Type)

            self.TypeString = "Extended Select"
            # Two DTE setting, one for standard setting, one for extended setting (AtsDisabled, etc.)
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size +\
                IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (self.ExtendedDTESetting,) = \
                struct.unpack("=I", header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:self.Length])

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            # Two DTE setting, one for standard setting, one for extended setting (AtsDisabled, etc.)
            byte_str += struct.pack("=I", self.ExtendedDTESetting)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            if (self.ExtendedDTESetting & 0x80000000) != 0:
                xml_item.set('ExtendedDTESetting', 'ATS requests blocked')
            else:
                xml_item.set('ExtendedDTESetting', 'ATS allowed')
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))
            if (self.ExtendedDTESetting & 0x80000000) != 0:
                ats_str = "ATS requests blocked"
            else:
                ats_str = "ATS allowed"
            print('\t\tExtended DTE Setting  : {ExtendedDTESetting:s}'.format(ExtendedDTESetting=ats_str))

    class DEVICE_TABLE_ENTRY_EX_RANGE_START(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_RANGE_START):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.EX_RANGE_START, self.Type)

            self.TypeString = "Extended Range"
            # Two DTE setting, one for standard setting start, one for extended setting start
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size +\
                IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (self.ExtendedDTESetting,) =\
                struct.unpack("=I", header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:self.Length])
            (Type, self.EndDeviceID, _) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                header_byte_array[self.Length:
                                                (self.Length + IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size)])
            if Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.RANGE_END:
                print("Start of range does not follow end of range")
                sys.exit(-1)
            self.Length += IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            # Two DTE setting, one for standard setting start, one for extended setting start
            byte_str += struct.pack("=I", self.ExtendedDTESetting)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format, 4, self.EndDeviceID, 0)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('StartofRange', '0x%X' % self.DeviceID)
            xml_item.set('EndofRange', '0x%X' % (self.EndDeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            if (self.ExtendedDTESetting & 0x80000000) != 0:
                xml_item.set('ExtendedDTESetting', 'ATS requests blocked')
            else:
                xml_item.set('ExtendedDTESetting', 'ATS allowed')
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tStart of Range        : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tEnd of Range          : 0x{EndDeviceID:04X}'.format(EndDeviceID=self.EndDeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))
            if (self.ExtendedDTESetting & 0x80000000) != 0:
                ats_str = "ATS requests blocked"
            else:
                ats_str = "ATS allowed"
            print('\t\tExtended DTE Setting  : {ExtendedDTESetting:s}'.format(ExtendedDTESetting=ats_str))

    class DEVICE_TABLE_ENTRY_SPECIAL(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.ExtendedDTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SPECIAL):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.SPECIAL, self.Type)

            self.TypeString = "Special Device"
            # First half for standard DTE setting, second half for special DevID and its variety (APIC, HPET, etc.)
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size +\
                IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size
            (self.Handle, self.SourceDeviceID, self.Variety) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:self.Length])

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            # First half for standard DTE setting, second half for special DevID and its variety (APIC, HPET, etc.)
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                    self.Handle,
                                    self.SourceDeviceID,
                                    self.Variety)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))
            xml_item.set('SourceDeviceID', '0x%X' % (self.SourceDeviceID))

            xml_item.set('Handle', '0x%X' % (self.Handle))
            if self.Variety == 1:
                xml_item.set('Variety', 'IOAPIC')
            elif self.Variety == 2:
                xml_item.set('Variety', 'HPET')
            else:
                xml_item.set('Variety', 'Reserved %X' % (self.Variety))
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))
            print('\t\tSource Device ID      : 0x{SourceDeviceID:04X}'.format(SourceDeviceID=self.SourceDeviceID))

            if self.Variety == 1:
                var_str = "IOAPIC"
            elif self.Variety == 2:
                var_str = "HPET"
            else:
                var_str = "Reserved 0x%02X" % (self.Variety)
            print('\t\tHandle                : 0x{Handle:02X}'.format(Handle=self.Handle))
            print('\t\tVariety               : {Variety:s}'.format(Variety=var_str))

    class DEVICE_TABLE_ENTRY_ACPI(object):
        def __init__(self, data=None):
            self.Type = 0
            self.DeviceID = 0
            self.DTESetting = 0
            self.ExtendedDTESetting = 0
            self.TypeString = None
            self.Length = 0
            if data is not None:
                self.Decode(data)

        def Decode(self, header_byte_array):
            (self.Type,
             self.DeviceID,
             self.DTESetting) = struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                                              header_byte_array[:IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size])
            if (self.Type != IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI):
                raise Exception ("Input device type (%d) does not match expectation (%d)", IVRS_TABLE.DEVICE_TABLE_ENTRY.DTE_TYPE.ACPI, self.Type)

            self.TypeString = "Variable Length ACPI HID Device"
            (self.HID, self.CID, self.UIDFormat, self.UIDLength) =\
                struct.unpack(IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_ext_format,
                                header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format_size:
                                                IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_len])
            self.Length = IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_len + self.UIDLength
            if self.UIDFormat == 0:
                self.UID = None
            elif self.UIDFormat == 1:
                (self.UID,) = struct.unpack("=Q", header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_len:
                                            self.Length])
            elif self.UIDFormat == 2:
                (self.UID,) =\
                    struct.unpack("=%ss" % self.UIDLength,
                                    header_byte_array[IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_len:self.Length])

        def Encode(self):
            byte_str = struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.struct_format,
                               self.Type,
                               self.DeviceID,
                               self.DTESetting)
            # Variable Length ACPI HID Device
            byte_str += struct.pack(IVRS_TABLE.DEVICE_TABLE_ENTRY.dte_var_ext_format,
                                    self.HID,
                                    self.CID,
                                    self.UIDFormat,
                                    self.UIDLength)
            if self.UIDFormat == 1:
                byte_str += struct.pack("=Q", self.UID)
            elif self.UIDFormat == 2:
                byte_str += struct.pack("=%ss" % self.UIDLength, self.UID)
            return byte_str

        def ToXmlElementTree(self):
            xml_item = ET.Element(self.TypeString.replace(" ", ""))
            xml_item.set('Type', '0x%X' % self.Type)
            xml_item.set('DeviceID', '0x%X' % (self.DeviceID))
            xml_item.set('DTESetting', '0x%X' % (self.DTESetting))

            xml_item.set('HardwareID', '%s' % (self.HID))
            xml_item.set('ExtendedDTE Setting', '%s' % (self.CID))
            xml_item.set('UniqueIDFormat', '%d' % (self.UIDFormat))
            xml_item.set('UniqueIDLength', '%d' % (self.UIDLength))
            if self.UIDFormat == 0:
                xml_item.set('UniqueID', 'None')
            elif self.UIDFormat == 1:
                xml_item.set('UniqueID', '0x%X' % (self.UID))
            elif self.UIDFormat == 2:
                xml_item.set('UniqueID', '%s' % (self.UID))
            else:
                print("Unrecognized UID format detected")
                sys.exit(-1)
            return xml_item

        def DumpInfo(self):
            print('\t\t  {TypeString:s}'.format(TypeString=self.TypeString))
            print('\t\t--------------------------------------------------')
            print('\t\tType                  : 0x{Type:02X}'.format(Type=self.Type))
            print('\t\tDevice ID             : 0x{DeviceID:04X}'.format(DeviceID=self.DeviceID))
            print('\t\tDTE Setting           : 0x{DTESetting:02X}'.format(DTESetting=self.DTESetting))

            print('\t\tHardware ID           : {HID:s}'.format(HID=self.HID.decode()))
            print('\t\tExtended DTE Setting  : {CID:s}'.format(CID=self.CID.decode()))
            print('\t\tUnique ID Format      : {UIDFormat:d}'.format(UIDFormat=self.UIDFormat))
            print('\t\tUnique ID Length      : {UIDLength:d}'.format(UIDLength=self.UIDLength))
            if self.UIDFormat == 0:
                print('\t\tUnique ID             : None')
            elif self.UIDFormat == 1:
                print('\t\tUnique ID             : 0x{UID:X}'.format(UID=self.UID))
            elif self.UIDFormat == 2:
                print('\t\tUnique ID             : {UID:s}'.format(UID=self.UID.decode()))
            else:
                raise Exception("Unrecognized UID format detected %d" % self.UIDFormat)
