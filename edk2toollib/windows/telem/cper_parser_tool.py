# @file cper_parser.py
# TODO: Write Readme and short description
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct
import uuid
import logging
import edk2toollib.windows.telem.decoders
from edk2toollib.windows.telem.cper_section_data import SECTION_DATA_PARSER

# TODO: Remove once done with development

"""
CPER: Common Platform Error Record

Structure of a CPER Header:
Signature           (0   byte offset, 4  byte length) : CPER Signature
Revision            (4   byte offset, 2  byte length) : The Revision of CPER
Signature End       (6   byte offset, 4  byte length) : Must always be 0xffffffff
Section Count       (10  byte offset, 2  byte length) : The Number of Sections of CPER
Error Severity      (12  byte offset, 4  byte length) : The Severity of Error of CPER
Validation Bits     (16  byte offset, 4  byte length) : Identify Valid Ids of the CPER
Record Length       (20  byte offset, 4  byte length) : The size(in bytes) of the ENTIRE Error Record
Timestamp           (24  byte offset, 8  byte length) : The Time at which the Error occured
Platform Id         (32  byte offset, 16 byte length) : The Platform GUID (Typically, the Platform SMBIOS UUID)
Partition Id        (48  byte offset, 16 byte length) : The Software Partition (if applicable)
Creator Id          (64  byte offset, 16 byte length) : The GUID of the Error "Creator"
Notification Type   (80  byte offset, 16 byte length) : A pre-assigned GUID associated with the event (ex.Boot)
Record Id           (96  byte offset, 8  byte length) : When combined with the Creator Id, identifies the Error Record
Flags               (104 byte offset, 4  byte length) : A specific "flag" for the Error Record. Flags are pre-defined
                                                        values which provide more information on the Error
Persistence Info    (108 byte offset, 8  byte length) : Produced and consumed by the creator of the Error
                                                        Record.There are no guidelines for these bytes.
Reserved            (116 byte offset, 12 byte length) : Must be zero


A Section Header within a CPER has the following structure

Section Offset      (0  byte offset, 4  byte length) : Offset from start of the CPER(not the start of
                                                       the section) to the beginning of the section body
Section Length      (4  byte offset, 4  byte length) : Length in bytes of the section body
Revision            (8  byte offset, 2  byte length) : Represents the major and minor version
                                                       number of the Error Record definition
Validation Bits     (10 byte offset, 1  byte length) : Indicates the validity of the Fru Id and Fru String fields
Reserved            (11 byte offset, 1  byte length) : Must be zero
Flags               (12 byte offset, 4  byte length) : Contains info describing the Error Record (ex. Is this the
                                                       primary section of the error, has the component been reset
                                                       if applicable, has the error been contained)
Section Type        (16 byte offset, 16 byte length) : Holds a pre-defined GUID value indicating that this
                                                       section is from a particular error
Fru Id              (32 byte offset, 16 byte length) : ? Not detailed in the CPER doc
Section Severity    (48 byte offset, 4  byte length) : Value from 0 - 3 indicating the severity of the error
Fru String          (52 byte offset, 20 byte length) : String identifying the Fru hardware

Python Struct Format Characters

Format      C Type                  Python Type     Standard Size
x           pad byte                none            1
c           char                    integer         1
b           signed char             integer         1
B           unsigned char           integer         1
?           _Bool                   bool            1
h           short                   integer         2
H           unsigned short          integer         2
i           int                     integer         4
I           unsigned int            integer         4
l           long                    integer         4
L           unsigned long           integer         4
q           long long               integer         8
Q           unsigned long long      integer         8
n           ssize_t                 integer
N           size_t                  integer
e           (6)                     float           2
f           float                   float           4
d           double                  float           8
s           char[]                  bytes
p           char[]                  bytes
P           void *                  integer
"""

CPER_HEADER_SIZE = 128          # CPER spec defines header as 128 bytes
CPER_SECTION_HEADER_SIZE = 72   # CPER spec defines section header as 72 bytes

predefined_guids = {"2dce8bb1-bdd7-450e-b9ad-9cf4ebd4f890": "CMC Notify Type",
                    "4e292f96-d843-4a55-a8c2-d481f27ebeee": "CPE Notify Type",
                    "e8f56ffe-919c-4cc5-ba88-65abe14913bb": "MCE Notify Type",
                    "cf93c01f-1a16-4dfc-b8bc-9c4daf67c104": "PCIe Notify Type",
                    "cc5263e8-9308-454a-89d0-340bd39bc98e": "INIT Notify Type",
                    "5bad89ff-b7e6-42c9-814a-cf2485d6e98a": "NMI Notify Type",
                    "3d61a466-ab40-409a-a698-f362d464b38f": "Boot Notify Type",
                    "9a78788a-bbe8-11e4-809e-67611e5d46b0": "SEA Notify Type",
                    "5c284c81-b0ae-4e87-a322-b04c85624323": "SEI Notify Type",
                    "09a9d5ac-5204-4214-96e5-94992e752bcd": "PEI Notify Type",
                    "487565ba-6494-4367-95ca-4eff893522f6": "BMC Notify Type",
                    "e9d59197-94ee-4a4f-8ad8-9b7d8bd93d2e": "SCI Notify Type",
                    "fe84086e-b557-43cf-ac1b-17982e078470": "EXTINT Notify Type",
                    "0033f803-2e70-4e88-992c-6f26daf3db7a": "Device Driver Notify Type",
                    "919448b2-3739-4b7f-a8f1-e0062805c2a3": "CMCI Notify Type",
                    "9876ccad-47b4-4bdb-b65e-16f193c4f3db": "Processor Generic Error Section",
                    "00000000-0000-0000-0000-000000000000": "Device Driver Error Section",
                    "1c15b445-9b06-4667-ac25-33c056b88803": "IPMI MSR Dump Section",
                    "dc3ea0b0-a144-4797-b95b-53fa242b6e1d": "XPF Processor Error",
                    "e429faf1-3cb7-11d4-bca7-0080c73c8881": "IPF Processor Error",
                    "e19e3d16-bc11-11e4-9caa-c2051d5d46b0": "ARM Processor Error",
                    "a5bc1114-6f64-4ede-b863-3e83ed7c83b1": "Memory Error Section",
                    "d995e954-bbc1-430f-ad91-b44dcb3c6f35": "PCIe Error Section",
                    "c5753963-3b84-4095-bf78-eddad3f9c9dd": "PCIX Bus Error Section",
                    "eb5e4685-ca66-4769-b6a2-26068b001326": "PCIX Device Error Section",
                    "81212a96-09ed-4996-9471-8d729c8e69ed": "Firmware Error Record Reference",
                    "81687003-dbfd-4728-9ffd-f0904f97597d": "PMEM Error Section",
                    "a55701f5-e3ef-43de-ac72-249b573fad2c": "WHEA Cache Check",
                    "fc06b535-5e1f-4562-9f25-0a3b9adb63c3": "WHEA TLB Check",
                    "1cf3f8b3-c5b1-49a2-aa59-5eef92ffa63c": "WHEA Bus Check",
                    "48ab7f57-dc34-4f6c-a7d3-b0b5b0a74314": "WHEA MS Check",
                    "cf07c4bd-b789-4e18-b3c4-1f732cb57131": "WHEA Record Creator",
                    "3e62a467-ab40-409a-a698-f362d464b38f": "Generic Notfiy Type",
                    "6f3380d1-6eb0-497f-a578-4d4c65a71617": "IPF SAL Record Section",
                    "8a1e1d01-42f9-4557-9c33-565e5cc3f7e8": "XPF MCA Section",
                    "e71254e7-c1b9-4940-ab76-909703a4320f": "NMI Section",
                    "e71254e8-c1b9-4940-ab76-909703a4320f": "Generic Section",
                    "e71254e9-c1b9-4940-ab76-909703a4320f": "WHEA Error Packet Section",
                    }

# List of plugin classes which inherit from CPER_SECTION_DATA and are
# therefore capable of parsing section data
Parsers = SECTION_DATA_PARSER.__subclasses__()


class GENERIC_FIELD(object):
    '''A super class for fields of CPER records'''
    def __init__(self, raw_value):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse()

    def Parse(self):
        '''Parse this field'''
        self.parsed_value = str(self.raw_value)
        self.valid = True

    def Valid(self):
        ''''Returns true if this field is valid'''
        return self.valid

    def GetString(self, parsed=True):
        '''
        Returns a string version of this field. If parsed is true, it will return a parsed
        version of the field if available
        '''
        if(parsed):
            return str(self.parsed_value)

        return str(self.raw_value)

    def GetRawValue(self):
        '''Returns the raw input value of this field'''
        return self.raw_value


class SIGNATURE_FIELD(GENERIC_FIELD):
    '''Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"'''

    def __init__(self, raw_value):
        super().__init__(raw_value)

    def Parse(self):
        # TODO: Finish
        # self.parsed_value = self.raw_value.decode('ascii')

        # if(self.parsed_value == "CPER"):
        #     self.valid = True
        self.valid = True


class REVISION_FIELD(GENERIC_FIELD):
    '''
        This is a 2-byte field representing a major and minor version number for the error record
        definition in BCD format.

        TODO: Actually parse out the zeroth and first byte which represent the minor and
        major version numbers respectively
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class SECTION_COUNT_FIELD(GENERIC_FIELD):
    '''
    This field indicates the number of valid sections associated with the record,
    corresponding to each of the following section descriptors.
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class SEVERITY_FIELD(GENERIC_FIELD):
    '''
        Indicates the severity of the error condition. The severity of the error record
        corresponds to the most severe error section.

        NOTE: A severity of "Informational" indicates that the section contains extra information
        that can be safely ignored
        '''

    def __init__(self, raw_value):
        super().__init__(raw_value)

    def Parse(self):
        '''Parse the error severity for 4 known values'''

        if(self.raw_value == 0):
            self.parsed_value = "Recoverable"
        elif(self.raw_value == 1):
            self.parsed_value = "Fatal"
        elif(self.raw_value == 2):
            self.parsed_value = "Corrected"
        elif(self.raw_value == 3):
            self.parsed_value = "Informational"
        else:
            self.parsed_value = "Unknown"


class CPER_HEADER_VALIDATION_BITS_FIELD(GENERIC_FIELD):
    '''
        This field indicates the validity of the following fields:

        if bit 1: PlatformId contains valid info\n
        if bit 2: Timestamp contains valid info\n
        if bit 3: PartitionId contains valid info
        '''
    def __init__(self, raw_value):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = True
        self.platform_id_valid = False
        self.timestamp_valid = False
        self.partition_id_valid = False
        self.Parse()

    def Parse(self):
        print("PARSING CPER HEADER VALID BITS")
        self.parsed_value = "Platform ID Valid?: "
        if(self.raw_value & int('0b1', 2)):   # Check bit 0
            print("PLAT ID TRUE")
            self.platform_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

        self.parsed_value = "Timestamp Valid?: "

        if(self.raw_value & int('0b10', 2)):  # Check bit 1
            print("TIMESTAMP TRUE")
            self.timestamp_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

        self.parsed_value = "Partition ID Valid?: "

        if(self.raw_value & int('0b100', 2)):  # Check bit 2
            print("PART ID TRUE")
            self.partition_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

    def PlatformIdValid(self):
        return self.platform_id_valid

    def TimestampValid(self):
        return self.timestamp_valid

    def PartitionIdValid(self):
        return self.partition_id_valid


class RECORD_LENGTH_FIELD(GENERIC_FIELD):
    '''
    Indicates the size of the actual error record, including the size of the record header,
    all section descriptors, and section bodies. The size may include extra buffer space to allow
    for the dynamic addition of error sections descriptors and bodies.
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class TIMESTAMP_FIELD(GENERIC_FIELD):
    '''
    The timestamp correlates to the time when the error information was collected by the system
    software and may not necessarily represent the time of the error event. The timestamp contains
    the local time in BCD format.
    '''

    def __init__(self, raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self, valid_bits_field):
        '''Convert the timestamp into a friendly version formatted to (M/D/YYYY Hours:Minutes:Seconds)'''
        if(valid_bits_field.TimestampValid()):
            self.parsed_value = str((self.raw_value >> 40) & int('0b11111111', 2)) + "/" + \
                str((self.raw_value >> 32) & int('0b11111111', 2)) + "/" + \
                str((((self.raw_value >> 56) & int('0b11111111', 2)) * 100)
                    + ((self.raw_value >> 48) & int('0b11111111', 2))) + " " + \
                format(str((self.raw_value >> 16) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.raw_value >> 8) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.raw_value >> 0) & int('0b11111111', 2)), "0>2")
        else:
            self.parsed_value = "Invalid"
        self.valid = True


class PLATFORM_ID_FIELD(GENERIC_FIELD):
    '''
    This field uniquely identifies the platform with a GUID. The platform’s SMBIOS UUID should
    be used to populate this field. Error analysis software may use this value to uniquely identify
    a platform.
    '''

    def __init__(self, raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self, valid_bits_field):
        if(valid_bits_field.PlatformIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)
        else:
            self.parsed_value = "Invalid"
        self.valid = True


class PARTITION_ID_FIELD(GENERIC_FIELD):
    '''
    If the platform has multiple software partitions, system software may associate a GUID
    with the partition on which the error occurred.
    '''

    def __init__(self, raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self, valid_bits_field):
        if(valid_bits_field.PartitionIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)
        else:
            self.parsed_value = "Invalid"
        self.valid = True


class CREATOR_ID_FIELD(GENERIC_FIELD):
    '''This field contains a GUID indicating the creator of the error record. This value may be
    overwritten by subsequent owners of the record.'''
    def __init__(self, raw_value):
        super().__init__(raw_value)

    def Parse(self):
        self.parsed_value = AttemptGuidParse(self.raw_value)
        self.valid = True


class NOTIFICATION_TYPE_FIELD(GENERIC_FIELD):
    '''This field holds a pre-assigned GUID value indicating the record association with an error
    event notification type.'''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class RECORD_ID_FIELD(GENERIC_FIELD):
    '''
    This value, when combined with the Creator ID, uniquely identifies the error record
    across other error records on a given system.
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class CPER_HEADER_FLAGS_FIELD(GENERIC_FIELD):
    '''
    Check the flags field and populate list containing applicable flags

    if bit 0: An error condition that has been recovered by system software\n
    if bit 1: An error condition that occurred during a previous session\n
    if bit 2: An error condition that was intentionally caused\n
    if bit 3: An error condition caused by a device driver\n
    if bit 4: An error condition critical to system operation\n
    if bit 5: An error condition which should persist between boots
    '''

    def __init__(self, raw_value):
        self.flags_list = []
        super().__init__(raw_value)

    def Parse(self):

        # Check each bit for associated flag
        if(self.raw_value & int('0b1', 2)):
            self.flags_list.append("Recovered")
        if(self.raw_value & int('0b10', 2)):
            self.flags_list.append("Previous Error")
        if(self.raw_value & int('0b100', 2)):
            self.flags_list.append("Simulated")
        if(self.raw_value & int('0b1000', 2)):
            self.flags_list.append("Device Driver")
        if(self.raw_value & int('0b10000', 2)):
            self.flags_list.append("Critical")
        if(self.raw_value & int('0b100000', 2)):
            self.flags_list.append("Persist")

        # If no flags were found
        if(self.flags_list == []):
            self.parsed_value = "None"

        # Join the FlagsList elements separated by commas
        self.parsed_value = ", ".join(self.flags_list)

        self.valid = True

    def GetFlagsList(self):
        return self.flags_list


class SECTION_HEADER_FLAGS_FIELD(GENERIC_FIELD):
    '''
    Check the flags field and populate list containing applicable flags

    if bit 0: This is the section to be associated with the error condition\n
    if bit 1: The error was not contained within the processor or memery heirarchy\n
    if bit 2: The component has been reset and must be reinitialized\n
    if bit 3: Error threshold exceeded for this component\n
    if bit 4: Resource could not be queried for additional information\n
    if bit 5: Action has been taken to contain the error, but the error has not been corrected
    '''

    def __init__(self, raw_value):
        self.flags_list = []
        super().__init__(raw_value)

    def Parse(self):

        if(self.raw_value & int('0b1', 2)):  # Check bit 0
            self.flags_list.append("Primary")
        if(self.raw_value & int('0b10', 2)):  # Check bit 1
            self.flags_list.append("Containment Warning")
        if(self.raw_value & int('0b100', 2)):  # Check bit 2
            self.flags_list.append("Reset")
        if(self.raw_value & int('0b1000', 2)):  # Check bit 3
            self.flags_list.append("Error Threshold Exceeded")
        if(self.raw_value & int('0b10000', 2)):  # Check bit 4
            self.flags_list.append("Resource Not Accessible")
        if(self.raw_value & int('0b100000', 2)):  # Check bit 5
            self.flags_list.append("Latent Error")

        # If no flags were found
        if(self.flags_list == []):
            self.parsed_value = "None"

        # Join the FlagsList elements separated by commas
        self.parsed_value = ", ".join(self.flags_list)

        self.valid = True

    def GetFlagsList(self):
        return self.flags_list


class PERSISTENCE_INFO_FIELD(GENERIC_FIELD):
    '''
    This field is produced and consumed by the creator of the error record identified in the
    Creator ID field. The format of this field is defined by the creator.
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class SECTION_LENGTH_FIELD(GENERIC_FIELD):
    '''The length in bytes of the section body.'''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class SECTION_OFFSET_FIELD(GENERIC_FIELD):
    '''Offset in bytes of the section body from the base of the record header.'''

    def __init__(self, raw_value):
        super().__init__(raw_value)


class SECTION_HEADER_VALIDATION_BITS_FIELD(GENERIC_FIELD):
    '''
    if bit 0: FruId contains valid info\n
    if bit 1: FruId String contains valid info
    '''
    def __init__(self, raw_value):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = True
        self.fru_id_valid = False
        self.fru_string_valid = False
        self.Parse()

    def Parse(self):

        self.parsed_value = "Fru ID Valid?: "
        if(self.raw_value & int('0b1', 2)):   # Check bit 0
            self.fru_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

        self.parsed_value = "Fru String Valid?: "
        if(self.raw_value & int('0b10', 2)):  # Check bit 1
            self.fru_string_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

    def FruIdValid(self):
        return self.fru_id_valid

    def FruStringValid(self):
        return self.fru_string_valid


class SECTION_TYPE_FIELD(GENERIC_FIELD):
    '''
    This field holds a pre-assigned GUID value indicating that it is a section of a
    particular error.
    '''

    def __init__(self, raw_value):
        super().__init__(raw_value)

    def Parse(self, valid_bits_field):
        if(valid_bits_field.PartitionIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)

        self.parsed_value = "Invalid"
        self.valid = True


class FRU_ID_FIELD(GENERIC_FIELD):
    '''
    GUID representing the FRU ID, if it exists, for the section reporting the error.
    The default value is zero indicating an invalid FRU ID. System software can use this
    to uniquely identify a physical device for tracking purposes.
    '''

    def __init__(self, raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self, valid_bits_field):
        if(valid_bits_field.FruIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)
        else:
            self.parsed_value = "Invalid"
        self.valid = True


class FRU_STRING_FIELD(GENERIC_FIELD):
    '''Custom ASCII string identifying the FRU hardware.'''

    def __init__(self, raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self, valid_bits_field):
        if(valid_bits_field.FruStringValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)
        else:
            self.parsed_value = "Invalid"
        self.valid = True


class CPER(object):
    '''
    A CPER (Common Platform Error Record) consists of a header; followed by one or more
    section descriptors; and for each descriptor, an associated section which may contain
    either error or informational data.
    '''

    def __init__(self, input: str):
        self.rawData = bytearray.fromhex(input)

        self.header = CPER_HEADER(self.rawData[:CPER_HEADER_SIZE])
        # self.SetCperHeader()
        self.sectionHeaders = []
        self.SetSectionHeaders()

    def SetCperHeader(self) -> None:
        '''Turn the portion of the raw input associated with the CPER head into a CPER_HEAD object'''

        temp = self.rawData[:CPER_HEADER_SIZE]
        try:
            self.header = CPER_HEADER(temp)
        except:
            print("Unable to parse record")

    def SetSectionHeaders(self) -> None:
        '''Set each of the section headers to CPER_SECTION_HEADER objects'''

        # Section of rawData containing the section headers
        temp = self.rawData[CPER_HEADER_SIZE:CPER_HEADER_SIZE + (CPER_SECTION_HEADER_SIZE * self.GetSectionCount())]

        # Go through each section header and attempt to create a
        # CPER_SECTION_HEADER object. Store each header in SectionHeaders list
        for x in range(self.GetSectionCount()):
            try:  # Don't want to stop runtime if parsing fails
                self.sectionHeaders.append(CPER_SECTION_HEADER(
                    temp[x * CPER_SECTION_HEADER_SIZE: (x + 1) * CPER_SECTION_HEADER_SIZE]))
            except:  # TODO: Add specific exception instructions
                # print("Error parsing section header %d" % x)
                pass

    def ParseSectionData(self, s: object) -> None:
        '''Get each of the actual section data pieces and either pass it to
        something which can parse it, or dump the hex'''

        # TODO: Should we only apply one plugin if multiple claim they can parse the data?

        # Runs CanParse() on each plugin in .\decoders\ folder to see if it can parse the section type
        p = CheckDecodersForGuid(s.sectionType)

        # if we've found a plugin which can parse this section
        if p is not None:
            try:
                # pass the data to that parser which should return a string of the data parsed/formatted
                return p.Parse(self.rawData[s.sectionOffset: s.sectionOffset + s.sectionLength])
            except:  # TODO: Add specific exception instructions
                logging.debug("Unable to apply plugin " + str(p) + " on section data!")

        # If no plugin can parse the section data, do a simple hex dump
        return HexDump(self.rawData[s.sectionOffset: s.sectionOffset + s.sectionLength], 16)

    def PrettyPrint(self) -> None:
        '''Print the entire CPER record'''

        counter = 1

        print(self.header.PrettyPrint())

        # Alert user that section count doesn't match sections being printed.
        # This could be because there was an error parsing a section, or the
        # section count is incorrect
        if self.GetSectionCount() != len(self.sectionHeaders):
            print("Section Count of CPER header is incorrect!\n")

        # Print each section header followed by the correlated section
        for s in self.sectionHeaders:
            print("Section " + str(counter))
            print(s.PrettyPrint())
            print(self.ParseSectionData(s))
            counter += 1

    def GetSectionCount(self) -> int:
        "Returns the number of sections in this record"
        return self.header.section_count.GetRawValue()

    def GetErrorSeverity(self) -> str:
        "Returns the severity of this record"
        return self.header.error_severity.GetString()

    def GetRecordLength(self) -> int:
        "Returns the length in bytes of this record"
        return self.header.record_length.GetRawValue()

    def GetTimestamp(self) -> str:
        "Returns the time at which this error occured"
        return self.header.timestamp.GetString()

    def GetPlatformId(self) -> str:
        "Returns the guid of the platform"
        return self.header.platform_id.GetString()

    def GetPartitionId(self) -> str:
        "Returns the guid of the software partition"
        return self.header.partition_id.GetString()

    def GetCreatorId(self) -> str:
        "Returns the guid of error creator"
        return self.header.creator_id.GetString()

    def GetRecordId(self) -> str:
        "Returns an 8 byte value which, when used with the creator id, identifies the record"
        return self.header.record_id.GetString()

    def GetFlags(self) -> list:
        "Returns a list of all flags set in the record"
        return self.header.flags.GetFlagsList()

    def GetSectionsLength(self) -> list:
        "Returns the length of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.section_length)
        return temp

    def GetSectionsOffset(self) -> list:
        "Returns the byte offset of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.section_offset)
        return temp

    def GetSectionsFlags(self) -> list:
        "Returns the flags set in each error section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.flags.GetString())
        return temp

    def GetSectionsType(self) -> list:
        "Returns the type of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.section_type.GetString())
        return temp

    def GetSectionsFruId(self) -> list:
        "Returns the fru id of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.fru_id.GetString())
        return temp

    def GetSectionsSeverity(self) -> list:
        "Returns the severity of each section error as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.section_severity.GetString())
        return temp

    def GetSectionsFruString(self) -> list:
        "Returns the fru string of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.fru_string.GetString())
        return temp


class CPER_HEADER(object):
    '''
    The CPER header includes information which uniquely identifies a hardware error record
    on a given system.
    '''

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, input: str):

        try:
            (self.signature_start,
                self.revision,
                self.signature_end,
                self.section_count,
                self.error_severity,
                self.validation_bits,
                self.record_length,
                self.timestamp,
                self.platform_id,
                self.partition_id,
                self.creator_id,
                self.notification_type,
                self.record_id,
                self.flags,
                self.persistence_info,
                self.reserved) = struct.unpack_from(self.STRUCT_FORMAT, input)
        except:
            return None

        self.signature_start = SIGNATURE_FIELD(self.signature_start)
        self.revision = REVISION_FIELD(self.revision)
        self.section_count = SECTION_COUNT_FIELD(self.section_count)
        self.error_severity = SEVERITY_FIELD(self.error_severity)
        self.validation_bits = CPER_HEADER_VALIDATION_BITS_FIELD(self.validation_bits)
        self.record_length = RECORD_LENGTH_FIELD(self.record_length)
        self.timestamp = TIMESTAMP_FIELD(self.timestamp, self.validation_bits)
        self.platform_id = PLATFORM_ID_FIELD(self.platform_id, self.validation_bits)
        self.partition_id = PARTITION_ID_FIELD(self.partition_id, self.validation_bits)
        self.creator_id = CREATOR_ID_FIELD(self.creator_id)
        self.notification_type = NOTIFICATION_TYPE_FIELD(self.notification_type)
        self.record_id = RECORD_ID_FIELD(self.record_id)
        self.flags = CPER_HEADER_FLAGS_FIELD(self.flags)
        self.persistence_info = PERSISTENCE_INFO_FIELD(self.persistence_info)

    def PrettyPrint(self) -> str:
        '''Print relevant portions of the CPER header. Change to suit your needs'''

        string = ""
        temp = ""

        string += "Record Length:  " + self.record_length.GetString() + '\n'

        temp = self.timestamp.GetString()
        string += "Time of error:  " + temp + '\n'

        temp = self.error_severity.GetString()
        string += "Error severity: " + temp + '\n'

        temp = self.flags.GetString()
        string += "Flags:       " + temp + '\n'

        temp = self.platform_id.GetString()
        string += "Platform Id:    " + temp + '\n'

        temp = self.partition_id.GetString()
        string += "Partition Id:   " + temp + '\n'

        temp = self.creator_id.GetString()
        string += "Creator Id:     " + temp + '\n'

        return string[0:-1]  # omit the last newline


class CPER_SECTION_HEADER(object):
    '''Describes the content of a CPER section'''

    STRUCT_FORMAT = "=IIHccI16s16sI20s"

    def __init__(self, input: str):

        (self.section_offset,
            self.section_length,
            self.revision,
            self.validation_bits,
            self.reserved,
            self.flags,
            self.section_type,
            self.fru_id,
            self.section_severity,
            self.fru_string) = struct.unpack_from(self.STRUCT_FORMAT, input)

        self.section_offset = SECTION_OFFSET_FIELD(self.section_offset)
        self.section_length = SECTION_LENGTH_FIELD(self.section_length)
        self.revision = REVISION_FIELD(self.revision)
        self.validation_bits = SECTION_HEADER_VALIDATION_BITS_FIELD(self.validation_bits)
        self.flags = SECTION_HEADER_FLAGS_FIELD(self.flags)
        self.section_type = SECTION_TYPE_FIELD(self.section_type)
        self.fru_id = FRU_ID_FIELD(self.fru_id, self.validation_bits)
        self.section_severity = SEVERITY_FIELD(self.section_severity)
        self.fru_string = FRU_STRING_FIELD(self.fru_string, self.validation_bits)

    def PrettyPrint(self) -> str:
        '''Print relevant portions of the section header. Change to suit your needs'''

        string = ""
        temp = ""

        string += "Section Length:      " + self.section_length.GetString() + '\n'

        temp = self.flags.GetString()
        string += "Flags:               " + temp + '\n'

        temp = self.section_severity.GetString()
        string += "Section Severity:    " + temp + '\n'

        temp = self.section_type.GetString()
        string += "Section Type:        " + temp + '\n'

        temp = self.fru_id.GetString()
        string += "Fru Id:              " + temp + '\n'

        temp = self.fru_string.GetString()
        string += "Fru String:          " + temp + '\n'

        return string


def HexDump(input: bytes, bytesperline: int) -> str:
    '''Dumps byte code of input'''

    string = ""  # Stores the entire hexdump string
    asc = ""  # Stores the ascii version of the current hexdump line
    byte = ""  # Stores the base 16 byte version of the current hexdump line

    # Used to check if a byte value is within relevant ascii character bounds
    def rangecheck(x):
        return x < 31 or x > 127

    # Go through every byte from the input
    for i in range(len(input)):

        # Add a byte string version of the byte onto the byte string
        byte += format(input[i], '02X') + " "

        # Add an ascii version of the byte onto the ascii string
        if rangecheck(input[i]):
            asc += ".  "
        else:
            asc += format(chr(input[i]), " <2") + " "

        # Once we've reached bytesperline length, concatenate asc and byte strings and start a new line
        if(not (i + 1) % bytesperline):
            string += byte + " " + asc + "\n"
            asc = ""
            byte = ""

    # Check if there are any remaining characters in the asc and byte strings to be added to string
    if(len(input) % bytesperline):
        string += byte + "   " * (bytesperline - (len(byte) // 3)) \
            + " " + asc + "   " * (bytesperline - (len(asc) // 3)) + "\n"

    return string


def ValidateFriendlyNames() -> None:
    '''Check the validity of each guid from predefined_guids'''

    for f in enumerate(predefined_guids):
        try:
            # Try to convert each friendly name guid into a uuid
            uuid.UUID(f[1])
        except:
            # Alert user if a guid could not be parsed
            logging.debug("Guid " + str(f[0]) + " of predefined_guids dict is invalid")


def AttemptGuidParse(g: bytes) -> str:
    '''
    Attempt to parse a guid. If that fails, notify user, otherwise if it has an associated
    friendly name. Just return the guid if no friendly name can be found.
    '''

    try:
        guid = uuid.UUID(bytes_le=g)
    except:
        return "Unable to parse"

    if(predefined_guids.get(str(guid))):
        return predefined_guids[str(guid)]

    # Return the guid if a friendly name cannot be found
    return str(guid)


def CheckDecodersForGuid(guid: uuid):
    '''Run each decoders CanParse() method to see if it can parse the input guid'''

    for p in Parsers:
        # CanParse() returns true if it recognizes the guid
        if p.CanParse(guid):
            return p
    return None


# def TestParser() -> None:
#     "Loads all decoders and prints out a parse of items in testdata.py"
#     ValidateFriendlyNames()
#     counter = 0
#     for line in TestData:
#         CPER(line).PrettyPrint()
#         counter += 1
