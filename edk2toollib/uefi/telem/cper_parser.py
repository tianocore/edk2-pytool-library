# @file cper_parser.py
# CPER object
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import struct
import uuid
import csv
import sys
from cper_head_parser import *
from cper_section_head_parser import *
from plugin_setup import PLUGIN_SETUP

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
"""

class CPER(object):

    CPER_HEADER_SIZE = 128
    CPER_SECTION_HEADER_SIZE = 72

    def __init__(self, input):
        self.RawData = bytearray.fromhex(input)
        self.Header = 1
        self.Sections = []
        self.SetCPERHeader()
        self.Header.PartitionIDParse()
        self.SetSectionHeaders()
        self.parsers = PLUGIN_SETUP()
        self.parsers.CheckPluginsForGuid(1)

    ##
    # Turn the portion of the raw input associated with the CPER head into a CPER_HEAD object
    ##
    def SetCPERHeader(self):
        temp = self.RawData[:self.CPER_HEADER_SIZE]
        self.Header = CPER_HEAD(temp)

    ##
    # Set each of the section headers to CPER_SECTION_HEADER objects
    ##
    def SetSectionHeaders(self):
        try:
            temp = self.RawData[self.CPER_HEADER_SIZE:self.CPER_HEADER_SIZE + (self.CPER_SECTION_HEADER_SIZE * self.Header.SectionCount)]
            for x in range(self.Header.SectionCount):
                #print("going from " + str(x * self.CPER_SECTION_HEADER_SIZE) + " to " + str(((x + 1) * self.CPER_SECTION_HEADER_SIZE) - 1))
                self.Sections.append(CPER_SECTION_HEAD(temp[x * self.CPER_SECTION_HEADER_SIZE: (x + 1) * self.CPER_SECTION_HEADER_SIZE]))
        except:
            pass
    
    ##
    # Get each of the actual section data pieces and either pass it to something which can parse it, or dump the hex
    ##
    def SetSectionData(self):
        x = 1
        return x

if __name__ == "__main__":
    with open('HeadersData.csv','r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        next(csv_reader) # skip the header
        for row in csv_reader:
            x = CPER(row[0])
            break # to parse just one cper for testing
