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

class CPER_SECTION(object):

    STRUCT_FORMAT = "=IIH1s1sH16sH20s"

    def __init__(self, cper_section_byte_array):
        (self.SectionOffset,
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
    def Section_Offset_Parse(self, x):
        return x

    ##
    #
    ##
    def Section_Length_Parse(self, x):
        return x

    ##
    #
    ##
    def Revision_Parse(self, x):
        return x

    ##
    #
    ##
    def Section_Valid_Mask_Parse(self, x):
        return x

    ##
    #
    ##
    def Flags_Parse(self, x):
        return x

    ##
    #
    ##
    def Section_Type_Parse(self, x):
        return x

    ##
    #
    ##
    def Section_Severity_Parse(self, x):
        return x

    ##
    #
    ##
    def FRU_String_Parse(self, x):
        return x
