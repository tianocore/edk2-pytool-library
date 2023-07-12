##
# Python script that converts a raw DMAR table into a struct
# More details see https://software.intel.com/sites/default/files/managed/c5/15/vt-directed-io-spec.pdf
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for converting a raw DMAR table into a struct."""

import os
import struct
import sys
import xml.etree.ElementTree as ET

DMARParserVersion = '1.01'


class DMARTable(object):
    """Object representing the DMAR Table."""
    # Header Lengths
    DMARHeaderLength = 48
    DRDHHeaderLength = 16
    RMRRHeaderLength = 24
    ASTRHeaderLength = 8
    ANDDHeaderLength = 8
    DeviceScopeHeaderLength = 6

    def __init__(self, data):
        """Inits the object."""
        self.dmar_table = self.AcpiTableHeader(data)
        self.data = data[DMARTable.DMARHeaderLength:]
        while len(self.data) > 0:
            # Get type and length of remapping struct
            remapping_header = self.RemappingStructHeader(self.data)
            assert remapping_header.Type < 5, "Reserved remapping struct found in DMAR table"

            # Parse remapping struct
            if remapping_header.Type == 0:
                remapping_header = self.DRHDStruct(self.data, remapping_header.Length)
            elif remapping_header.Type == 1:
                remapping_header = self.RMRRStruct(self.data, remapping_header.Length)
                self.dmar_table.RMRRlist.append(remapping_header)
            elif remapping_header.Type == 2:
                remapping_header = self.ATSRStruct(self.data, remapping_header.Length)
            elif remapping_header.Type == 3:
                remapping_header = self.RHSAStruct(self.data, remapping_header.Length)
            elif remapping_header.Type == 4:
                remapping_header = self.ANDDStruct(self.data, remapping_header.Length)
                self.dmar_table.ANDDCount += 1
            else:
                print('Reserved remapping struct found in DMAR table')
                sys.exit(-1)

            self.dmar_table.SubStructs.append(remapping_header)
            # Add to XML
            self.data = self.data[remapping_header.Length:]

        self.xml = self.toXml()

    def toXml(self):
        """Converts the object to an xml representation."""
        root = ET.Element('DMAR Table')
        root.append(self.dmar_table.toXml())
        for sub in self.dmar_table.SubStructs:
            root.append(sub.toXml())

        return root

    def __str__(self):
        """String representation of the object."""
        retval = str(self.dmar_table)

        for sub in self.dmar_table.SubStructs:
            retval += str(sub)

        return retval

    def DMARBitEnabled(self):
        """Returns the status of the DMAR Bit."""
        return bool(self.dmar_table.DMARBit)

    def ANDDCount(self):
        """Returns the amount of ANDD in the DMAR table."""
        return self.dmar_table.ANDDCount

    def CheckRMRRCount(self, goldenxml=None):
        """Verifies all RMRR paths are in the golden XML."""
        goldenignores = set()

        if goldenxml is None or not os.path.isfile(goldenxml):
            print("XML File not found")
        else:
            goldenfile = ET.parse(goldenxml)
            goldenroot = goldenfile.getroot()
            for RMRR in goldenroot:
                goldenignores.add(RMRR.find('Path').text.lower())

        for RMRR in self.dmar_table.RMRRlist:
            if RMRR.getPath() not in goldenignores:
                print("RMRR PCIe Endpoint " + RMRR.getPath() + " found but not in golden XML")
                return False

        return True

    class AcpiTableHeader(object):
        """Object representing the ACPI Table Header."""
        STRUCT_FORMAT = '=4sIBB6s8sI4sIBB'
        size = struct.calcsize(STRUCT_FORMAT)

        def __init__(self, header_byte_array):
            """Inits the object."""
            (self.Signature,
             self.Length,
             self.Revision,
             self.Checksum,
             self.OEMID,
             self.OEMTableID,
             self.OEMRevision,
             self.CreatorID,
             self.CreatorRevision,
             self.HostAddressWidth,
             self.Flags) = struct.unpack_from(DMARTable.AcpiTableHeader.STRUCT_FORMAT, header_byte_array)

            self.DMARBit = self.Flags & 0x4
            self.ANDDCount = 0
            self.RMRRlist = list()
            self.SubStructs = list()

        def __str__(self):
            """String representation of the object."""
            return """\n  ACPI Table Header
    ------------------------------------------------------------------
      Signature          : %s
      Length             : 0x%08X
      Revision           : 0x%02X
      Checksum           : 0x%02X
      OEM ID             : %s
      OEM Table ID       : %s
      OEM Revision       : 0x%08X
      Creator ID         : %s
      Creator Revision   : 0x%08X
      Host Address Width : 0x%02X
      Flags              : 0x%02X\n""" % (self.Signature, self.Length, self.Revision, self.Checksum,
                                          self.OEMID, self.OEMTableID, self.OEMRevision, self.CreatorID,
                                          self.CreatorRevision, self.HostAddressWidth, self.Flags)

        def toXml(self):
            """Converts the object to an xml representation."""
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
            xml_repr.set('HostAddressWidth', '0x%X' % self.HostAddressWidth)
            xml_repr.set('Flags', '0x%X' % self.Flags)
            return xml_repr

    class RemappingStructHeader(object):
        """Generic remapping struct header."""
        STRUCT_FORMAT = '=HH'

        def __init__(self, header_byte_array):
            """Inits the object."""
            (self.Type,
             self.Length) = struct.unpack_from(DMARTable.RemappingStructHeader.STRUCT_FORMAT, header_byte_array)

        def __str__(self):
            """String representation of the object."""
            return """\n  Remapping Struct Header
    ------------------------------------------------------------------
      Type               : 0x%04X
      Length             : 0x%04X
    """ % (self.Type, self.Length)

    class DRHDStruct(RemappingStructHeader):
        """Object representing the DRHD struct."""
        STRUCT_FORMAT = '=HHBBHQ'  # spell-checker: disable-line

        def __init__(self, header_byte_array, length):
            """Inits the object."""
            (self.Type,
             self.Length,
             self.Flags,
             self.Reserved,
             self.SegmentNumber,
             self.RegisterBaseAddress) = struct.unpack_from(DMARTable.DRHDStruct.STRUCT_FORMAT, header_byte_array)

            # Get Sub Structs
            self.DeviceScope = list()
            header_byte_array = header_byte_array[DMARTable.DRDHHeaderLength:]
            bytes_left = self.Length - DMARTable.DRDHHeaderLength
            while bytes_left > 0:
                device_scope = DMARTable.DeviceScopeStruct(header_byte_array)
                header_byte_array = header_byte_array[device_scope.Length:]
                bytes_left -= device_scope.Length
                self.DeviceScope.append(device_scope)

        def toXml(self):
            """Converts the object to an xml representation."""
            xml_repr = ET.Element('DRHD')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Flags', '0x%X' % self.Flags)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('SegmentNumber', '0x%X' % self.SegmentNumber)
            xml_repr.set('RegisterBaseAddress', '0x%X' % self.RegisterBaseAddress)

            # Add SubStructs
            for item in self.DeviceScope:
                xml_subitem = ET.SubElement(xml_repr, item.TypeString)
                xml_subitem.set('Type', '0x%X' % item.Type)
                xml_subitem.set('Length', '0x%X' % item.Length)
                xml_subitem.set('Reserved', '0x%X' % item.Reserved)
                xml_subitem.set('EnumerationID', '0x%X' % item.EnumerationID)
                xml_subitem.set('StartBusNumber', '0x%X' % item.StartBusNumber)

            return xml_repr

        def __str__(self):
            """String representation of the object."""
            retstring = """\n  DRHD
    ------------------------------------------------------------------
      Type                  : 0x%04X
      Length                : 0x%04X
      Flags                 : 0x%02X
      Reserved              : 0x%02X
      Segment Number        : 0x%04x
      Register Base Address : 0x%016x
    """ % (self.Type, self.Length, self.Flags, self.Reserved, self.SegmentNumber, self.RegisterBaseAddress)

            for item in self.DeviceScope:
                retstring += str(item)

            return retstring

    class RMRRStruct(RemappingStructHeader):
        """Object representing the RMRR struct."""
        STRUCT_FORMAT = '=HHHHQQ'  # spell-checker: disable-line

        def __init__(self, header_byte_array, length):
            """Inits the object."""
            (self.Type,
             self.Length,
             self.Reserved,
             self.SegmentNumber,
             self.ReservedMemoryBaseAddress,
             self.ReservedMemoryRegionLimitAddress) = struct.unpack_from(DMARTable.RMRRStruct.STRUCT_FORMAT,
                                                                         header_byte_array)

            # Get Sub Structs
            self.DeviceScope = list()
            header_byte_array = header_byte_array[DMARTable.RMRRHeaderLength:]
            bytes_left = self.Length - DMARTable.RMRRHeaderLength
            while bytes_left > 0:
                device_scope = DMARTable.DeviceScopeStruct(header_byte_array)
                header_byte_array = header_byte_array[device_scope.Length:]
                bytes_left -= device_scope.Length
                self.DeviceScope.append(device_scope)

        def getPath(self):
            """Generates and returns the path."""
            retString = ""
            for index, item in enumerate(self.DeviceScope):
                retString += self.DeviceScope[index].getPath()
                if index != len(self.DeviceScope) - 1:
                    retString += ", "
            return retString

        def toXml(self):
            """Converts the object to an xml representation."""
            xml_repr = ET.Element('RMRR')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('SegmentNumber', '0x%X' % self.SegmentNumber)
            xml_repr.set('ReservedMemoryBaseAddress', '0x%X' % self.ReservedMemoryBaseAddress)
            xml_repr.set('ReservedMemoryRegionLimitAddress', '0x%X' % self.ReservedMemoryRegionLimitAddress)

            # Add SubStructs
            for item in self.DeviceScope:
                xml_subitem = ET.SubElement(xml_repr, item.TypeString)
                xml_subitem.set('Type', '0x%X' % item.Type)
                xml_subitem.set('Length', '0x%X' % item.Length)
                xml_subitem.set('Reserved', '0x%X' % item.Reserved)
                xml_subitem.set('EnumerationID', '0x%X' % item.EnumerationID)
                xml_subitem.set('StartBusNumber', '0x%X' % item.StartBusNumber)

            return xml_repr

        def __str__(self):
            """String representation of the object."""
            retstring = """\n  RMRR
    ------------------------------------------------------------------
      Type                                 : 0x%04X
      Length                               : 0x%04X
      Reserved                             : 0x%04X
      Segment Number                       : 0x%04x
      Reserved Memory Base Address         : 0x%016x
      Reserved Memory Region Limit Address : 0x%016x\n""" % (self.Type, self.Length, self.Reserved,
                                                             self.SegmentNumber, self.ReservedMemoryBaseAddress,
                                                             self.ReservedMemoryRegionLimitAddress)

            for item in self.DeviceScope:
                retstring += str(item)

            return retstring

    class ATSRStruct(RemappingStructHeader):
        """Object representing the ANDD struct."""
        STRUCT_FORMAT = '=HHBBH'  # spell-checker: disable-line

        def __init__(self, header_byte_array, length):
            """Inits the object."""
            (self.Type,
             self.Length,
             self.Flags,
             self.Reserved,
             self.SegmentNumber) = struct.unpack_from(DMARTable.ATSRStruct.STRUCT_FORMAT, header_byte_array)

            # Get Sub Structs
            self.DeviceScope = list()
            header_byte_array = header_byte_array[DMARTable.ASTRHeaderLength:]
            bytes_left = self.Length - DMARTable.ASTRHeaderLength
            while bytes_left > 0:
                device_scope = DMARTable.DeviceScopeStruct(header_byte_array)
                header_byte_array = header_byte_array[device_scope.Length:]
                bytes_left -= device_scope.Length
                self.DeviceScope.append(device_scope)

        def toXml(self):
            """Converts the object to an xml representation."""
            xml_repr = ET.Element('ASTR')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Flags', '0x%X' % self.Flags)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('SegmentNumber', '0x%X' % self.SegmentNumber)

            # Add SubStructs
            for item in self.DeviceScope:
                xml_subitem = ET.SubElement(xml_repr, item.TypeString)
                xml_subitem.set('Type', '0x%X' % item.Type)
                xml_subitem.set('Length', '0x%X' % item.Length)
                xml_subitem.set('Reserved', '0x%X' % item.Reserved)
                xml_subitem.set('EnumerationID', '0x%X' % item.EnumerationID)
                xml_subitem.set('StartBusNumber', '0x%X' % item.StartBusNumber)

            return xml_repr

        def __str__(self):
            """String representation of the object."""
            retstring = """\n  ASTR
    ------------------------------------------------------------------
      Type                                 : 0x%04X
      Length                               : 0x%04X
      Flags                                : 0x%02X
      Reserved                             : 0x%02X
      Segment Number                       : 0x%04x
    """ % (self.Type, self.Length, self.Flags, self.Reserved, self.SegmentNumber)

            for item in self.DeviceScope:
                retstring += str(item)

            return retstring

    class RHSAStruct(RemappingStructHeader):
        """Object representing the RHSA struct."""
        STRUCT_FORMAT = '=HHIQI'  # spell-checker: disable-line

        def __init__(self, header_byte_array, length):
            """Inits the object."""
            (self.Type,
             self.Length,
             self.Reserved,
             self.RegisterBaseAddress,
             self.ProximityDomain) = struct.unpack_from(DMARTable.RHSAStruct.STRUCT_FORMAT, header_byte_array)

        def toXml(self):
            """Converts the object to an xml representation."""
            xml_repr = ET.Element('RHSA')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('RegisterBaseAddress', '0x%X' % self.RegisterBaseAddress)
            xml_repr.set('ProximityDomain', '0x%X' % self.ProximityDomain)

            return xml_repr

        def __str__(self):
            """String representation of the object."""
            return """\n  RHSA
    ------------------------------------------------------------------
      Type                                 : 0x%04X
      Length                               : 0x%04X
      Reserved                             : 0x%08X
      Register Base Address                : 0x%016X
      Proximity Domain                     : 0x%08x
    """ % (self.Type, self.Length, self.Reserved, self.RegisterBaseAddress, self.ProximityDomain)

    class ANDDStruct(RemappingStructHeader):
        """Object representing the ANDD struct."""
        header_format = '=HH'

        def __init__(self, header_byte_array, length):
            """Inits the object."""
            self.STRUCT_FORMAT = '=B'
            (self.Type,
             self.Length) = struct.unpack_from(DMARTable.ANDDStruct.header_format, header_byte_array)

            # Since there is no variable of size 3 we need to manually pull into reserved
            self.Reserved = 0
            for i in range(6, 3, -1):
                self.Reserved = self.Reserved << 8
                self.Reserved |= struct.unpack("<B", header_byte_array[i:i + 1])[0]
            header_byte_array = header_byte_array[7:]

            # Unpack remaining values
            self.STRUCT_FORMAT = self.STRUCT_FORMAT + str(self.Length - DMARTable.ANDDHeaderLength) + 's'
            (self.ACPIDeviceNumber,
             self.ACPIObjectName) = struct.unpack_from(self.STRUCT_FORMAT, header_byte_array)

        def toXml(self):
            """Converts the object to an xml representation."""
            xml_repr = ET.Element('ANDD')
            xml_repr.set('Type', '0x%X' % self.Type)
            xml_repr.set('Length', '0x%X' % self.Length)
            xml_repr.set('Reserved', '0x%X' % self.Reserved)
            xml_repr.set('ACPIDeviceNumber', '0x%X' % self.ACPIDeviceNumber)
            xml_repr.set('ACPIObjectName', '%s' % self.ACPIObjectName)

            return xml_repr

        def __str__(self):
            """String representation of the object."""
            return """\n  ANDD
    ------------------------------------------------------------------
      Type                                 : 0x%04X
      Length                               : 0x%04X
      Reserved                             : 0x%06X
      ACPI Device Number                   : 0x%02X
      ACPI Object Name                     : %s
    """ % (self.Type, self.Length, self.Reserved, self.ACPIDeviceNumber, self.ACPIObjectName)

    class DeviceScopeStruct(object):
        """Object representing a Device Scope."""
        STRUCT_FORMAT = '=BBHBB'  # spell-checker: disable-line

        def __init__(self, header_byte_array):
            """Inits a DeviceScopeStruct."""
            (self.Type,
             self.Length,
             self.Reserved,
             self.EnumerationID,
             self.StartBusNumber) = struct.unpack_from(DMARTable.DeviceScopeStruct.STRUCT_FORMAT, header_byte_array)

            assert self.Type < 6, "Reserved Device Scope Type Found"

            if self.Type == 1:
                self.TypeString = "PCI Endpoint Device"
            elif self.Type == 2:
                self.TypeString = "PCI Sub-hierarchy"
            elif self.Type == 3:
                self.TypeString = "IOAPIC"
            elif self.Type == 4:
                self.TypeString = "MSI_CAPABLE_HPET"
            elif self.Type == 5:
                self.TypeString = "ACPI_NAMESPACE_DEVICE"
            else:
                print("Reserved Device Scope Type Found")
                sys.exit(-1)

            number_path_entries = (self.Length - DMARTable.DeviceScopeHeaderLength) / 2
            offset = 6
            self.Path = list()
            while number_path_entries > 0:
                self.Path.append((struct.unpack("<B", header_byte_array[offset:offset + 1]),
                                  struct.unpack("<B", header_byte_array[offset + 1:offset + 2])))
                offset += 2
                number_path_entries -= 1

        def getPath(self):
            """Returns the path."""
            retstring = "%02d" % self.StartBusNumber + ":"

            for (index, item) in enumerate(self.Path):
                retstring += "%02d" % item[0] + "." + "%01d" % item[1]
                if index != len(self.Path) - 1:
                    retstring += ":"

            return retstring

        def __str__(self):
            """String representation."""
            retstring = """\n\t\t  %s
    \t\t--------------------------------------------------
    \t\t  Type                  : 0x%02X
    \t\t  Length                : 0x%02X
    \t\t  Reserved              : 0x%04X
    \t\t  Enumeration ID        : 0x%02x
    \t\t  Start Bus Number      : 0x%02x
    \t\t  Path                  : """ % (self.TypeString, self.Type, self.Length, self.Reserved,
                                         self.EnumerationID, self.StartBusNumber)

            retstring += "%02d" % self.StartBusNumber + ":"
            for (index, item) in enumerate(self.Path):
                retstring += "%02d" % item[0] + "." + "%01d" % item[1]
                if index != len(self.Path) - 1:
                    retstring += ":"
            retstring += "\n"

            return retstring
