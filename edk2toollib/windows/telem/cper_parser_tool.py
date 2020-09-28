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
from edk2toolext.telem.friendlynames import friendlynamedict
from edk2toolext.telem.testdata import TestData

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

# TODO: Remove once done with development

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

CPER_HEADER_SIZE = 128  # A CPER header is 128 bytes
CPER_SECTION_HEADER_SIZE = 72  # A CPER section header is 72 bytes

# List of plugin classes which inherit from CPER_SECTION_DATA and are
# therefore capable of parsing section data
Parsers = SECTION_PARSER_PLUGIN.__subclasses__()


class CPER(object):
    '''TODO: Fill in'''

    def __init__(self, input: str):
        self.rawData = bytearray.fromhex(input)
        self.header = None
        self.SetCperHeader()
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
        temp = self.rawData[CPER_HEADER_SIZE:CPER_HEADER_SIZE + (CPER_SECTION_HEADER_SIZE * self.header.sectionCount)]

        # Go through each section header and attempt to create a
        # CPER_SECTION_HEADER object. Store each header in SectionHeaders list
        for x in range(self.header.sectionCount):
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
        if self.header.sectionCount != len(self.sectionHeaders):
            print("Section Count of CPER header is incorrect!\n")

        # Print each section header followed by the correlated section
        for s in self.sectionHeaders:
            print("Section " + str(counter))
            print(s.PrettyPrint())
            print(self.ParseSectionData(s))
            counter += 1

    def GetSectionCount(self) -> int:
        "Returns the number of sections in this record"
        return self.header.sectionCount

    def GetErrorSeverity(self) -> str:
        "Returns the severity of this record"
        return self.header.ErrorSeverityParse()

    def GetRecordLength(self) -> int:
        "Returns the length in bytes of this record"
        return self.header.recordLength

    def GetTimestamp(self) -> str:
        "Returns the time at which this error occured"
        return self.header.TimestampParse()

    def GetPlatformId(self) -> str:
        "Returns the guid of the platform"
        return self.header.PlatformIdParse()

    def GetPartitionId(self) -> str:
        "Returns the guid of the software partition"
        return self.header.PartitionIdParse()

    def GetCreatorId(self) -> str:
        "Returns the guid of error creator"
        return self.header.CreatorIdParse()

    def GetRecordId(self) -> str:
        "Returns an 8 byte value which, when used with the creator id, identifies the record"
        return self.header.RecordIdParse()

    def GetFlags(self) -> list:
        "Returns a list of all flags set in the record"
        if self.header.FlagsParse() == "None":
            return []

        return self.header.FlagsParse().split(', ')

    def GetSectionsLength(self) -> list:
        "Returns the length of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.sectionLength)
        return temp

    def GetSectionsOffset(self) -> list:
        "Returns the byte offset of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.sectionOffset)
        return temp

    def GetSectionsFlags(self) -> list:
        "Returns the flags set in each error section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.FlagsParse())
        return temp

    def GetSectionsType(self) -> list:
        "Returns the type of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.SectionTypeParse())
        return temp

    def GetSectionsFruId(self) -> list:
        "Returns the fru id of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.FruIdParse())
        return temp

    def GetSectionsSeverity(self) -> list:
        "Returns the severity of each section error as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.SectionSeverityParse())
        return temp

    def GetSectionsFruString(self) -> list:
        "Returns the fru string of each section as a list"
        temp = []
        for sec in self.sectionHeaders:
            temp.append(sec.FruStringParse())
        return temp


class CPER_HEADER(object):
    '''TODO: Fill in'''

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, input: str):

        self.platformIdValid = False
        self.timestampValid = False
        self.partitionIdValid = False

        (self.signatureStart,
         self.revision,
         self.signatureEnd,
         self.sectionCount,
         self.errorSeverity,
         self.validationBits,
         self.recordLength,
         self.timestamp,
         self.platformId,
         self.partitionId,
         self.creatorId,
         self.notificationType,
         self.recordId,
         self.flags,
         self.persistenceInfo,
         self.reserved) = struct.unpack_from(self.STRUCT_FORMAT, input)

        self.ValidBitsParse()

    def SignatureParse(self) -> str:
        '''Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"'''
        return self.signatureStart.decode('utf-8')

    def RevisionParse(self) -> str:
        '''
        Parse the major and minor version number of the Error Record definition

        TODO: Actually parse out the zeroth and first byte which represent the minor and
        major version numbers respectively
        '''
        return str(self.revision)

    def ErrorSeverityParse(self) -> str:
        '''Parse the error severity for 4 known values'''

        if(self.errorSeverity == 0):
            return "Recoverable"
        elif(self.errorSeverity == 1):
            return "Fatal"
        elif(self.errorSeverity == 2):
            return "Corrected"
        elif(self.errorSeverity == 3):
            return "Informational"

        return "Unknown"

    def ValidBitsParse(self) -> None:
        '''
        Parse validation bits from header

        if bit 1: PlatformId contains valid info\n
        if bit 2: Timestamp contains valid info\n
        if bit 3: PartitionId contains valid info
        '''
        if(self.validationBits & int('0b1', 2)):  # Check bit 0
            self.platformIdValid = True
        if(self.validationBits & int('0b10', 2)):  # Check bit 1
            self.timestampValid = True
        if(self.validationBits & int('0b100', 2)):  # Check bit 2
            self.partitionIdValid = True

    def TimestampParse(self) -> str:
        '''Convert the timestamp into a friendly version formatted to (M/D/YYYY Hours:Minutes:Seconds)'''
        if(self.timestampValid):
            return str((self.timestamp >> 40) & int('0b11111111', 2)) + "/" + \
                str((self.timestamp >> 32) & int('0b11111111', 2)) + "/" + \
                str((((self.timestamp >> 56) & int('0b11111111', 2)) * 100)
                    + ((self.timestamp >> 48) & int('0b11111111', 2))) + " " + \
                format(str((self.timestamp >> 16) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.timestamp >> 8) & int('0b11111111', 2)), "0>2") + ":" + \
                format(str((self.timestamp >> 0) & int('0b11111111', 2)), "0>2")

        return "Invalid"

    def PlatformIdParse(self) -> str:
        '''Parse the Platform GUID (Typically, the Platform SMBIOS UUID)'''

        # Only parse if data is valid
        if(self.platformIdValid):
            return AttemptGuidParse(self.platformId)

        # Platform Id is invalid based on validation bits
        return "Invalid"

    def PartitionIdParse(self) -> str:
        '''Parse the GUID for the Software Partition (if applicable)'''

        # Only parse if data is valid
        if(self.partitionIdValid):
            return AttemptGuidParse(self.partitionId)

        # Partition Id is invalid based on validation bits
        return "Invalid"

    def CreatorIdParse(self) -> str:
        '''Parse the GUID for the GUID of the Error "Creator"'''
        return AttemptGuidParse(self.creatorId)

    def NotificationTypeParse(self) -> str:
        '''Parse the pre-assigned GUID associated with the event (ex.Boot)'''
        return AttemptGuidParse(self.notificationType)

    def RecordIdParse(self) -> str:
        '''When combined with the Creator Id, Record Id identifies the Error Record'''
        return str(self.recordId)

    def FlagsParse(self) -> str:
        '''Check the flags field and populate list containing applicable flags'''

        FlagList = []

        # Check each bit for associated flag
        if(self.flags & int('0b1', 2)):
            FlagList.append("Recovered")
        if(self.flags & int('0b10', 2)):
            FlagList.append("Previous Error")
        if(self.flags & int('0b100', 2)):
            FlagList.append("Simulated")
        if(self.flags & int('0b1000', 2)):
            FlagList.append("Device Driver")
        if(self.flags & int('0b10000', 2)):
            FlagList.append("Critical")
        if(self.flags & int('0b100000', 2)):
            FlagList.append("Persist")

        # If no flags were found
        if(FlagList == []):
            return "None"

        # Join the FlagsList elements separated by commas
        return ", ".join(FlagList)

    def PersistenceInfoParse(self) -> str:
        '''Parse the persistence info which is produced and consumed by the creator of the Error Record'''
        return str(self.persistenceInfo)

    def PrettyPrint(self) -> str:
        '''Print relevant portions of the CPER header. Change to suit your needs'''

        string = ""
        temp = ""

        string += "Record Length:  " + str(self.recordLength) + '\n'

        temp = self.TimestampParse()
        string += "Time of error:  " + temp + '\n'

        temp = self.ErrorSeverityParse()
        string += "Error severity: " + temp + '\n'

        temp = self.FlagsParse()
        string += "Flags Id:       " + temp + '\n'

        temp = self.PlatformIdParse()
        string += "Platform Id:    " + temp + '\n'

        temp = self.PartitionIdParse()
        string += "Partition Id:   " + temp + '\n'

        temp = self.CreatorIdParse()
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
    '''Check the validity of each guid from the friendlynamedict in friendlynames.py'''
    rowcounter = 0  # Used to track which row we are checking

    for f in friendlynamedict:
        try:
            # Try to convert each friendly name guid into a uuid
            uuid.UUID(f)
        except:
            # Alert user if a guid could not be parsed
            logging.debug("Guid " + str(rowcounter) + " of FriendlyName \
                          in dictionary located in friendlyname.py file is invalid")

        rowcounter += 1


def AttemptGuidParse(g: bytes) -> str:
    '''
    Attempt to parse a guid. If that fails, notify user, otherwise if it has an associated
    friendly name. Just return the guid if no friendly name can be found.
    '''

    try:
        guid = uuid.UUID(bytes_le=g)
    except:
        return "Unable to parse"

    if(friendlynamedict.get(str(guid))):
        return friendlynamedict[str(guid)]

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
