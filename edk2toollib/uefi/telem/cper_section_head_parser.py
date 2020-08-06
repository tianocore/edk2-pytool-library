# @file cper_section_parser.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct
import uuid

"""
A Section Header within a CPER has the following structure

Section Offset      (0  byte offset, 4  byte length) : Offset from start of the CPER(not the start of the section) to the beginning of the section body
Section Length      (4  byte offset, 4  byte length) : Length in bytes of the section body
Revision            (8  byte offset, 2  byte length) : Represents the major and minor version number of the Error Record definition
Validation Bits     (10 byte offset, 1  byte length) : Indicates the validity of the FRU ID and FRU String fields
Reserved            (11 byte offset, 1  byte length) : Must be zero
Flags               (12 byte offset, 4  byte length) : Contains info describing the Error Record TODO: More info here
Section Type        (16 byte offset, 16 byte length) : Holds a pre-defined GUID value indicating that this section is from a particular error.
FRU ID              (32 byte offset, 16 byte length) : ? Not detailed in the CPER doc
Section Severity    (48 byte offset, 4  byte length) : Value from 0 - 3 indicating the severity of the error
FRU String          (52 byte offset, 20 byte length) : String identifying the FRU hardware
"""

"""
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


class CPER_SECTION_HEAD(object):

    STRUCT_FORMAT = "=IIH1s1sH16sH20s"

    def __init__(self, cper_section_byte_array):
        (self.SectionOffset,
            self.SectionLength,
            self.Revision,
            self.ValidationBits,
            self.Reserved,
            self.Flags,
            self.SectionType,
            self.SectionSeverity,
            self.FRUString) = struct.unpack_from(self.STRUCT_FORMAT, cper_section_byte_array)

        self.ValidBitsList = [False,False]
        self.FlagList = []

        print("In section parsing. Section Length: " + str(self.SectionLength) + " Section Offset: " + str(self.SectionOffset))

    ##
    #
    ##
    def RevisionParse(self):
        return self.Revision

    ##
    # if bit 1: FruID contains valid info
    # if bit 2: FruID String contains valid info
    ##
    def ValidationBitsParse(self):
        if(self.ValidationBits & int('0b1', 2)):
            self.ValidBitsList[0] = True
        if(self.ValidationBits & int('0b10', 2)):
            self.ValidBitsList[1] = True

    ##
    # Check the flags field and populate list containing applicable flags
    ##
    def FlagsParse(self):

        if(self.Flags & int('0b1', 2)):
            self.FlagList += "Primary"
        if(self.Flags & int('0b10', 2)):
            self.FlagList += "Containment Warning"
        if(self.Flags & int('0b100', 2)):
            self.FlagList += "Reset"
        if(self.Flags & int('0b1000', 2)):
            self.FlagList += "Error Threshold Exceeded"
        if(self.Flags & int('0b10000', 2)):
            self.FlagList += "Resource Not Accessible"
        if(self.Flags & int('0b100000', 2)):
            self.FlagList += "Latent Error"

    ##
    #
    ##
    def SectionTypeParse(self):
        try:
            guid = uuid.UUID(bytes=self.SectionType)
            return guid.bytes_le()
        except:
            return self.SectionType

    ##
    #
    ##
    def FRUIDParse(self):
        if(self.ValidationBits[0]):
            try:
                guid = uuid.UUID(bytes=self.SectionType)
                return guid.bytes_le()
            except:
                pass

        return self.SectionType

    ##
    # Parse the severity of the error in this section
    #
    # Note that severity of "Informational" indicates that the section contains extra information that can be safely ignored by error handling software.
    ##
    def SectionSeverityParse(self):
        if(self.SectionSeverity == 0):
            return "Recoverable"
        elif(self.SectionSeverity == 1):
            return "Fatal"
        elif(self.SectionSeverity == 2):
            return "Corrected"
        elif(self.SectionSeverity == 3):
            return "Informational"

    ##
    #
    ##
    def FRUStringParse(self):
        if(self.ValidBitsList[1]):
            return self.FRUString
        else:
            return "none"