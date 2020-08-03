# @file cper_section_parser.py
# Code to help parse cper header
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct

"""
A Section Header within a CPER has the following structure

Section Offset      (4  bytes) : Offset from start of the CPER (not the start of the section)
                                 to the beginning of the section body
Section Length      (4  bytes) : Length in bytes of the section body
Revision            (2  bytes) : Represents the major and minor version number of the Error Record
                                 definition
Validation Bits     (1  byte ) : Indicates the validity of the FRU ID and FRU String fields
Reserved            (1  byte ) : Must be zero
Flags               (12 bytes) : Contains info describing the Error Record TODO: More info here
Section Type        (16 bytes) : Holds a pre-defined GUID value indicating that this section is from a 
                                 particular error.
Section Severity    (4  bytes) : Value from 0 - 3 indicating the severity of the error
FRU String          (20 bytes) : String identifying the FRU hardware
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


    ##
    #
    ##
    def Section_Offset_Parse(self):
        return self.SectionOffset

    ##
    #
    ##
    def Section_Length_Parse(self):
        return self.SectionLength

    ##
    #
    ##
    def Revision_Parse(self):
        return self.Revision

    ##
    #
    ##
    def Validation_Bits_Parse(self):
        return self.ValidationBits

    ##
    #
    ##
    def Flags_Parse(self):
        return self.Flags

    ##
    #
    ##
    def Section_Type_Parse(self):
        return self.SectionType

    ##
    #
    ##
    def Section_Severity_Parse(self):
        return self.SectionSeverity

    ##
    #
    ##
    def FRU_String_Parse(self):
        return self.FRUString
