# @file parser_main.py
# TODO: Write Readme and short description
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##


import struct
import uuid
import csv
import sys
from plugins import *
from cper_section_data import SECTION_PARSER_PLUGIN

"""
CPER: Common Platform Error Record

Structure of a CPER:
Signature           (0   byte offset, 4  byte length) : CPER Signature
Revision            (4   byte offset, 2  byte length) : The Revision of CPER
Signature End       (6   byte offset, 4  byte length) : Must always be 0xffffffff
Section Count       (10  byte offset, 4  byte length) : The Number of Sections of CPER
Error Severity      (12  byte offset, 4  byte length) : The Severity of Error of CPER
Validation Bits     (16  byte offset, 4  byte length) : Identify Valid IDs of the CPER
Record Length       (20  byte offset, 4  byte length) : The size(in bytes) of the ENTIRE Error Record
Timestamp           (24  byte offset, 8  byte length) : The Time at which the Error occured
Platform ID         (32  byte offset, 16 byte length) : The Platform GUID (Typically, the Platform SMBIOS UUID)
Partition ID        (48  byte offset, 16 byte length) : The Software Partition (if applicable)
Creator ID          (64  byte offset, 16 byte length) : The GUID of the Error "Creator"
Notification Type   (80  byte offset, 16 byte length) : A pre-assigned GUID associated with the event (ex.Boot)
Record ID           (96  byte offset, 8  byte length) : When combined with the Creator ID, identifies the Error Record
Flags               (104 byte offset, 4  byte length) : A specific "flag" for the Error Record. Flags are pre-defined values which provide more information on the Error
Persistence Info    (108 byte offset, 8  byte length) : Produced and consumed by the creator of the Error Record.There are no guidelines for these bytes.
Reserved            (116 byte offset, 12 byte length) : Must be zero


A Section Header within a CPER has the following structure

Section Offset      (0  byte offset, 4  byte length) : Offset from start of the CPER(not the start of the section) to the beginning of the section body
Section Length      (4  byte offset, 4  byte length) : Length in bytes of the section body
Revision            (8  byte offset, 2  byte length) : Represents the major and minor version number of the Error Record definition
Validation Bits     (10 byte offset, 1  byte length) : Indicates the validity of the FRU ID and FRU String fields
Reserved            (11 byte offset, 1  byte length) : Must be zero
Flags               (12 byte offset, 4  byte length) : Contains info describing the Error Record (ex. Is this the primary section of the error, has the component been reset if applicable, has the error been contained)
Section Type        (16 byte offset, 16 byte length) : Holds a pre-defined GUID value indicating that this section is from a particular error
FRU ID              (32 byte offset, 16 byte length) : ? Not detailed in the CPER doc
Section Severity    (48 byte offset, 4  byte length) : Value from 0 - 3 indicating the severity of the error
FRU String          (52 byte offset, 20 byte length) : String identifying the FRU hardware


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

CPER_HEADER_SIZE = 128
CPER_SECTION_HEADER_SIZE = 72
FriendlyNames = {}
Parsers = []

concat_s = lambda x, y : (''.join([x, y," "]))
concat_n = lambda x, y : (''.join([x, y,"\n"]))
concat   = lambda x, y : (''.join([x, y]))
empty    = lambda x : x == "" or x == None
neq      = lambda x,y : x != y
eq       = lambda x,y : x == y

class CPER(object):

    def __init__(self, input):
        self.RawData = bytearray.fromhex(input)
        self.Header = None
        self.SetCPERHeader()
        self.SectionHeaders = []
        self.SetSectionHeaders()

    ##
    # Turn the portion of the raw input associated with the CPER head into a CPER_HEAD object
    ##
    def SetCPERHeader(self):
        temp = self.RawData[:CPER_HEADER_SIZE]
        self.Header = CPER_HEADER(temp)

    ##
    # Set each of the section headers to CPER_SECTION_HEADER objects
    ##
    def SetSectionHeaders(self):
        try:
            temp = self.RawData[CPER_HEADER_SIZE:CPER_HEADER_SIZE + (CPER_SECTION_HEADER_SIZE * self.Header.SectionCount)]
            for x in range(self.Header.SectionCount):
                self.SectionHeaders.append(CPER_SECTION_HEADER(temp[x * CPER_SECTION_HEADER_SIZE: (x + 1) * CPER_SECTION_HEADER_SIZE]))
        except:
            pass
    
    ##
    # Get each of the actual section data pieces and either pass it to something which can parse it, or dump the hex
    ##
    def ParseSectionData(self, s):
        p = CheckPluginsForGuid(s.SectionType)
        if p != None:
            try:
                # print("Passing data to plugin " + str(p) + ". Data wihin CPER from byte " + str(x.SectionOffset) + " to byte " + str(x.SectionOffset + x.SectionLength) \
                #      + ". Total section length: " + str(x.SectionLength))
                return p.Parse(self.RawData[s.SectionOffset : s.SectionOffset + s.SectionLength])
            except:
                print("Unable to apply plugin " + str(p)  + " on section data!")

        return HexDump(self.RawData[s.SectionOffset : s.SectionOffset + s.SectionLength],16)
    
    def PrettyPrint(self):
        counter = 1
        
        print(self.Header.PrettyPrint())

        for s in self.SectionHeaders:
            print(concat("Section ",str(counter)))
            counter += 1
            print(s.PrettyPrint())
            print(self.ParseSectionData(s))

class CPER_HEADER(object):

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, input):
        (self.SignatureStart,
         self.Revision,
         self.SignatureEnd,
         self.SectionCount,
         self.ErrorSeverity,
         self.ValidationBits,
         self.RecordLength,
         self.Timestamp,
         self.PlatformID,
         self.PartitionID,
         self.CreatorID,
         self.NotificationType,
         self.RecordID,
         self.Flags,
         self.PersistenceInfo,
         self.Reserved) = struct.unpack_from(self.STRUCT_FORMAT, input)
            
        self.ValidBitsList = [False,False,False]
        self.ValidBitsParse()

    ##
    # Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"
    ##
    def SignatureParse(self) -> str:
        return str(self.SignatureStart)

    ##
    # Parse the major and minor version number of the Error Record definition
    #
    # TODO: Actually parse out the zeroth and first byte which represent the minor and major version numbers respectively 
    ##
    def RevisionParse(self) -> str:
        return str(self.Revision)

    ##
    #
    ##
    def ErrorSeverityParse(self) -> str:
        if(self.ErrorSeverity == 0):
            return "Recoverable"
        elif(self.ErrorSeverity == 1):
            return "Fatal"
        elif(self.ErrorSeverity == 2):
            return "Corrected"
        elif(self.ErrorSeverity == 3):
            return "Informational"
        
        return "Unknown"

    ##
    # if bit 1: PlatformID contains valid info
    # if bit 2: Timestamp contains valid info
    # if bit 3: PartitionID contains valid info
    ##
    def ValidBitsParse(self):
        if(self.ValidationBits & int('0b1', 2)):
            self.ValidBitsList[0] = True
        if(self.ValidationBits & int('0b10', 2)):
            self.ValidBitsList[1] = True
        if(self.ValidationBits & int('0b100', 2)):
            self.ValidBitsList[2] = True

    ##
    # Convert the timestamp into a friendly version formatted to (MM/DD/YY Hours:Minutes:Seconds)
    ##
    def TimestampParse(self) -> str:
        if(self.ValidBitsList[1]):
            return str(( self.Timestamp >> 40) & int('0b11111111', 2)) + "/" + \
                                     str(( self.Timestamp >> 32) & int('0b11111111', 2)) + "/" + \
                                     str(((self.Timestamp >> 48) & int('0b11111111', 2) * 100) + (self.Timestamp >> 56) & int('0b11111111', 2)) + " " + \
                                     str(( self.Timestamp >> 16) & int('0b11111111', 2)) + ":" + \
                                     str(( self.Timestamp >> 8 ) & int('0b11111111', 2)) + ":" + \
                                     str(( self.Timestamp >> 0 ) & int('0b11111111', 2))
        
        return ""

    ##
    # Parse the Platform GUID (Typically, the Platform SMBIOS UUID)
    ##
    def PlatformIDParse(self) -> str:
        if(self.ValidBitsList[0]): # TODO: Uncomment this   
            try:
                guid = uuid.UUID(bytes_le=self.PlatformID)
                if(FriendlyNames.get(guid)):
                    return FriendlyNames[guid]
            except:
                return str(uuid.UUID(bytes_le=self.PlatformID))
        
        return ""

    ##
    # Parse the GUID for the Software Partition (if applicable)
    ##
    def PartitionIDParse(self) -> str:
        # if(self.ValidBitsList[2]): # TODO: Uncomment this      
        try:
            guid = uuid.UUID(bytes_le=self.PartitionID)
            if(FriendlyNames.get(guid)):
                return FriendlyNames[guid]
        except:
            return str(uuid.UUID(bytes_le=self.PartitionID))
        
        return ""

    ##
    # Parse the GUID for the GUID of the Error "Creator"
    ##
    def CreatorIDParse(self) -> str:
        try:
            guid = uuid.UUID(bytes_le=self.CreatorID)
            if(FriendlyNames.get(guid)):
                return FriendlyNames[guid]
        except:
            return str(uuid.UUID(bytes_le=self.CreatorID))

        return ""
        

    ##
    # Parse the pre-assigned GUID associated with the event (ex.Boot)
    ##
    def NotificationTypeParse(self) -> str:
        try:
            guid = uuid.UUID(bytes_le=self.NotificationType)
            if(FriendlyNames.get(guid)):
                return FriendlyNames[guid]
        except:
            return str(uuid.UUID(bytes_le=self.NotificationType))

        return ""

    ##
    # When combined with the Creator ID, Record ID identifies the Error Record
    ##
    def RecordIDParse(self) -> str:
        return str(self.RecordID) 

    ##
    # Check the flags field and populate list containing applicable flags
    ##
    def FlagsParse(self):

        FlagList = []

        if(self.Flags & int('0b1', 2)):
            FlagList.append("Recovered")
        if(self.Flags & int('0b10', 2)):
            FlagList.append("Previous Error")
        if(self.Flags & int('0b100', 2)):
            FlagList.append("Simulated")
        if(self.Flags & int('0b1000', 2)):
            FlagList.append("Device Driver")
        if(self.Flags & int('0b10000', 2)):
            FlagList.append("Critical")
        if(self.Flags & int('0b100000', 2)):
            FlagList.append("Persist")

        return ", ".join(FlagList)

    ##
    # Parse the persistence info which is produced and consumed by the creator of the Error Record
    ##
    def PersistenceInfoParse(self) -> str:
        return str(self.PersistenceInfo)


    def PrettyPrint(self) -> str:

        string = ""
        temp = ""

        string = concat_n(string,concat("Record Length:  ",str(self.RecordLength)))

        temp = self.TimestampParse()
        string = concat_n(string,concat("Time of error:  ","?" if empty(temp) else temp))

        temp = self.ErrorSeverityParse()
        string = concat_n(string,concat("Error severity: ","?" if empty(temp) else temp))

        temp = self.FlagsParse()
        string = concat_n(string,concat("Flags ID:       ","?" if empty(temp) else temp))

        temp = self.PlatformIDParse()
        string = concat_n(string,concat("Platform ID:    ","?" if empty(temp) else temp))

        temp = self.PartitionIDParse()
        string = concat_n(string,concat("Partition ID:   ","?" if empty(temp) else temp))

        temp = self.CreatorIDParse()
        string = concat_n(string,concat("Creator ID:     ","?" if empty(temp) else temp))

        return string

class CPER_SECTION_HEADER(object):

    STRUCT_FORMAT = "=IIH1s1sH16s16sH20s"

    def __init__(self, cper_section_byte_array):

        self.ValidSectionBitsList = [False,False]
        self.FlagList = []

        (self.SectionOffset,
            self.SectionLength,
            self.Revision,
            self.ValidationBits,
            self.Reserved,
            self.Flags,
            self.SectionType,
            self.FRUID,
            self.SectionSeverity,
            self.FRUString) = struct.unpack_from(self.STRUCT_FORMAT, cper_section_byte_array)

        self.FlagsParse()

    ##
    # Parse the major and minor version number of the Error Record definition
    #
    # TODO: Actually parse the zeroth and first byte which represent the minor and major version numbers respectively 
    ##
    def RevisionParse(self) -> str:
        return str(self.Revision)

    ##
    # if bit 0: FruID contains valid info
    # if bit 1: FruID String contains valid info
    ##
    def ValidationBitsParse(self):
        if(self.ValidationBits & int('0b1', 2)):
            self.ValidSectionBitsList[0] = True
        if(self.ValidationBits & int('0b10', 2)):
            self.ValidSectionBitsList[1] = True

    ##
    # Check the flags field and populate list containing applicable flags
    # if bit 0: This is the section to be associated with the error condition
    # if bit 1: The error was not contained within the processor or memery heirarchy
    # if bit 2: The component has been reset and must be reinitialized
    # if bit 3: Error threshold exceeded for this componenet
    # if bit 4: Resource could not be queried for additional information
    # if bit 5: Action has been taken to contain the error, but the error has not been corrected
    ##
    def FlagsParse(self):

        FlagList = []

        if(self.Flags & int('0b1', 2)):
            FlagList.append("Primary")
        if(self.Flags & int('0b10', 2)):
            FlagList.append("Containment Warning")
        if(self.Flags & int('0b100', 2)):
            FlagList.append("Reset")
        if(self.Flags & int('0b1000', 2)):
            FlagList.append("Error Threshold Exceeded")
        if(self.Flags & int('0b10000', 2)):
            FlagList.append("Resource Not Accessible")
        if(self.Flags & int('0b100000', 2)):
            FlagList.append("Latent Error")

        return ' '.join(FlagList)

    ##
    # Parse the Section Type which is a pre-defined GUID indicating that this section is from a particular error
    ##
    def SectionTypeParse(self) -> str:

        try:
            guid = uuid.UUID(bytes_le=self.SectionType)
            if(FriendlyNames.get(guid)):
                return FriendlyNames[guid]
        except:
            return str(uuid.UUID(bytes_le=self.SectionType))
        
        return ""

    ##
    # TODO: Fill in
    ##
    def FRUIDParse(self) -> str:
        # if(self.ValidSectionBitsList[0]): # TODO: Uncomment this
        try:
            guid = uuid.UUID(bytes_le=self.FRUID)
            if(FriendlyNames.get(guid)):
                return FriendlyNames[guid]
        except:
            return str(uuid.UUID(bytes_le=self.FRUID))

        return ""

    ##
    # Parse the severity of the error in this section
    #
    # Note that severity of "Informational" indicates that the section contains extra information that can be safely ignored by error handling software.
    ##
    def SectionSeverityParse(self) -> str:
        if(self.SectionSeverity == 0):
            return "Recoverable"
        elif(self.SectionSeverity == 1):
            return "Fatal"
        elif(self.SectionSeverity == 2):
            return "Corrected"
        elif(self.SectionSeverity == 3):
            return "Informational"
        else:
            return ""

    ##
    # Parse out the custom string identifying the FRU hardware
    ##
    def FRUStringParse(self) -> str:
        if(self.ValidSectionBitsList[1]):
            return self.FRUString
        else:
            return ""

    # A Section Header within a CPER has the following structure

    # Section Offset      (0  byte offset, 4  byte length) : Offset from start of the CPER(not the start of the section) to the beginning of the section body
    # Section Length      (4  byte offset, 4  byte length) : Length in bytes of the section body
    # Revision            (8  byte offset, 2  byte length) : Represents the major and minor version number of the Error Record definition
    # Validation Bits     (10 byte offset, 1  byte length) : Indicates the validity of the FRU ID and FRU String fields
    # Reserved            (11 byte offset, 1  byte length) : Must be zero
    # Flags               (12 byte offset, 4  byte length) : Contains info describing the Error Record (ex. Is this the primary section of the error, has the component been reset if applicable, has the error been contained)
    # Section Type        (16 byte offset, 16 byte length) : Holds a pre-defined GUID value indicating that this section is from a particular error
    # FRU ID              (32 byte offset, 16 byte length) : ? Not detailed in the CPER doc
    # Section Severity    (48 byte offset, 4  byte length) : Value from 0 - 3 indicating the severity of the error
    # FRU String          (52 byte offset, 20 byte length) : String identifying the FRU hardware

    def PrettyPrint(self) -> str:
        string = ""
        temp = ""

        string = concat_n(string,concat("Section Length:     ",str(self.SectionLength)))

        temp = self.FlagsParse()
        string = concat_n(string,concat("Flags:             ","?" if empty(temp) else temp))

        temp = self.SectionSeverityParse()
        string = concat_n(string,concat("Section Severity:  ","?" if empty(temp) else temp))

        temp = self.SectionTypeParse()
        string = concat_n(string,concat("Section Type:      ","?" if empty(temp) else temp))

        temp = self.FRUIDParse()
        string = concat_n(string,concat("FRU ID:            ","?" if empty(temp) else temp))
        
        temp = self.FRUStringParse()
        string = concat_n(string,concat("FRU String:        ","?" if empty(temp) else temp))
        
        return string

##
# Dumps byte code of input
##
def HexDump(input, bytesperline):

    inputlen    = len(input)
    string      = ""
    asc         = ""
    byte        = ""
    rangecheck  = lambda x : x < 31 or x > 127

    for i in range(inputlen):
        byte = concat_s(byte, format(input[i],'02X'))
        if rangecheck(input[i]):
                asc = concat_s(asc,". ")
        else:
            asc = concat_s(asc,format(chr(input[i])," <2"))
        
        if(not (i + 1) % bytesperline):
            string = concat_n(string,concat(byte,asc))
            asc = ""
            byte = ""
    
    if(inputlen % bytesperline):  
        string = concat(string,concat_n(concat(byte,"   " * (bytesperline - (len(byte)//3))),concat(asc,"   " * (bytesperline - (len(asc)//3)))))
    return string

##
# Import Friendly Names from friendlynames.csv
##
def ImportFriendlyNames():
    with open('friendlynames.csv','r') as csv_file:
        
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader) # skip the header
        rowcounter = 2

        for row in csv_reader:
            try:
                FriendlyNames[uuid.UUID(row[1].strip())] = row[0]
            except:
                print("Unable to add row " + str(rowcounter) + " to the friendly name dictionary!")
            
            rowcounter += 1

##
# Load all plugins from the /plugins folder
##
def LoadPlugins():
    subclasslist = SECTION_PARSER_PLUGIN.__subclasses__()
    
    for cl in subclasslist:
        Parsers.append(cl())

##
# Run each plugins CanParse() method to see if it can parse the input guid
##
def CheckPluginsForGuid(guid):
    for p in Parsers:
        if p.CanParse(guid):
            return p

    return None

##
# Parse a list of cper record strings
##
def parse_cper_list(input):
    for x in input:
        CPER(x)

##
# Parse a single cper record
##
def parse_cper(input):
    c = CPER(input)
    c.PrettyPrint()

##
# Parse cper records from event viewer xml file
##
def parse_from_xml(input): # TODO: Create xml parser
    pass

# Main function used to test functionality
if __name__ == "__main__":
    LoadPlugins()
    ImportFriendlyNames()
    with open('HeadersData.csv','r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader) # skip the header

        for row in csv_reader:
            parse_cper(row[0])
