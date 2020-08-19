# @file cper_parser.py
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

Structure of a CPER Header:
Signature           (0   byte offset, 4  byte length) : CPER Signature
Revision            (4   byte offset, 2  byte length) : The Revision of CPER
Signature End       (6   byte offset, 4  byte length) : Must always be 0xffffffff
Section Count       (10  byte offset, 2  byte length) : The Number of Sections of CPER
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

CPER_HEADER_SIZE            = 128 # A CPER header is 128 bytes 
CPER_SECTION_HEADER_SIZE    = 72  # A CPER section header is 72 bytes
FriendlyNames               = {}  # dict loaded from friendlynames.csv used to associate guids with friendly strings
Parsers                     = []  # list of plugin classes which inherit from CPER_SECTION_DATA and are therefore capable of parsing section data

# Using these lambda concat statements to guarantee linear runtime when concatonating strings, and for simplicity
concat_s = lambda x,y  : (''.join([x,y," "]))  # Concatenate two strings and put a space at the end
concat_n = lambda x,y  : (''.join([x,y,"\n"])) # Concatenate two strings and put a newline at the end
concat   = lambda x,y  : (''.join([x,y]))      # Concatenate two strings

# Useful lambdas
empty    = lambda x     : x == "" or x == None or x == []   # True if x is an empty string, list, etc.
neq      = lambda x,y   : x != y                            # True if x and y are not equal
eq       = lambda x,y   : x == y                            # True if x and y are equal

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
        try:
            self.Header = CPER_HEADER(temp)
        except:
            print("Unable to parse record")

    ##
    # Set each of the section headers to CPER_SECTION_HEADER objects
    ##
    def SetSectionHeaders(self):
        # Section of RawData containing the section headers
        temp = self.RawData[CPER_HEADER_SIZE:CPER_HEADER_SIZE + (CPER_SECTION_HEADER_SIZE * self.Header.SectionCount)]

        # Go through each section header and attempt to create a CPER_SECTION_HEADER object. Store each header in SectionHeaders list
        for x in range(self.Header.SectionCount):
            try: # Don't want to stop runtime if parsing fails
                self.SectionHeaders.append(CPER_SECTION_HEADER(temp[x * CPER_SECTION_HEADER_SIZE: (x + 1) * CPER_SECTION_HEADER_SIZE]))
            except:
                print("Error parsing section header %d" % x)

    ##
    # Get each of the actual section data pieces and either pass it to something which can parse it, or dump the hex
    ##
    def ParseSectionData(self, s):
        p = CheckPluginsForGuid(s.SectionType) # Runs CanParse() on each plugin in .\plugins\ folder to see if it can parse the section type 
        
        # if we've found a plugin which can parse this section
        if p != None: 
            try:
                # pass the data to that parser which should return a string of the data parsed/formatted
                return p.Parse(self.RawData[s.SectionOffset : s.SectionOffset + s.SectionLength])
            except:
                print("Unable to apply plugin " + str(p)  + " on section data!")

        # If no plugin can parse the section data, do a simple hex dump
        return HexDump(self.RawData[s.SectionOffset : s.SectionOffset + s.SectionLength],16)
    
    ##
    # Print the entire CPER record
    ##
    def PrettyPrint(self):
        counter = 1
        
        print(self.Header.PrettyPrint())

        # Alert user that section count doesn't match sections being printed.
        # This could be because there was an error parsing a section, or the
        # section count is incorrect
        if neq(self.Header.SectionCount,self.SectionHeaders.count):
            print("Section Count of CPER header \n")

        # Print each section header followed by the correlated section
        for s in self.SectionHeaders:
            print(concat("Section ",str(counter)))
            print(s.PrettyPrint())
            print(self.ParseSectionData(s))
            counter += 1

# CPER: Common Platform Error Record

# Structure of a CPER Header:
# Signature           (0   byte offset, 4  byte length) : CPER Signature
# Revision            (4   byte offset, 2  byte length) : The Revision of CPER
# Signature End       (6   byte offset, 4  byte length) : Must always be 0xffffffff
# Section Count       (10  byte offset, 2  byte length) : The Number of Sections of CPER
# Error Severity      (12  byte offset, 4  byte length) : The Severity of Error of CPER
# Validation Bits     (16  byte offset, 4  byte length) : Identify Valid IDs of the CPER
# Record Length       (20  byte offset, 4  byte length) : The size(in bytes) of the ENTIRE Error Record
# Timestamp           (24  byte offset, 8  byte length) : The Time at which the Error occured
# Platform ID         (32  byte offset, 16 byte length) : The Platform GUID (Typically, the Platform SMBIOS UUID)
# Partition ID        (48  byte offset, 16 byte length) : The Software Partition (if applicable)
# Creator ID          (64  byte offset, 16 byte length) : The GUID of the Error "Creator"
# Notification Type   (80  byte offset, 16 byte length) : A pre-assigned GUID associated with the event (ex.Boot)
# Record ID           (96  byte offset, 8  byte length) : When combined with the Creator ID, identifies the Error Record
# Flags               (104 byte offset, 4  byte length) : A specific "flag" for the Error Record. Flags are pre-defined values which provide more information on the Error
# Persistence Info    (108 byte offset, 8  byte length) : Produced and consumed by the creator of the Error Record.There are no guidelines for these bytes.
# Reserved            (116 byte offset, 12 byte length) : Must be zero
class CPER_HEADER(object):

    STRUCT_FORMAT = "=IHIHIIIQ16s16s16s16sQIQ12s"

    def __init__(self, input):
        
        self.ValidBitsList = [False,False,False] # Go to self.ValidBitsParse to see description of the field

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
            
        self.ValidBitsParse()

    ##
    # Signature should be ascii array (0x43,0x50,0x45,0x52) or "CPER"
    ##
    def SignatureParse(self) -> str:
        return self.SignatureStart.decode('utf-8')

    ##
    # Parse the major and minor version number of the Error Record definition
    #
    # TODO: Actually parse out the zeroth and first byte which represent the minor and major version numbers respectively 
    ##
    def RevisionParse(self) -> str:
        return str(self.Revision)

    ##
    # Parse the error severity for 4 known values
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
        if(self.ValidationBits & int('0b1', 2)): # Check bit 0
            self.ValidBitsList[0] = True
        if(self.ValidationBits & int('0b10', 2)): # Check bit 1
            self.ValidBitsList[1] = True
        if(self.ValidationBits & int('0b100', 2)): # Check bit 2
            self.ValidBitsList[2] = True

    ##
    # Convert the timestamp into a friendly version formatted to (MM/DD/YY Hours:Minutes:Seconds)
    ##
    def TimestampParse(self) -> str:
        if(self.ValidBitsList[1]):
            return str(( self.Timestamp >> 40) & int('0b11111111', 2)) + "/" + \
                                     str(( self.Timestamp >> 32) & int('0b11111111', 2)) + "/" + \
                                     str((((self.Timestamp >> 56) & int('0b11111111', 2)) * 100) + ((self.Timestamp >> 48) & int('0b11111111', 2))) + " " + \
                                     str(( self.Timestamp >> 16) & int('0b11111111', 2)) + ":" + \
                                     str(( self.Timestamp >> 8 ) & int('0b11111111', 2)) + ":" + \
                                     str(( self.Timestamp >> 0 ) & int('0b11111111', 2))
        
        return "Invalid"

    ##
    # Parse the Platform GUID (Typically, the Platform SMBIOS UUID)
    ##
    def PlatformIDParse(self) -> str:

        # Only parse if data is valid
        if(self.ValidBitsList[0]):
            return AttemptGuidParse(self.PlatformID)

        # Platform ID is invalid based on validation bits
        return "Invalid"

    ##
    # Parse the GUID for the Software Partition (if applicable)
    ##
    def PartitionIDParse(self) -> str:

        # Only parse if data is valid
        if(self.ValidBitsList[2]):
            return AttemptGuidParse(self.PartitionID)
        
        # Partition ID is invalid based on validation bits
        return "Invalid"

    ##
    # Parse the GUID for the GUID of the Error "Creator"
    ##
    def CreatorIDParse(self) -> str:
        return AttemptGuidParse(self.CreatorID)

    ##
    # Parse the pre-assigned GUID associated with the event (ex.Boot)
    ##
    def NotificationTypeParse(self) -> str:
        return AttemptGuidParse(self.NotificationType)

    ##
    # When combined with the Creator ID, Record ID identifies the Error Record
    ##
    def RecordIDParse(self) -> str:
        return str(self.RecordID)

    ##
    # Check the flags field and populate list containing applicable flags
    ##
    def FlagsParse(self) -> str:

        FlagList = []

        # Check each bit for associated flag
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

        # If no flags were found
        if(empty(FlagList)):
            return "None"
        
        # Join the FlagsList elements separated by commas
        return ", ".join(FlagList)

    ##
    # Parse the persistence info which is produced and consumed by the creator of the Error Record
    ##
    def PersistenceInfoParse(self) -> str:
        return str(self.PersistenceInfo)

    ##
    # Print relevant portions of the CPER header. Change to suit your needs
    ##
    def PrettyPrint(self) -> str:

        string = ""
        temp = ""

        string = concat_n(string,concat("Record Length:  ",str(self.RecordLength)))

        temp = self.TimestampParse()
        string = concat_n(string,concat("Time of error:  ",temp))

        temp = self.ErrorSeverityParse()
        string = concat_n(string,concat("Error severity: ",temp))

        temp = self.FlagsParse()
        string = concat_n(string,concat("Flags ID:       ",temp))

        temp = self.PlatformIDParse()
        string = concat_n(string,concat("Platform ID:    ",temp))

        temp = self.PartitionIDParse()
        string = concat_n(string,concat("Partition ID:   ",temp))

        temp = self.CreatorIDParse()
        string = concat_n(string,concat("Creator ID:     ",temp))

        return string[0:-1] #omit the last newline

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
class CPER_SECTION_HEADER(object):

    STRUCT_FORMAT = "=IIHccH16s16sH20s"

    def __init__(self, input):

        self.ValidSectionBitsList = [False,False] # Go to self.ValidBitsParse to see description of the field
        self.FlagList = [] # go to self.FlagsParse to se description of this field

        (self.SectionOffset,
            self.SectionLength,
            self.Revision,
            self.ValidationBits,
            self.Reserved,
            self.Flags,
            self.SectionType,
            self.FRUID,
            self.SectionSeverity,
            self.FRUString) = struct.unpack_from(self.STRUCT_FORMAT, input)
        
        self.FlagsParse()
        self.ValidBitsParse()

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
    def ValidBitsParse(self):
        if(ord(self.ValidationBits) & 0b1): # check bit 0
            self.ValidSectionBitsList[0] = True
        if(ord(self.ValidationBits) & 0b10): # check bit 1
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

        if(self.Flags & int('0b1', 2)): # Check bit 0
            FlagList.append("Primary")
        if(self.Flags & int('0b10', 2)): # Check bit 1
            FlagList.append("Containment Warning")
        if(self.Flags & int('0b100', 2)): # Check bit 2
            FlagList.append("Reset")
        if(self.Flags & int('0b1000', 2)): # Check bit 3
            FlagList.append("Error Threshold Exceeded")
        if(self.Flags & int('0b10000', 2)): # Check bit 4
            FlagList.append("Resource Not Accessible")
        if(self.Flags & int('0b100000', 2)): # Check bit 5
            FlagList.append("Latent Error")

        # If no flags were found
        if(empty(FlagList)):
            return "None"
        
        # Join the FlagsList elements separated by commas
        return ' '.join(FlagList)

    ##
    # Parse the Section Type which is a pre-defined GUID indicating that this section is from a particular error
    ##
    def SectionTypeParse(self) -> str:
        return AttemptGuidParse(self.SectionType)

    ##
    # TODO: Fill in - not detailed in CPER doc
    ##
    def FRUIDParse(self) -> str:

        # Only parse if data is valid
        if(self.ValidSectionBitsList[0]):
            return AttemptGuidParse(self.FRUID)

        return "Invalid"
    

    ##
    # Parse the error severity for 4 known values
    #
    # NOTE: A severity of "Informational" indicates that the section contains extra information that 
    #       can be safely ignored
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
        
        return ""

    ##
    # Parse out the custom string identifying the FRU hardware
    ##
    def FRUStringParse(self) -> str:

        # Only parse if data is valid
        if(self.ValidSectionBitsList[1]):

            # Convert the FRU string from bytes to a string
            try:
                return self.FRUString.decode('utf-8')
            except:
                return "Unable to parse"
        
        return "Invalid"

    ##
    # Print relevant portions of the section header. Change to suit your needs
    ##
    def PrettyPrint(self) -> str:
        string = ""
        temp = ""

        string = concat_n(string,concat("Section Length:    ",str(self.SectionLength)))

        temp = self.FlagsParse()
        string = concat_n(string,concat("Flags:             ",temp))

        temp = self.SectionSeverityParse()
        string = concat_n(string,concat("Section Severity:  ",temp))

        temp = self.SectionTypeParse()
        string = concat_n(string,concat("Section Type:      ",temp))

        temp = self.FRUIDParse()
        string = concat_n(string,concat("FRU ID:            ",temp))
        
        temp = self.FRUStringParse()
        string = concat_n(string,concat("FRU String:        ",temp))
        
        return string

##
# Dumps byte code of input
##
def HexDump(input, bytesperline):

    string      = "" # Stores the entire hexdump string
    asc         = "" # Stores the ascii version of the current hexdump line
    byte        = "" # Stores the base 16 byte version of the current hexdump line
    rangecheck  = lambda x : x < 31 or x > 127 # Used to check if a byte value is within relevant ascii character bounds

    # Go through every byte from the input
    for i in range(len(input)):

        # Add a byte string version of the byte onto the byte string
        byte = concat_s(byte, format(input[i],'02X'))
        
        # Add an ascii version of the byte onto the ascii string
        if rangecheck(input[i]):
                asc = concat_s(asc,". ")
        else:
            asc = concat_s(asc,format(chr(input[i])," <2"))
        
        # Once we've reached bytesperline length, concatenate asc and byte strings and start a new line
        if(not (i + 1) % bytesperline):
            string = concat_n(string,concat(byte,asc))
            asc = ""
            byte = ""
    
    # Check if there are any remaining characters in the asc and byte strings to be added to string 
    if(len(input) % bytesperline):  
        string = concat(string,concat_n(concat(byte,"   " * (bytesperline - (len(byte)//3))),concat(asc,"   " * (bytesperline - (len(asc)//3)))))

    return string

##
# Load friendly names from friendlynames.csv to FriendlyNames dict
##
def ImportFriendlyNames():
    # open friendlynames.csv
    with open('friendlynames.csv','r') as csv_file:

        rowcounter = 2 # Used to track which row we are reading
        csv_reader = csv.reader(csv_file, delimiter=',') # Read the csv file
        next(csv_reader) # Skip the header

        for row in csv_reader:
            try:
                # Input friendly name into dict
                FriendlyNames[uuid.UUID(row[1].strip())] = row[0]
            except:
                # Alert user if a row could not be parsed
                print("Unable to add row " + str(rowcounter) + " to the friendly name dictionary!")
            
            rowcounter += 1

##
# Load all plugins from the /plugins folder
##
def LoadPlugins():
    # Get all subclasses of SECTION_PARSER_PLUGIN which have been imported 
    # using the "from plugins import *" call at start of file
    subclasslist = SECTION_PARSER_PLUGIN.__subclasses__()
    
    for cl in subclasslist:
        Parsers.append(cl())

##
# Attempt to parse a guid. If that fails, notify user, otherwisesee if it has an associated 
# friendly name. Just return the guid if no friendly name can be found.
##
def AttemptGuidParse(g) -> str:
        try:
            guid = uuid.UUID(bytes_le=g)
        except:
            return "Unable to parse"

        # Check the friendlynames list (loaded from the friendlynames.csv file) for this guid
        if(FriendlyNames.get(guid)):
            return FriendlyNames[guid]

        # Return the guid if a friendly name cannot be found
        return str(guid)

##
# Run each plugins CanParse() method to see if it can parse the input guid
##
def CheckPluginsForGuid(guid):

    for p in Parsers:
        # CanParse() returns true if it recognizes the guid
        if p.CanParse(guid):
            return p

    return None

##
# Parse a list of cper record strings
##
def ParseCPERList(input):
    for x in input:
        CPER(x)

##
# Parse a single cper record
##
def ParseCPER(input):
    c = CPER(input)
    c.PrettyPrint()

##
# Parse cper records from event viewer xml file
##
def ParseCPERFromXML(input): # TODO: Create xml parser
    pass

##
# Main function used to test functionality
##
if __name__ == "__main__":
    LoadPlugins()
    ImportFriendlyNames()
    with open('testdata.csv','r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader) # skip the header

        for row in csv_reader:
            ParseCPER(row[0])
