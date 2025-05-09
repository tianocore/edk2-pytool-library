## @file
# UnitTest for device_path.py
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##

import unittest
import base64
from edk2toollib.uefi.device_path import DevicePathFactory


class TestDevicePath(unittest.TestCase):
    """Test the DevicePathFactory class for decoding device paths."""

    def test_device_path_decode_nvme_boot(self):
        """Test decoding a device path for NVMe boot."""
        # Base64-encoded binary data
        base64_data = (
            "AgEMANBBAwoAAAAAAQEGAAAGAQEGAAAAAxcQAAEAAAAAG0RKSNbiDgQBKgABAAAAAAgAAAAAAAAAIAgAAAAAAFq+A2SZ1KhDtWRY8TJI4hoCAgQERgBcAEUARgBJAFwATQBpAGMA"
            "cgBvAHMAbwBmAHQAXABCAG8AbwB0AFwAYgBvAG8AdABtAGcAZgB3AC4AZQBmAGkAAAB//wQA"
        )

        # Decode the base64 string into binary data
        binary_data = base64.b64decode(base64_data)

        # Parse the binary data into a list of device path objects
        device_paths = DevicePathFactory.from_binary(binary_data)

        # Expected structure
        expected_structure = [
            {
                "ACPI / ACPI HID": {
                    "Header": {"type": "ACPI", "subtype": "ACPI HID", "length": 12},
                    "HID": "A0341D0",
                    "UID": "0",
                }
            },
            {
                "Hardware / PCI": {
                    "Header": {"type": "Hardware", "subtype": "PCI", "length": 6},
                    "Function": 0,
                    "Device": 6,
                }
            },
            {
                "Hardware / PCI": {
                    "Header": {"type": "Hardware", "subtype": "PCI", "length": 6},
                    "Function": 0,
                    "Device": 0,
                }
            },
            {
                "Messaging / NVMe Namespace": {
                    "Header": {"type": "Messaging", "subtype": "NVMe Namespace", "length": 16},
                    "NamespaceIdType": 1,
                    "NamespaceId": "000000001B444A48D6E20E",
                    "SubsystemNqn": "",
                }
            },
            {
                "Media / Hard Drive": {
                    "Header": {"type": "Media", "subtype": "Hard Drive", "length": 42},
                    "PartitionNumber": 1,
                    "PartitionStart": 2048,
                    "PartitionSize": 532480,
                    "Signature": "5ABE036499D4A843B56458F13248E21A",
                    "MBRType": 2,
                    "SignatureType": 2,
                }
            },
            {
                "Media / File Path": {
                    "Header": {"type": "Media", "subtype": "File Path", "length": 70},
                    "PathName": "\\EFI\\Microsoft\\Boot\\bootmgfw.efi",
                }
            },
            {
                "type": "End of Hardware",
                "subtype": "End of Hardware",
                "length": 4,
            },
        ]

        # Convert the parsed device paths to their dictionary representations
        decoded_structure = [dp.__dict__() for dp in device_paths]

        # Assert that the decoded structure matches the expected structure
        self.assertEqual(decoded_structure, expected_structure)

    def test_device_path_decode_piwg_firmware(self):
        """Test decoding a device path for PIWG firmware. Embedded applications in the firmware volume."""
        # Base64-encoded binary data
        base64_data = "BAcUALAIEGPRsgpBi0ksXE2OzH4EBhQAcQBnUI9H50utE4dU83nGL3//BAA="

        # Decode the base64 string into binary data
        binary_data = base64.b64decode(base64_data)

        # Parse the binary data into a list of device path objects
        device_paths = DevicePathFactory.from_binary(binary_data)

        # Expected structure
        expected_structure = [
            {
                "Media / PIWG Firmware Volume": {
                    "Header": {"type": "Media", "subtype": "PIWG Firmware Volume", "length": 20},
                    "FvName": "631008B0-B2D1-410A-8B49-2C5C4D8ECC7E",
                }
            },
            {
                "Media / PIWG Firmware File": {
                    "Header": {"type": "Media", "subtype": "PIWG Firmware File", "length": 20},
                    "FvFileName": "50670071-478F-4BE7-AD13-8754F379C62F",
                }
            },
            {
                "type": "End of Hardware",
                "subtype": "End of Hardware",
                "length": 4,
            },
        ]

        # Convert the parsed device paths to their dictionary representations
        decoded_structure = [dp.__dict__() for dp in device_paths]

        # Assert that the decoded structure matches the expected structure
        self.assertEqual(decoded_structure, expected_structure)

    def test_device_path_decode_relative_offset_range(self):
        """Test decoding a device path with a relative offset range. These are option roms that are not in the firmware volume."""
        # Base64-encoded binary data
        base64_data = "AgEMANBBAwoAAAAAAQEGAAEBAQEGAAAABAgYAAAAAABQ/AAAAAAAAP9LAgAAAAAAf/8EAA=="

        # Decode the base64 string into binary data
        binary_data = base64.b64decode(base64_data)

        # Parse the binary data into a list of device path objects
        device_paths = DevicePathFactory.from_binary(binary_data)

        # Expected structure
        expected_structure = [
            {
                "ACPI / ACPI HID": {
                    "Header": {"type": "ACPI", "subtype": "ACPI HID", "length": 12},
                    "HID": "A0341D0",
                    "UID": "0",
                }
            },
            {
                "Hardware / PCI": {
                    "Header": {"type": "Hardware", "subtype": "PCI", "length": 6},
                    "Function": 1,
                    "Device": 1,
                }
            },
            {
                "Hardware / PCI": {
                    "Header": {"type": "Hardware", "subtype": "PCI", "length": 6},
                    "Function": 0,
                    "Device": 0,
                }
            },
            {
                "Media / Relative Offset Range": {
                    "Header": {"type": "Media", "subtype": "Relative Offset Range", "length": 24},
                    "Reserved": 0,
                    "StartingOffset": 64592,
                    "EndingOffset": 150527,
                }
            },
            {
                "type": "End of Hardware",
                "subtype": "End of Hardware",
                "length": 4,
            },
        ]

        # Convert the parsed device paths to their dictionary representations
        decoded_structure = [dp.__dict__() for dp in device_paths]

        # Assert that the decoded structure matches the expected structure
        self.assertEqual(decoded_structure, expected_structure)

    def test_device_path_decode_usb_ipv4(self):
        """Test decoding a device path with USB and IPv4 messaging."""
        # Base64-encoded binary data
        base64_data = "AgEMANBBAwoAAAAAAQEGAAANAwUGAAMAAwUGAAMAAwUGAAMAAwslAHD4rrFIqgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMMGwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAH//BAA="

        # Decode the base64 string into binary data
        binary_data = base64.b64decode(base64_data)

        # Parse the binary data into a list of device path objects
        device_paths = DevicePathFactory.from_binary(binary_data)

        # Expected structure
        expected_structure = [
            {
                "ACPI / ACPI HID": {
                    "Header": {"type": "ACPI", "subtype": "ACPI HID", "length": 12},
                    "HID": "A0341D0",
                    "UID": "0",
                }
            },
            {
                "Hardware / PCI": {
                    "Header": {"type": "Hardware", "subtype": "PCI", "length": 6},
                    "Function": 0,
                    "Device": 13,
                }
            },
            {
                "Messaging / USB": {
                    "Header": {"type": "Messaging", "subtype": "USB", "length": 6},
                    "ParentPortNumber": 3,
                    "InterfaceNumber": 0,
                }
            },
            {
                "Messaging / USB": {
                    "Header": {"type": "Messaging", "subtype": "USB", "length": 6},
                    "ParentPortNumber": 3,
                    "InterfaceNumber": 0,
                }
            },
            {
                "Messaging / USB": {
                    "Header": {"type": "Messaging", "subtype": "USB", "length": 6},
                    "ParentPortNumber": 3,
                    "InterfaceNumber": 0,
                }
            },
            {
                "Messaging / MAC Address": {
                    "Header": {"type": "Messaging", "subtype": "MAC Address", "length": 37},
                    "MacAddress": {
                        "Addr": "70:F8:AE:B1:48:AA:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00"
                    },
                    "IfType": (0,),
                }
            },
            {
                "Messaging / IPv4": {
                    "Header": {"type": "Messaging", "subtype": "IPv4", "length": 27},
                    "LocalIpAddress": "0.0.0.0",
                    "RemoteIpAddress": "0.0.0.0",
                    "LocalPort": 0,
                    "RemotePort": 0,
                    "Protocol": 0,
                    "StaticIpAddress": True,
                    "GatewayIpAddress": "0.0.0.0",
                    "SubnetMask": "0.0.0.0",
                }
            },
            {
                "type": "End of Hardware",
                "subtype": "End of Hardware",
                "length": 4,
            },
        ]

        # Convert the parsed device paths to their dictionary representations
        self.maxDiff = None
        decoded_structure = [dp.__dict__() for dp in device_paths]

        # Assert that the decoded structure matches the expected structure
        self.assertEqual(decoded_structure, expected_structure)


if __name__ == "__main__":
    unittest.main()
