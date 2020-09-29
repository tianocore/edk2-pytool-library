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
import edk2toolext.telem.decoders
from edk2toollib.windows.telem.cper_section_data import SECTION_PARSER_PLUGIN
from edk2toolext.telem.friendlynames import FriendlyNameDict
from edk2toollib.windows.telem.cper_parser_tool_test import TestData

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

# List of plugin classes which inherit from CPER_SECTION_DATA and are
# therefore capable of parsing section data
Parsers = SECTION_PARSER_PLUGIN.__subclasses__()


class GENERIC_FIELD(object):

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

    def GetString(self, parsed = True):
        '''Returns a string version of this field. If parsed is true,
        it will return a parsed version of the field if available'''
        if(parsed):
            return str(self.parsed_value)
        
        return str(self.raw_value)
    
    def GetRaw(self):
        return self.raw_value


class SIGNATURE_FIELD(GENERIC_FIELD):
    '''Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"'''
    
    def __init__(self,raw_value):
        super().__init__(raw_value)

    def Parse(self):
        # TODO: Finish
        # self.parsed_value = self.raw_value.decode('ascii')
        
        # if(self.parsed_value == "CPER"):
        #     self.valid = True
        self.valid = True

class REVISION_FIELD(GENERIC_FIELD):
    '''
        Parse the major and minor version number of the Error Record definition

        TODO: Actually parse out the zeroth and first byte which represent the minor and
        major version numbers respectively
        '''

    def __init__(self,raw_value):
        super().__init__(raw_value)


class SECTION_COUNT_FIELD(GENERIC_FIELD):
    '''The number of sections in this record'''

    def __init__(self,raw_value):
        super().__init__(raw_value)
        

class SEVERITY_FIELD(GENERIC_FIELD):
    '''
        The severity of this record or section. The severity of a record
        corresponds to the most severe error section
    '''

    def __init__(self,raw_value):
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
        Capture the validation bits from CPER header

        if bit 1: PlatformId contains valid info\n
        if bit 2: Timestamp contains valid info\n
        if bit 3: PartitionId contains valid info
        '''
    def __init__(self,raw_value):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = True
        self.platform_id_valid = False
        self.timestamp_valid = False
        self.partition_id_valid = False

    def Parse(self):
        
        self.parsed_value = "Platform ID Valid?: "
        if(self.raw_value & int('0b1', 2)):   # Check bit 0
            self.platform_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"
        
        self.parsed_value = "Timestamp Valid?: "

        if(self.raw_value & int('0b10', 2)):  # Check bit 1
            self.timestamp_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"
        
        self.parsed_value = "Partition ID Valid?: "
        
        if(self.raw_value & int('0b100', 2)): # Check bit 2
            self.partition_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"
    
    def PlatformIdValid(self):
        return self.partition_id_valid
    
    def TimestampValid(self):
        return self.timestamp_valid
    
    def PartitionIdValid(self):
        return self.partition_id_valid


class RECORD_LENGTH_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value):
        super().__init__(raw_value)


class TIMESTAMP_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value,valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self,valid_bits_field):
        if(valid_bits_field.TimestampValid()):
            self.parsed_value = str((self.raw_value >> 40) & int('0b11111111', 2)) + "/" + \
                str((self.raw_value >> 32) & int('0b11111111', 2)) + "/" + \
                str((((self.raw_value >> 56) & int('0b11111111', 2)) * 100)
                    + ((self.raw_value >> 48) & int('0b11111111', 2))) + " " + \
                format(str((self.raw_value >> 16) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.raw_value >> 8) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.raw_value >> 0) & int('0b11111111', 2)), "0>2")

        self.parsed_value = "Invalid"
        self.valid = True


class PLATFORM_ID_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self,valid_bits_field):
        if(valid_bits_field.PlatformIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)
        
        self.parsed_value = "Invalid"
        self.valid = True


class PARTITION_ID_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value, valid_bits_field):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = False
        self.Parse(valid_bits_field)

    def Parse(self,valid_bits_field):
        if(valid_bits_field.PartitionIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)

        self.parsed_value = "Invalid"
        self.valid = True


class CREATOR_ID_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value):
        super().__init__(raw_value)

    def Parse(self):
        self.parsed_value = AttemptGuidParse(self.raw_value)
        self.valid = True


class NOTIFICATION_TYPE_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value):
        super().__init__(raw_value)


class RECORD_ID_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value):
        super().__init__(raw_value)


class FLAGS_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value):
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
        self.parsed_value =  ", ".join(self.flags_list)

        self.valid = True
        
    
    def GetFlagsList(self):
        return self.flags_list


class PERSISTENCE_INFO_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value):
        super().__init__(raw_value)


class SECTION_LENGTH_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value):
        super().__init__(raw_value)


class SECTION_OFFSET_FIELD(GENERIC_FIELD):
    
    def __init__(self,raw_value):
        super().__init__(raw_value)


class SECTION_HEADER_VALIDATION_BITS_FIELD(GENERIC_FIELD):
    '''
        if bit 0: FruId contains valid info\n
        if bit 1: FruId String contains valid info
    '''
    def __init__(self,raw_value):
        self.raw_value = raw_value
        self.parsed_value = ""
        self.valid = True
        self.fru_id = False
        self.fru_string = False

    def Parse(self):
        
        self.parsed_value = "Fru ID Valid?: "
        if(self.raw_value & int('0b1', 2)):   # Check bit 0
            self.platform_id_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"
        
        self.parsed_value = "Fru String Valid?: "
        if(self.raw_value & int('0b10', 2)):  # Check bit 1
            self.timestamp_valid = True
            self.parsed_value += "True\n"
        else:
            self.parsed_value += "False\n"

    
    def FruIdValid(self):
        return self.FruIdValid
    
    def FruStringValid(self):
        return self.FruStringValid
    

class SECTION_TYPE_FIELD(GENERIC_FIELD):

    def __init__(self,raw_value):
        super().__init__(raw_value)

    def Parse(self,valid_bits_field):
        if(valid_bits_field.PartitionIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)

        self.parsed_value = "Invalid"
        self.valid = True


class FRU_ID_FIELD(GENERIC_FIELD):
    
    def Parse(self,valid_bits_field):
        if(valid_bits_field.FruIdValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)

        self.parsed_value = "Invalid"
        self.valid = True


class FRU_STRING_FIELD(GENERIC_FIELD):
    
    def Parse(self,valid_bits_field):
        if(valid_bits_field.FruStringValid()):
            self.parsed_value = AttemptGuidParse(self.raw_value)

        self.parsed_value = "Invalid"
        self.valid = True
       

class CPER(object):
    '''TODO: Fill in'''

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
                print("Error parsing section header %d" % x)

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
        return self.header.section_count.GetRaw()

    def GetErrorSeverity(self) -> str:
        "Returns the severity of this record"
        return self.header.error_severity.GetString()

    def GetRecordLength(self) -> int:
        "Returns the length in bytes of this record"
        return self.header.record_length

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
    '''TODO: Fill in'''

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
        self.flags = FLAGS_FIELD(self.flags)
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
    '''TODO: Fill in'''

    STRUCT_FORMAT = "=IIHccI16s16sI20s"

    def __init__(self, input: str):

        self.FlagList = []  # go to self.FlagsParse() to see description of this field
        self.fruIdValid = False
        self.fruStringValid = False

        (self.sectionOffset,
            self.sectionLength,
            self.revision,
            self.validationBits,
            self.reserved,
            self.flags,
            self.sectionType,
            self.fruId,
            self.sectionSeverity,
            self.fruString) = struct.unpack_from(self.STRUCT_FORMAT, input)

        self.FlagsParse()
        self.ValidBitsParse()

    def RevisionParse(self) -> str:
        '''
        Parse the major and minor version number of the Error Record definition

        TODO: Actually parse the zeroth and first byte which represent the minor
        and major version numbers respectively
        '''

        return str(self.revision)

    def ValidBitsParse(self) -> None:
        '''
        if bit 0: FruId contains valid info\n
        if bit 1: FruId String contains valid info
        '''

        if(ord(self.validationBits) & 0b1):  # check bit 0
            self.fruIdValid = True
        if(ord(self.validationBits) & 0b10):  # check bit 1
            self.fruStringValid = True

    def FlagsParse(self) -> None:
        '''
        Check the flags field and populate list containing applicable flags

        if bit 0: This is the section to be associated with the error condition\n
        if bit 1: The error was not contained within the processor or memery heirarchy\n
        if bit 2: The component has been reset and must be reinitialized\n
        if bit 3: Error threshold exceeded for this component\n
        if bit 4: Resource could not be queried for additional information\n
        if bit 5: Action has been taken to contain the error, but the error has not been corrected
        '''

        FlagList = []

        if(self.flags & int('0b1', 2)):  # Check bit 0
            FlagList.append("Primary")
        if(self.flags & int('0b10', 2)):  # Check bit 1
            FlagList.append("Containment Warning")
        if(self.flags & int('0b100', 2)):  # Check bit 2
            FlagList.append("Reset")
        if(self.flags & int('0b1000', 2)):  # Check bit 3
            FlagList.append("Error Threshold Exceeded")
        if(self.flags & int('0b10000', 2)):  # Check bit 4
            FlagList.append("Resource Not Accessible")
        if(self.flags & int('0b100000', 2)):  # Check bit 5
            FlagList.append("Latent Error")

        # If no flags were found
        if(FlagList == []):
            return "None"

        # Join the FlagsList elements separated by commas
        return ' '.join(FlagList)

    def SectionTypeParse(self) -> str:
        '''Parse the Section Type which is a pre-defined GUID indicating that this section is from a particular error'''

        return AttemptGuidParse(self.sectionType)

    def FruIdParse(self) -> str:
        '''TODO: Fill in - not detailed in CPER doc'''

        # Only parse if data is valid
        if(self.fruIdValid):
            return AttemptGuidParse(self.fruId)

        return "Invalid"

    def SectionSeverityParse(self) -> str:
        '''
        Parse the error severity for 4 known values

        NOTE: A severity of "Informational" indicates that the section contains extra information that
        can be safely ignored
        '''

        if(self.sectionSeverity == 0):
            return "Recoverable"
        elif(self.sectionSeverity == 1):
            return "Fatal"
        elif(self.sectionSeverity == 2):
            return "Corrected"
        elif(self.sectionSeverity == 3):
            return "Informational"

        return ""

    def FruStringParse(self) -> str:
        '''Parse out the custom string identifying the Fru hardware'''

        # Only parse if data is valid
        if(self.fruStringValid):

            # Convert the Fru string from bytes to a string
            try:
                return "".join([chr(x) for x in self.fruString])
            except:
                return "Unable to parse"

        return "Invalid"

    def PrettyPrint(self) -> str:
        '''Print relevant portions of the section header. Change to suit your needs'''

        string = ""
        temp = ""

        string += "Section Length:      " + str(self.sectionLength) + '\n'

        temp = self.FlagsParse()
        string += "Flags:               " + temp + '\n'

        temp = self.SectionSeverityParse()
        string += "Section Severity:    " + temp + '\n'

        temp = self.SectionTypeParse()
        string += "Section Type:        " + temp + '\n'

        temp = self.FruIdParse()
        string += "Fru Id:              " + temp + '\n'

        temp = self.FruStringParse()
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
    '''Check the validity of each guid from the FriendlyNameDict in friendlynames.py'''

    for f in enumerate(FriendlyNameDict):
        try:
            # Try to convert each friendly name guid into a uuid
            uuid.UUID(f[1])
        except:
            # Alert user if a guid could not be parsed
            logging.debug("Guid " + str(f[0]) + " of FriendlyName \
                          in dictionary located in friendlyname.py file is invalid")


def AttemptGuidParse(g: bytes) -> str:
    '''
    Attempt to parse a guid. If that fails, notify user, otherwise if it has an associated
    friendly name. Just return the guid if no friendly name can be found.
    '''

    try:
        guid = uuid.UUID(bytes_le=g)
    except:
        return "Unable to parse"

    if(FriendlyNameDict.get(str(guid))):
        return FriendlyNameDict[str(guid)]

    # Return the guid if a friendly name cannot be found
    return str(guid)


def CheckDecodersForGuid(guid: uuid):
    '''Run each decoders CanParse() method to see if it can parse the input guid'''

    for p in Parsers:
        # CanParse() returns true if it recognizes the guid
        if p.CanParse(guid):
            return p
    return None


def TestParser() -> None:
    "Loads all decoders and prints out a parse of items in testdata.py"
    ValidateFriendlyNames()
    counter = 0
    for line in TestData:
        CPER(line).PrettyPrint()
        counter += 1
