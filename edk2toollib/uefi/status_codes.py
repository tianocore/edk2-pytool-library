# @file
# Code to help convert an Int to StatusCode string
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""Module for converting an Int to StatusCode string."""


class UefiStatusCode(object):
    """Object representing a UEFI Status Code from Appendix D of the UEFI spec."""

    # high bit set
    ErrorCodeStrings = ["NOT VALID", "Load Error", "Invalid Parameter", "Unsupported", "Bad BufferSize",
                        "Buffer Too Small", "Not Ready", "Device Error", "Write Protected", "Out of Resources",
                        "Volume Corrupt", "Volume Full", "No Media", "Media Changed", "Not Found", "Access Denied",
                        "No Response", "No Mapping", "Time Out", "Not Started", "Already Started", "Aborted",
                        "ICMP Error", "TFTP Error", "Protocol Error", "Incompatible Error", "Security Violation",
                        "CRC Error", "End of Media", "Reserved(29)", "Reserved(30)", "End of File",
                        "Invalid Language", "Compromised Data", "IP Address Conflict", "HTTP Error"]

    NonErrorCodeStrings = ["Success", "Unknown Glyph", "Delete Failure", "Write Failure", "Buffer Too Small",
                           "Stale Data", "File System", "Reset Required"]

    def Convert32BitToString(self, value: int) -> str:
        """Convert 32 bit int to a friendly UEFI status code string value."""
        StatusStrings = UefiStatusCode.NonErrorCodeStrings

        if (value >> 31) & 1 == 1:
            # error
            StatusStrings = UefiStatusCode.ErrorCodeStrings
            value = value & 0x7FFFFFFF  # mask off upper bit

        if (value >= len(StatusStrings)):
            return "Undefined StatusCode"

        return StatusStrings[value]

    def Convert64BitToString(self, value: int) -> str:
        """Convert 64 bit int to a friendly UEFI status code string value."""
        StatusStrings = UefiStatusCode.NonErrorCodeStrings

        if (value >> 63) & 1 == 1:
            # error
            StatusStrings = UefiStatusCode.ErrorCodeStrings
            value = value & 0x7FFFFFFFFFFFFFFF  # mask off upper bit

        if (value >= len(StatusStrings)):
            return "Undefined StatusCode"

        return StatusStrings[value]

    def ConvertHexString64ToString(self, hexstring: str) -> str:
        """Convert 64 bit hexstring in 0x format to a UEFI status code."""
        value = int(hexstring, 16)
        return self.Convert64BitToString(value)

    def ConvertHexString32ToString(self, hexstring: str) -> str:
        """Convert 32 bit hexstring in 0x format to a UEFI status code."""
        value = int(hexstring, 16)
        return self.Convert32BitToString(value)
