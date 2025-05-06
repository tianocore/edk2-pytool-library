# @file
# Python implementation of UEFI Device Paths
#
# Copyright (c) Microsoft Corporation
#
# SPDX-License-Identifier: BSD-2-Clause-Patent
##
"""This is a python implementation of the UEFI Specification Device Paths

C Implementations may be found here:
https://github.com/tianocore/edk2/blob/00ccd99d46068c87e73e8e521afea09e19419885/MdePkg/Include/Protocol/DevicePath.h

"""

from uuid import UUID
from edk2toollib.uefi.uefi_types import UINT8
from typing import List

from collections import defaultdict
from dataclasses import dataclass

import struct
import json
import base64

# GUIDs
EFI_DEVICE_PATH_PROTOCOL_GUID = UUID("{09576e91-6d3f-11d2-8e39-00a0c969723b}")
DEVICE_PATH_PROTOCOL = EFI_DEVICE_PATH_PROTOCOL_GUID

# Device Path Types
# These represent the type of device path and the subtype of the device path.
# Visit the C implementation for more details

# Hardware Device Path
HARDWARE_DEVICE_PATH = 0x01

# Subtypes
HW_PCI_DP = 0x01
HW_PCCARD_DP = 0x02
HW_MEMMAP_DP = 0x03
HW_VENDOR_DP = 0x04
HW_CONTROLLER_DP = 0x05
HW_BMC_DP = 0x06

# ACPI Device Path
ACPI_DEVICE_PATH = 0x02

# Subtypes
ACPI_DP = 0x01
ACPI_EXTENDED_DP = 0x02

# Messaging Device Path
MESSAGING_DEVICE_PATH = 0x03

# Subtypes
MSG_ATAPI_DP = 0x01
MSG_SCSI_DP = 0x02
MSG_FIBRECHANNEL_DP = 0x03
MSG_1394_DP = 0x04
MSG_USB_DP = 0x05
MSG_I2O_DP = 0x06
MSG_SAS_DP = 0x07
MSG_SAS_EX_DP = 0x08
MSG_INFINIBAND_DP = 0x09
MSG_VENDOR_DP = 0x0A
MSG_MAC_ADDR_DP = 0x0B
MSG_IPV4_DP = 0x0C
MSG_IPV6_DP = 0x0D
MSG_UART_DP = 0x0E
MSG_USB_CLASS_DP = 0x0F
MSG_USB_WWID_DP = 0x10
MSG_DEVICE_LOGICAL_UNIT_DP = 0x11
MSG_SATA_DP = 0x12
MSG_ISCSI_DP = 0x13
MSG_VLAN_DP = 0x14
MSG_FIBRECHANNELEX_DP = 0x15
MSG_SASEX_DP = 0x16
MSG_NVME_NAMESPACE_DP = 0x17
MSG_URI_DP = 0x18
MSG_UFS_DP = 0x19
MSG_SD_DP = 0x1A
MSG_EMMC_DP = 0x1B
MSG_BLUEFIELD_DP = 0x1C
MSG_BLUETOOTH_DP = 0x1D
MSG_WIFI_DP = 0x1E
MSG_EFI_DP = 0x1F

# Media Device Path
MEDIA_DEVICE_PATH = 0x04

# Subtypes
MEDIA_HARDDRIVE_DP = 0x01
MEDIA_CDROM_DP = 0x02
MEDIA_VENDOR_DP = 0x03
MEDIA_FILEPATH_DP = 0x04
MEDIA_PROTOCOL_DP = 0x05
MEDIA_PIWG_FW_FILE_DP = 0x06

# BIOS Boot Specification Device Path
BIOS_BOOT_SPECIFICATION_DEVICE_PATH = 0x05

# Subtypes
BBS_BBS_DP = 0x01

# End of Hardware Device Path
END_OF_HARDWARE_DEVICE_PATH = 0x7F

NOT_FOUND = 255


def _helper_get_device_path_type(type, subtype) -> tuple[str, str]:
    """Helper function to get the device path type and subtype.

    Args:
        type (int): The device path type.
        subtype (int): The device path subtype.

    Returns:
        tuple[str, str]: A tuple containing the device path type and subtype.
    """
    device_path_type = DEVICE_PATH_TYPES[type]
    device_path_subtype = DEVICE_PATH_SUBTYPES[type][subtype][0]

    return (device_path_type, device_path_subtype)


@dataclass
class DevicePathHeader(object):
    """
    DevicePathHeader class represents the header of a device path in UEFI.

    Attributes:
        dev_type (int): The type of the device path.
        dev_subtype (int): The subtype of the device path.
        dev_length (int): The length of the device path.
        dev_data (bytes): The data associated with the device path.
    """

    dev_type: UINT8
    dev_subtype: UINT8
    dev_length: int
    dev_data: bytes


class EfiDevicePathProtocol(object):
    """
    Represents the EFI Device Path Protocol, which is used to describe the location of a device in the system.

    Attributes:
        dev_type (int): The type of the device path.
        dev_subtype (int): The subtype of the device path.
        dev_length (int): The length of the device path.
        dev_data (bytes): The data associated with the device path.
    """

    _dp_struct_format = "<BBh"
    _dp_struct_size = struct.calcsize(_dp_struct_format)

    def __init__(self, header: DevicePathHeader):
        """
        Initializes a DevicePath object with the given header.
        Args:
            header (DevicePathHeader): The header containing device path information.
        """

        self.dev_type = header.dev_type
        self.dev_subtype = header.dev_subtype
        self.dev_length = header.dev_length
        self.dev_data = header.dev_data

    def __str__(self):
        return json.dumps(self.__dict__(), indent=2)

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {"type": device_type, "subtype": device_subtype, "length": self.dev_length}

    @staticmethod
    def decode(binary) -> "DevicePathHeader":
        """
        Decodes a binary representation of an EFI device path.

        Args:
            binary (bytes): The binary data representing the EFI device path.

        Returns:
            DevicePathHeader: An object containing the type, subtype, length, and data of the device path.
        """

        type, subtype, length = struct.unpack(
            EfiDevicePathProtocol._dp_struct_format, binary[: EfiDevicePathProtocol._dp_struct_size]
        )
        length_tuple = (length & 0xFF, (length >> 8) & 0xFF)
        data_length = int.from_bytes(length_tuple, "little")
        data = binary[EfiDevicePathProtocol._dp_struct_size : data_length]

        return DevicePathHeader(type, subtype, data_length, data)


class UnimplementedDevicePath(EfiDevicePathProtocol):
    """
    UnimplementedDevicePath class represents a device path node that is not implemented.
    This class inherits from EfiDevicePathProtocol and provides a way to handle
    unimplemented device path nodes by storing the header and providing a dictionary
    representation of the device path type and subtype.

    Attributes:
        header (DevicePathHeader): The header of the device path node.
    """

    def __init__(self, header: DevicePathHeader):
        """
        Initializes the UnimplementedDevicePath instance with the given header.

        Args:
            header (DevicePathHeader): The header containing device path information.
        """
        super().__init__(header)

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "data": base64.b64encode(self.dev_data).decode("utf-8"),
            }
        }

    @classmethod
    def from_binary(cls, header: DevicePathHeader) -> "UnimplementedDevicePath":
        """
        Creates an UnimplementedDevicePath instance from a binary representation.

        Args:
            header (DevicePathHeader): The header containing device path information.

        Returns:
            UnimplementedDevicePath: An instance of UnimplementedDevicePath.
        """

        return cls(header)


############################################################################################################
# Start Implementation of Device Paths
############################################################################################################


class PciDevicePath(EfiDevicePathProtocol):
    """
    Represents a PCI Device Path in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        header (EfiDevicePathProtocol): The header of the device path.
        function (int): The function number of the PCI device.
        device (int): The device number of the PCI device.
    """

    def __init__(self, header, function, device):
        """
        Initializes the PciDevicePath instance with the given header, function, and device.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.
            function (int): The function number of the PCI device.
            device (int): The device number of the PCI device.
        """
        super().__init__(header)
        self.function = function
        self.device = device

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "Function": self.function,
                "Device": self.device,
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "PciDevicePath":
        function, device = struct.unpack("<BB", header.dev_data[:2])
        return cls(header, function, device)


class PccardDevicePath(EfiDevicePathProtocol):
    """
    Represents a PC Card device path in the UEFI environment.

    Attributes:
        function_number (UINT8): The function number of the PC Card device.
    """

    def __init__(self, header: DevicePathHeader, function_number: UINT8):
        """
        Initializes the PccardDevicePath instance with the given header and function number.

            Args:
                header (DevicePathHeader): The header containing device path information.
                function_number (UINT8): The function number of the PC Card device.
        """
        super().__init__(header)
        self.function_number = function_number

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {"Header": super().__dict__(), "FunctionNumber": self.function_number}
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "PccardDevicePath":
        function_number = struct.unpack("<B", header.data[:1])[0]
        return cls(header, function_number)


class AcpiHidDevicePath(EfiDevicePathProtocol):
    """
    Represents an ACPI HID Device Path in the UEFI device path protocol.

    Attributes:
        header (EfiDevicePathProtocol): The EFI device path protocol header.
        hid (int): Device's PnP hardware ID stored in a numeric 32-bit compressed EISA-type ID.
                   This value must match the corresponding _HID in the ACPI name space.
        uid (int): Unique ID required by ACPI if two devices have the same _HID. This value must
                   also match the corresponding _UID/_HID pair in the ACPI name space. Only the
                   32-bit numeric value type of _UID is supported.
    """

    def __init__(self, header: EfiDevicePathProtocol, hid, uid):
        """
        Initializes the AcpiHidDevicePath instance with the given header, HID, and UID.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.
            hid (int): Device's PnP hardware ID stored in a numeric 32-bit compressed EISA-type ID.
            uid (int): Unique ID required by ACPI if two devices have the same _HID.
        """
        super().__init__(header)
        self.hid = hid
        self.uid = uid

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "HID": f"{self.hid:x}".upper(),
                "UID": f"{self.uid:x}".upper(),
            }
        }

    @classmethod
    def from_binary(cls, header: EfiDevicePathProtocol) -> "AcpiHidDevicePath":
        hid, uid = struct.unpack("<II", header.dev_data[:8])
        return cls(header, hid, uid)


class UsbDevicePath(EfiDevicePathProtocol):
    """
    Represents a USB Device Path in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        header (EfiDevicePathProtocol): The header of the device path.
        parent_port_number (int): The USB Parent Port Number.
        interface_number (int): The USB Interface Number.
    """

    def __init__(self, header, parent_port_number, interface_number):
        """
        Initializes the UsbDevicePath instance with the given header, parent port number, and interface number.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.
            parent_port_number (int): The USB Parent Port Number.
            interface_number (int): The USB Interface Number.
        """
        super().__init__(header)
        self.parent_port_number = parent_port_number
        self.interface_number = interface_number

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "ParentPortNumber": self.parent_port_number,
                "InterfaceNumber": self.interface_number,
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "UsbDevicePath":
        parent_port_number, interface_number = struct.unpack("BB", header.dev_data[:2])
        return cls(header, parent_port_number, interface_number)


class EfiMacAddress(object):
    """
    Represents a MAC address in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        addr (list): The MAC address for a network interface padded with 0s.
    """

    def __init__(self, addr):
        self.addr = addr

    def __str__(self) -> str:
        return ":".join(f"{byte:02X}" for byte in self.addr)

    def __dict__(self):
        return {"Addr": str(self)}

    @classmethod
    def from_binary(cls, data: bytes) -> "EfiMacAddress":
        addr = list(data[:32])
        return cls(addr)


class MacAddrDevicePath(EfiDevicePathProtocol):
    """
    Represents a MAC Address Device Path in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        header (EfiDevicePathProtocol): The header of the device path.
        mac_address (EfiMacAddress): The MAC address for a network interface padded with 0s.
        if_type (int): The network interface type (i.e., 802.3, FDDI).
    """

    def __init__(self, header, mac_address, if_type):
        super().__init__(header)
        self.mac_address = mac_address
        self.if_type = if_type

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "MacAddress": self.mac_address.__dict__(),
                "IfType": self.if_type,
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "MacAddrDevicePath":
        mac_address = EfiMacAddress.from_binary(header.dev_data[:32])
        if_type = struct.unpack("B", header.dev_data[32:33])
        return cls(header, mac_address, if_type)


class EfiIpv4Address(object):
    """
    Represents an IPv4 address in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        addr (list): The IPv4 address.
    """

    def __init__(self, addr):
        """
        Initializes the EfiIpv4Address instance with the given address.

        Args:
            addr (list): The IPv4 address.
        """
        self.addr = addr

    def __dict__(self):
        return {"Addr": self.addr}

    @classmethod
    def from_binary(cls, data: bytes) -> "EfiIpv4Address":
        addr = list(data[:4])
        return cls(addr)

    def __str__(self):
        return ".".join(str(byte) for byte in self.addr)


class Ipv4DevicePath(EfiDevicePathProtocol):
    """
    Represents an IPv4 Device Path in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        header (EfiDevicePathProtocol): The header of the device path.
        local_ip_address (EfiIpv4Address): The local IPv4 address.
        remote_ip_address (EfiIpv4Address): The remote IPv4 address.
        local_port (int): The local port number.
        remote_port (int): The remote port number.
        protocol (int): The network protocol (i.e., UDP, TCP).
        static_ip_address (bool): Indicates if the source IP address is statically bound.
        gateway_ip_address (EfiIpv4Address): The gateway IP address.
        subnet_mask (EfiIpv4Address): The subnet mask.
    """

    def __init__(
        self,
        header,
        local_ip_address,
        remote_ip_address,
        local_port,
        remote_port,
        protocol,
        static_ip_address,
        gateway_ip_address,
        subnet_mask,
    ):
        """
        Initializes the Ipv4DevicePath instance with the given header, local IP address,
        remote IP address, local port, remote port, protocol, static IP address,
        gateway IP address, and subnet mask.

        Args:
            header (DevicePathHeader): The header containing device path information.
            local_ip_address (EfiIpv4Address): The local IPv4 address.
            remote_ip_address (EfiIpv4Address): The remote IPv4 address.
            local_port (int): The local port number.
            remote_port (int): The remote port number.
            protocol (int): The network protocol (i.e., UDP, TCP).
            static_ip_address (bool): Indicates if the source IP address is statically bound.
            gateway_ip_address (EfiIpv4Address): The gateway IP address.
            subnet_mask (EfiIpv4Address): The subnet mask.
        """
        super().__init__(header)
        self.local_ip_address = local_ip_address
        self.remote_ip_address = remote_ip_address
        self.local_port = local_port
        self.remote_port = remote_port
        self.protocol = protocol
        self.static_ip_address = static_ip_address
        self.gateway_ip_address = gateway_ip_address
        self.subnet_mask = subnet_mask

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "LocalIpAddress": str(self.local_ip_address),
                "RemoteIpAddress": str(self.remote_ip_address),
                "LocalPort": self.local_port,
                "RemotePort": self.remote_port,
                "Protocol": self.protocol,
                "StaticIpAddress": self.static_ip_address,
                "GatewayIpAddress": str(self.gateway_ip_address),
                "SubnetMask": str(self.subnet_mask),
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "Ipv4DevicePath":
        local_ip_address = EfiIpv4Address.from_binary(header.dev_data[:4])
        remote_ip_address = EfiIpv4Address.from_binary(header.dev_data[4:8])
        local_port, remote_port, protocol = struct.unpack("HHH", header.dev_data[8:14])
        static_ip_address = bool(header.dev_data)
        gateway_ip_address = EfiIpv4Address.from_binary(header.dev_data[15:19])
        subnet_mask = EfiIpv4Address.from_binary(header.dev_data[19:23])
        return cls(
            header,
            local_ip_address,
            remote_ip_address,
            local_port,
            remote_port,
            protocol,
            static_ip_address,
            gateway_ip_address,
            subnet_mask,
        )


class SataDevicePath(EfiDevicePathProtocol):
    """
    Represents a SATA Device Path.

    Attributes:
        hba_port_number (int): The HBA port number that facilitates the connection.
        port_multiplier_port_number (int): The port multiplier port number.
        lun (int): Logical Unit Number.
    """

    def __init__(self, header, hba_port_number, port_multiplier_port_number, lun):
        """
        Initializes the SataDevicePath instance with the given header, HBA port number,
        port multiplier port number, and LUN.

        Args:
            header (DevicePathHeader): The header containing device path information.
            hba_port_number (int): The HBA port number that facilitates the connection.
            port_multiplier_port_number (int): The port multiplier port number.
            lun (int): Logical Unit Number.
        """
        super().__init__(header)
        self.hba_port_number = hba_port_number
        self.port_multiplier_port_number = port_multiplier_port_number
        self.lun = lun

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "HBAPortNumber": self.hba_port_number,
                "PortMultiplierPortNumber": self.port_multiplier_port_number,
                "Lun": self.lun,
            }
        }

    @classmethod
    def from_binary(cls, header: EfiDevicePathProtocol) -> "SataDevicePath":
        hba_port_number = int.from_bytes(header.dev_data[:2], "little")
        port_multiplier_port_number = int.from_bytes(header.dev_data[2:4], "little")
        lun = int.from_bytes(header.dev_data[4:6], "little")
        return cls(header, hba_port_number, port_multiplier_port_number, lun)


class NvmeOfNamespaceDevicePath(EfiDevicePathProtocol):
    """
    Represents an NVMe over Fabrics (NVMe-oF) Namespace Device Path.

    Attributes:
        namespace_id_type (int): The type of the namespace identifier.
        namespace_id (bytes): The namespace identifier.
        subsystem_nqn (str): The NVMe Qualified Name (NQN) of the subsystem.
    """

    def __init__(self, header, namespace_id_type, namespace_id, subsystem_nqn):
        """
        Initializes the NvmeOfNamespaceDevicePath instance with the given header, namespace ID type,
        namespace ID, and subsystem NQN.

        Args:
            header (DevicePathHeader): The header containing device path information.
            namespace_id_type (int): The type of the namespace identifier.
            namespace_id (bytes): The namespace identifier.
            subsystem_nqn (str): The NVMe Qualified Name (NQN) of the subsystem.
        """
        super().__init__(header)
        self.namespace_id_type = namespace_id_type
        self.namespace_id = namespace_id
        self.subsystem_nqn = subsystem_nqn

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "NamespaceIdType": self.namespace_id_type,
                "NamespaceId": self.namespace_id.hex().upper(),
                "SubsystemNqn": self.subsystem_nqn,
            }
        }

    @classmethod
    def from_binary(cls, header: EfiDevicePathProtocol) -> "NvmeOfNamespaceDevicePath":
        namespace_id_type = header.dev_data[0]
        namespace_id = header.dev_data[1:17]
        subsystem_nqn = header.dev_data[17:].decode("utf-8").rstrip("\x00")
        return cls(header, namespace_id_type, namespace_id, subsystem_nqn)


class HardDriveDevicePath(EfiDevicePathProtocol):
    """
    Represents a hard drive device path in the UEFI (Unified Extensible Firmware Interface) specification.

    Attributes:
        partition_number (int): The partition number on the hard drive.
        partition_start (int): The starting LBA (Logical Block Addressing) of the partition.
        partition_size (int): The size of the partition in blocks.
        signature (bytes): The unique signature of the partition.
        MBR_type (int): The type of MBR (Master Boot Record).
        signature_type (int): The type of signature used.
    """

    _struct_format = "<IQQ16sBB"
    _struct_size = struct.calcsize(_struct_format)

    def __init__(
        self,
        header: DevicePathHeader,
        partition_number: int,
        partition_start: int,
        partition_size: int,
        signature: bytes,
        MBR_type: int,
        signature_type: int,
    ):
        """
        Initializes the HardDriveDevicePath instance with the given header, partition number,
        partition start, partition size, signature, MBR type, and signature type.

        Args:
            header (DevicePathHeader): The header containing device path information.
            partition_number (int): The partition number on the hard drive.
            partition_start (int): The starting LBA of the partition.
            partition_size (int): The size of the partition in blocks.
            signature (bytes): The unique signature of the partition.
            MBR_type (int): The type of MBR.
            signature_type (int): The type of signature used.
        """

        super().__init__(header)
        self.partition_number = partition_number
        self.partition_start = partition_start
        self.partition_size = partition_size
        self.signature = signature
        self.MBR_type = MBR_type
        self.signature_type = signature_type

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "PartitionNumber": self.partition_number,
                "PartitionStart": self.partition_start,
                "PartitionSize": self.partition_size,
                "Signature": self.signature.hex().upper(),
                "MBRType": self.MBR_type,
                "SignatureType": self.signature_type,
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "HardDriveDevicePath":
        """
        Creates a HardDriveDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.
        """
        partition_number, partition_start, partition_size, signature, mbr_type, signature_type = struct.unpack(
            cls._struct_format, header.dev_data
        )
        return cls(header, partition_number, partition_start, partition_size, signature, mbr_type, signature_type)


class FilepathDevicePath(EfiDevicePathProtocol):
    """
    Represents a file path device path in the UEFI device path protocol.

    Attributes:
        path_name (str): The file path name associated with the device path.
    """

    def __init__(self, header: DevicePathHeader, path_name: str):
        """
        Initializes the FilepathDevicePath instance with the given header and path name.

        Args:
            header (DevicePathHeader): The header containing device path information.
            path_name (str): The file path name associated with the device path.
        """
        super().__init__(header)
        self.path_name = path_name

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {f"{device_type} / {device_subtype}": {"Header": super().__dict__(), "PathName": self.path_name}}

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "FilepathDevicePath":
        """
        Creates a FilepathDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.

        Returns:
            FilepathDevicePath: An instance of FilepathDevicePath.
        """
        # Decode the path name from the binary data
        path_name = header.dev_data.decode("utf-16-le").rstrip("\x00")
        return cls(header, path_name)


class FwVolPathDevicePath(EfiDevicePathProtocol):
    """
    Represents a Media Firmware Volume Path Device Path in the UEFI specification.

    Attributes:
        fv_name (UUID): The firmware volume name.
    """

    def __init__(self, header: DevicePathHeader, fv_name):
        """
        Initializes the FwVolPathDevicePath instance with the given header and firmware volume name.

        Args:
            header (DevicePathHeader): The header containing device path information.
            fv_name (UUID): The firmware volume name.
        """
        super().__init__(header)
        self.fv_name = fv_name

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {"Header": super().__dict__(), "FvName": str(self.fv_name).upper()}
        }

    @classmethod
    def from_binary(cls, header: EfiDevicePathProtocol) -> "FwVolPathDevicePath":
        """
        Creates a FwVolPathDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.

        Returns:
            FwVolPathDevicePath: An instance of FwVolPathDevicePath.
        """
        # Decode the firmware volume name from the binary data
        return cls(header, UUID(bytes_le=header.dev_data[:16]))


MEDIA_PIWG_FW_VOL_DP = 0x07


class MediaFwVolFilePathDevicePath(EfiDevicePathProtocol):
    """
    Represents a Media Firmware Volume File Path Device Path in the UEFI specification.

    Attributes:
        fv_file_name (UUID): The firmware volume file name.
    """

    def __init__(self, header: DevicePathHeader, fv_file_name):
        """
        Initializes the MediaFwVolFilePathDevicePath instance with the given header and firmware volume file name.

        Args:
            header (DevicePathHeader): The header containing device path information.
            fv_file_name (UUID): The firmware volume file name.
        """
        super().__init__(header)
        self.fv_file_name = fv_file_name

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "FvFileName": str(self.fv_file_name).upper(),
            }
        }

    @classmethod
    def from_binary(cls, header: EfiDevicePathProtocol) -> "MediaFwVolFilePathDevicePath":
        """
        Creates a MediaFwVolFilePathDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.

        Returns:
            MediaFwVolFilePathDevicePath: An instance of MediaFwVolFilePathDevicePath.
        """
        # Decode the firmware volume file name from the binary data
        return cls(header, UUID(bytes_le=header.dev_data[:16]))


MEDIA_RELATIVE_OFFSET_RANGE_DP = 0x08


class MediaRelativeOffsetRangeDevicePath(EfiDevicePathProtocol):
    """
    Represents a MEDIA_RELATIVE_OFFSET_RANGE_DEVICE_PATH in the UEFI (Unified Extensible Firmware Interface) environment.

    Attributes:
        header (EfiDevicePathProtocol): The header of the device path.
        reserved (int): Reserved field.
        starting_offset (int): The starting offset.
        ending_offset (int): The ending offset.
    """

    def __init__(self, header, reserved, starting_offset, ending_offset):
        """
        Initializes the MediaRelativeOffsetRangeDevicePath instance with the given header, reserved,
        starting offset, and ending offset.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.
            reserved (int): Reserved field.
            starting_offset (int): The starting offset.
            ending_offset (int): The ending offset.
        """
        super().__init__(header)
        self.reserved = reserved
        self.starting_offset = starting_offset
        self.ending_offset = ending_offset

    def __dict__(self):
        device_type, device_subtype = _helper_get_device_path_type(self.dev_type, self.dev_subtype)
        return {
            f"{device_type} / {device_subtype}": {
                "Header": super().__dict__(),
                "Reserved": self.reserved,
                "StartingOffset": self.starting_offset,
                "EndingOffset": self.ending_offset,
            }
        }

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "MediaRelativeOffsetRangeDevicePath":
        """
        Creates a MediaRelativeOffsetRangeDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathProtocol): The header containing device path information.

        Returns:
            MediaRelativeOffsetRangeDevicePath: An instance of MediaRelativeOffsetRangeDevicePath.
        """
        reserved, starting_offset, ending_offset = struct.unpack("<IQQ", header.dev_data[:20])
        return cls(header, reserved, starting_offset, ending_offset)


class EndOfHardwareDevicePath(EfiDevicePathProtocol):
    """
    EndOfHardwareDevicePath represents the end of a hardware device path in the UEFI specification.

    Attributes:
        header (DevicePathHeader): The header of the device path.
    """

    def __init__(self, header: DevicePathHeader):
        """
        Initializes the EndOfHardwareDevicePath instance with the given header.

        Args:
            header (DevicePathHeader): The header containing device path information.
        """
        super().__init__(header)

    @classmethod
    def from_binary(cls, header: "EfiDevicePathProtocol") -> "EndOfHardwareDevicePath":
        """
        Creates an EndOfHardwareDevicePath instance from a binary representation.

        Args:
            header (EfiDevicePathHeader): The header containing device path information.
        """
        return cls(header)


DEVICE_PATH_TYPES = defaultdict(
    lambda: "NOT FOUND",
    {
        HARDWARE_DEVICE_PATH: "Hardware",
        ACPI_DEVICE_PATH: "ACPI",
        MESSAGING_DEVICE_PATH: "Messaging",
        MEDIA_DEVICE_PATH: "Media",
        BIOS_BOOT_SPECIFICATION_DEVICE_PATH: "BIOS Boot Specification",
        END_OF_HARDWARE_DEVICE_PATH: "End of Hardware",
    },
)

# Map of subtypes
# Change function to DevicePath Implementation to begin decoding.
# __dict__() will be called to add the device path to the parent dictionary
DEVICE_PATH_SUBTYPES = defaultdict(
    lambda: {NOT_FOUND: ("NOT_FOUND!", UnimplementedDevicePath)},
    {
        HARDWARE_DEVICE_PATH: defaultdict(
            lambda: ("Unimplemented!", UnimplementedDevicePath),
            {
                HW_PCI_DP: ("PCI", PciDevicePath),
                HW_PCCARD_DP: ("PCCARD", PccardDevicePath),
                HW_MEMMAP_DP: ("Memory Mapped", UnimplementedDevicePath),
                HW_VENDOR_DP: ("Vendor", UnimplementedDevicePath),
                HW_CONTROLLER_DP: ("Controller", UnimplementedDevicePath),
                HW_BMC_DP: ("BMC", UnimplementedDevicePath),
            },
        ),
        ACPI_DEVICE_PATH: defaultdict(
            lambda: ("Unimplemented!", UnimplementedDevicePath),
            {
                ACPI_DP: ("ACPI HID", AcpiHidDevicePath),
                ACPI_EXTENDED_DP: ("ACPI Extended HID", UnimplementedDevicePath),
            },
        ),
        MESSAGING_DEVICE_PATH: defaultdict(
            lambda: ("Unimplemented!", UnimplementedDevicePath),
            {
                MSG_ATAPI_DP: ("ATAPI", UnimplementedDevicePath),
                MSG_SCSI_DP: ("SCSI", UnimplementedDevicePath),
                MSG_FIBRECHANNEL_DP: ("Fibre Channel", UnimplementedDevicePath),
                MSG_1394_DP: ("1394", UnimplementedDevicePath),
                MSG_USB_DP: ("USB", UsbDevicePath),
                MSG_I2O_DP: ("I2O", UnimplementedDevicePath),
                MSG_INFINIBAND_DP: ("InfiniBand", UnimplementedDevicePath),
                MSG_VENDOR_DP: ("Vendor", UnimplementedDevicePath),
                MSG_MAC_ADDR_DP: ("MAC Address", MacAddrDevicePath),
                MSG_IPV4_DP: ("IPv4", Ipv4DevicePath),
                MSG_IPV6_DP: ("IPv6", UnimplementedDevicePath),
                MSG_UART_DP: ("UART", UnimplementedDevicePath),
                MSG_USB_CLASS_DP: ("USB Class", UnimplementedDevicePath),
                MSG_USB_WWID_DP: ("USB WWID", UnimplementedDevicePath),
                MSG_DEVICE_LOGICAL_UNIT_DP: ("Device Logical Unit", UnimplementedDevicePath),
                MSG_SATA_DP: ("SATA", SataDevicePath),
                MSG_ISCSI_DP: ("iSCSI", UnimplementedDevicePath),
                MSG_VLAN_DP: ("VLAN", UnimplementedDevicePath),
                MSG_FIBRECHANNELEX_DP: ("Fibre Channel Extended", UnimplementedDevicePath),
                MSG_SASEX_DP: ("SAS Extended", UnimplementedDevicePath),
                MSG_NVME_NAMESPACE_DP: ("NVMe Namespace", NvmeOfNamespaceDevicePath),
                MSG_URI_DP: ("URI", UnimplementedDevicePath),
                MSG_UFS_DP: ("UFS", UnimplementedDevicePath),
                MSG_SD_DP: ("SD", UnimplementedDevicePath),
                MSG_EMMC_DP: ("eMMC", UnimplementedDevicePath),
                MSG_BLUEFIELD_DP: ("BlueField", UnimplementedDevicePath),
                MSG_BLUETOOTH_DP: ("Bluetooth", UnimplementedDevicePath),
                MSG_WIFI_DP: ("WiFi", UnimplementedDevicePath),
                MSG_EFI_DP: ("EFI", UnimplementedDevicePath),
            },
        ),
        MEDIA_DEVICE_PATH: defaultdict(
            lambda: ("Unimplemented!", UnimplementedDevicePath),
            {
                MEDIA_HARDDRIVE_DP: ("Hard Drive", HardDriveDevicePath),
                MEDIA_CDROM_DP: ("CD-ROM", UnimplementedDevicePath),
                MEDIA_VENDOR_DP: ("Vendor", UnimplementedDevicePath),
                MEDIA_FILEPATH_DP: ("File Path", FilepathDevicePath),
                MEDIA_PROTOCOL_DP: ("Protocol", UnimplementedDevicePath),
                MEDIA_PIWG_FW_FILE_DP: ("PIWG Firmware File", MediaFwVolFilePathDevicePath),
                MEDIA_PIWG_FW_VOL_DP: ("PIWG Firmware Volume", FwVolPathDevicePath),
                MEDIA_RELATIVE_OFFSET_RANGE_DP: ("Relative Offset Range", MediaRelativeOffsetRangeDevicePath),
            },
        ),
        BIOS_BOOT_SPECIFICATION_DEVICE_PATH: defaultdict(
            lambda: ("Unimplemented!", UnimplementedDevicePath),
            {BBS_BBS_DP: ("BIOS Boot Specification", UnimplementedDevicePath)},
        ),
        END_OF_HARDWARE_DEVICE_PATH: defaultdict(lambda: ("End of Hardware", EndOfHardwareDevicePath), {}),
    },
)


class DevicePathFactory(object):
    """
    A factory class for creating device path objects from binary data.
    """

    def __init__(self):
        pass

    @staticmethod
    def _find_implementation(header: DevicePathHeader):
        """
        Finds the implementation class for a given DevicePathHeader.

        Args:
            header (DevicePathHeader): The header containing the device type and subtype.

        Returns:
            class: The implementation class corresponding to the device type and subtype.
        """

        class_impl = DEVICE_PATH_SUBTYPES[header.dev_type][header.dev_subtype][1]
        return class_impl

    @staticmethod
    def from_binary(binary: bytes) -> List["EfiDevicePathProtocol"]:
        """
        Parses a binary stream into a list of EfiDevicePathProtocol objects.

        Args:
            binary (bytes): The binary data to parse.

        Returns:
            List[EfiDevicePathProtocol]: A list of parsed EfiDevicePathProtocol objects.

        Raises:
            ValueError: If an invalid header length is encountered.
        """

        device_paths = []
        offset = 0

        while offset < len(binary):
            header = EfiDevicePathProtocol.decode(binary[offset:])
            device_path_class = DevicePathFactory._find_implementation(header)
            device_path = device_path_class.from_binary(header)
            device_paths.append(device_path)

            if header.dev_length == 0:
                # dev_length is user controlled after all..
                raise ValueError(f"Invalid Header Length: {header}")

            offset += header.dev_length

        return device_paths
