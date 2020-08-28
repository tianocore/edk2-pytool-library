# @file mu_plugin.py
# Parser for MU telemetry
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import sys
import uuid
import struct
from edk2toollib.uefi.telem.cper_section_data import SECTION_PARSER_PLUGIN

"""
A MU Telemetry section has the following structure:
# TODO : FILL IN
Library IDD             (0  byte offset, 16  byte length) : 
IHV Sharing Guid        (16 byte offset, 16  byte length) : 
Additional Info 1       (32 byte offset, 64  byte length) : 
Additional Info 2       (96 byte offset, 64  byte length) : 
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

class MU_SECTION_DATA_PARSER(SECTION_PARSER_PLUGIN):

    STRUCT_FORMAT = "=16s16s64s64s"
    STRUCT_SIZE = 160

    def __init__(self):
        self.LibraryID = None
        self.IhvSharingGuid = None
        self.AdditionalInfo1 = None
        self.AdditionalInfo2 = None
        self.MuTelemGuid = uuid.UUID(bytes=bytes(16)) # TODO: Fill in with real mu telemetry guid

    def __str__(self) -> str:
        return "MU PARSER"

    def CanParse(self,guid:uuid) -> bool:
        if guid == self.MuTelemGuid:
            return True
        
        return False 

    def Parse(self,data:str) -> str:
        if(len(data) < self.STRUCT_SIZE):
            print("Data passed to " + self.__str__() + " was smaller than the minimum size. Minimum size: " + str(self.STRUCT_SIZE) + " size of input: " + str(len(data)))
            return
            
        (self.LibraryID,
         self.IhvSharingGuid,
         self.AdditionalInfo1,
         self.AdditionalInfo2) = struct.unpack_from(self.STRUCT_FORMAT, data)

        # TODO: Fill in actual parse code for mu section - consult Kun or read source code