# @file qemu_command_builder.py
#
# QEMU Command Builder Class allow for easy construction of QEMU command line
# arguments
#
# Copyright (c), Microsoft Corporation
# SPDX-License-Identifier: BSD-2-Clause-Patent
"""QEMU Command Builder for Q35 and SBSA architectures"""

import os
import logging
import datetime
from pathlib import Path
from enum import Enum


class QemuArchitecture(Enum):
    """Supported QEMU architectures"""

    Q35 = "q35"
    SBSA = "sbsa"


class QemuCommandBuilder:
    """Builder class for constructing QEMU command arguments"""

    def __init__(self, executable, architecture=QemuArchitecture.Q35):
        self.executable = executable
        self.architecture = architecture
        self.args = []

        # Common initial arguments
        self.args.extend(["-global", "driver=cfi.pflash01,property=secure,value=on"])
        if self.architecture == QemuArchitecture.Q35:
            self.args.extend(["-debugcon", "stdio"])  # enable debug console
            self.args.extend(
                ["-global", "ICH9-LPC.disable_s3=1"]
            )  # disable S3 sleep state
            self.args.extend(["-global", f"isa-debugcon.iobase=0x402"])  # debug console
            self.args.extend(
                ["-device", "isa-debug-exit,iobase=0xf4,iosize=0x04"]
            )  # debug exit device

    def with_rom_path(self, rom_dir):
        """Set ROM path for QEMU external dependency"""
        if rom_dir:
            self.args.extend(["-L", str(Path(rom_dir))])
        return self

    def with_machine(self, smm_enabled=True, accel=None):
        """Configure machine type with SMM and acceleration"""
        if self.architecture == QemuArchitecture.Q35:
            smm = "on" if smm_enabled else "off"
            machine_config = f"q35,smm={smm}"

            if accel:
                accel_lower = accel.lower()
                if accel_lower in ["kvm", "tcg", "whpx"]:
                    machine_config += f",accel={accel_lower}"

            self.args.extend(["-machine", machine_config])
        elif self.architecture == QemuArchitecture.SBSA:
            self.args.extend(["-machine", "sbsa-ref"])

        return self

    def with_cpu(self, model=None, core_count=None):
        """Configure CPU model and core count"""
        if self.architecture == QemuArchitecture.Q35:
            cpu_model = model or "qemu64"
            cpu_features = f"{cpu_model},rdrand=on,umip=on,smep=on,pdpe1gb=on,popcnt=on,+sse,+sse2,+sse3,+ssse3,+sse4.2,+sse4.1"
            self.args.extend(["-cpu", cpu_features])
        elif self.architecture == QemuArchitecture.SBSA:
            self.args.extend(["-cpu", "max,sve=off,sme=off"])

        if core_count:
            self.args.extend(["-smp", str(core_count)])

        return self

    def with_firmware(self, code_fd, vars_fd=None):
        """Configure firmware (CODE and VARS)"""
        if self.architecture == QemuArchitecture.Q35:
            self.args.extend(
                [
                    "-drive",
                    f"if=pflash,format=raw,unit=0,file={str(code_fd)},readonly=on",
                    "-drive",
                    f"if=pflash,format=raw,unit=1,file={str(vars_fd)}",
                ]
            )
        elif self.architecture == QemuArchitecture.SBSA:
            # SBSA has different firmware layout
            # Unit 0: SECURE_FLASH0.fd (writable)
            # Unit 1: QEMU_EFI.fd (readonly)
            if vars_fd:
                self.args.extend(
                    ["-drive", f"if=pflash,format=raw,unit=0,file={str(vars_fd)}"]
                )
            self.args.extend(
                [
                    "-drive",
                    f"if=pflash,format=raw,unit=1,file={str(code_fd)},readonly=on",
                ]
            )

        return self

    def with_usb_controller(self, include_keyboard=False):
        """Add USB controller with tablet and optionally keyboard"""
        self.args.extend(
            [
                "-device",
                "qemu-xhci,id=usb",
                "-device",
                "usb-tablet,id=input0,bus=usb.0,port=1",
            ]
        )

        if include_keyboard:
            self.args.extend(["-device", "usb-kbd,id=input1,bus=usb.0,port=2"])

        return self

    def with_usb_storage(self, drive_file, drive_id, drive_format="raw"):
        """Add USB storage device"""
        self.args.extend(
            [
                "-drive",
                f"file={drive_file},format={drive_format},media=disk,if=none,id={drive_id}",
                "-device",
                f"usb-storage,bus=usb.0,drive={drive_id}",
            ]
        )
        return self

    def with_memory(self, size_mb):
        """Set memory size in MB"""
        self.args.extend(["-m", str(size_mb)])
        return self

    def with_os_storage(self, path_to_os):
        """Configure OS storage (VHD, QCOW2, or ISO)"""
        if not path_to_os:
            return self

        file_extension = Path(path_to_os).suffix.lower().replace('"', "")

        storage_format = {
            ".vhd": "raw",
            ".qcow2": "qcow2",
            ".iso": "iso",
        }.get(file_extension)

        if storage_format is None:
            raise Exception(f"Unknown OS storage type: {path_to_os}")

        if storage_format == "iso":
            self.args.extend(["-cdrom", path_to_os])
        else:
            if self.architecture == QemuArchitecture.Q35:
                self.args.extend(
                    [
                        "-drive",
                        f"file={path_to_os},format={storage_format},if=none,id=os_nvme",
                        "-device",
                        "nvme,serial=nvme-1,drive=os_nvme",
                    ]
                )
            elif self.architecture == QemuArchitecture.SBSA:
                self.args.extend(
                    [
                        "-drive",
                        f"file={path_to_os},format={storage_format},if=none,id=os_disk",
                        "-device",
                        "ahci,id=ahci",
                        "-device",
                        "ide-hd,drive=os_disk,bus=ahci.0",
                    ]
                )
        return self

    def with_virtual_drive(self, virtual_drive):
        """Mount virtual drive
        Args:
            virtual_drive: Path to virtual drive. Can be either:
                - A file path: Mounts the file as a virtio drive
                - A directory path: Mounts the directory as a FAT filesystem with read/write access
                - None/empty: No virtual drive will be mounted
        """

        if not virtual_drive:
            return self

        if os.path.isfile(virtual_drive):
            self.args.extend(["-drive", f"file={virtual_drive},if=virtio"])
        elif os.path.isdir(virtual_drive):
            self.args.extend(
                ["-drive", f"file=fat:rw:{virtual_drive},format=raw,media=disk"]
            )
        else:
            logging.critical("Virtual Drive Path Invalid")

        return self

    def with_network(self, enable_dfci_ports=False, use_virtio=False):
        """Configure network device with user mode networking
        Args:
            enable_dfci_ports (bool): Enable DFCI port forwarding (ports 8270, 8271).
                When True, forwards TCP ports 8270 and 8271 from host to guest
                for DFCI (Device Firmware Configuration Interface) communication.
            use_virtio (bool): Use virtio network device instead of e1000.
                - True: Uses virtio-net-pci device (better performance, requires virtio drivers)
                - False: Uses e1000 device (broader compatibility, standard Ethernet emulation)
        """
        netdev_config = "user,id=net0"

        if enable_dfci_ports:
            netdev_config += ",hostfwd=tcp::8270-:8270,hostfwd=tcp::8271-:8271"

        self.args.extend(["-netdev", netdev_config])

        if use_virtio:
            self.args.extend(["-device", "virtio-net-pci,netdev=net0"])
        else:
            self.args.extend(["-device", "e1000,netdev=net0"])

        return self

    def with_network_disabled(self):
        """Disable networking"""
        self.args.extend(["-net", "none"])
        return self

    def with_smbios(
        self, code_fd, vendor, version, manufacturer, qemu_version="10.0.0", boot_selection=""
    ):
        """Configure SMBIOS information"""
        creation_time = Path(code_fd).stat().st_mtime
        creation_datetime = datetime.datetime.fromtimestamp(creation_time)
        creation_date = creation_datetime.strftime("%m/%d/%Y")

        if self.architecture == QemuArchitecture.Q35:
            self.args.extend(
                [
                    "-smbios",
                    f"type=0,vendor={vendor},version={version},date={creation_date},uefi=on",
                    "-smbios",
                    f"type=1,manufacturer={manufacturer},product=QEMU Q35,family=QEMU,version={qemu_version},serial=42-42-42-42,uuid=99fb60e2-181c-413a-a3cf-0a5fea8d87b0",
                    "-smbios",
                    f"type=3,manufacturer={manufacturer},serial=40-41-42-43{boot_selection}",
                ]
            )
        elif self.architecture == QemuArchitecture.SBSA:
            self.args.extend(
                [
                    "-smbios",
                    f"type=0,vendor={vendor},version={version},date={creation_date},uefi=on",
                    "-smbios",
                    f"type=1,manufacturer={manufacturer},product=QEMU SBSA,family=QEMU,version={qemu_version},serial=42-42-42-42",
                    "-smbios",
                    f"type=3,manufacturer={manufacturer},serial=42-42-42-42,asset=SBSA,sku=SBSA",
                ]
            )

        return self

    def with_tpm(self, tpm_dev):
        """Configure TPM device"""
        if tpm_dev:
            self.args.extend(
                [
                    "-chardev",
                    f"socket,id=chrtpm,path={tpm_dev}",
                    "-tpmdev",
                    "emulator,id=tpm0,chardev=chrtpm",
                ]
            )

            # Q35 uses tpm-tis, SBSA would use tpm-tis-device (not added here as original doesn't have it)
            if self.architecture == QemuArchitecture.Q35:
                self.args.extend(["-device", "tpm-tis,tpmdev=tpm0"])

        return self

    def with_display(self, headless=False):
        """Configure display output"""
        if headless:
            self.args.extend(["-display", "none"])
        elif self.architecture == QemuArchitecture.Q35:
            self.args.extend(["-vga", "cirrus"])
        # SBSA doesn't set VGA by default
        return self

    def with_gdb_server(self, port):
        """Enable GDB server"""
        if port:
            logging.info(f"Enabling GDB server at port tcp::{port}")
            self.args.extend(["-gdb", f"tcp::{port}"])
        return self

    def with_serial_port(self, port=None, use_stdio=False, log_files=None):
        """Configure serial port for console output"""
        if port:
            self.args.extend(["-serial", f"tcp:127.0.0.1:{port},server,nowait"])
        elif use_stdio:
            self.args.extend(["-serial", "stdio"])
            if log_files:
                for log_file in log_files:
                    self.args.extend(["-serial", f"file:{log_file}"])
        return self

    def with_monitor_port(self, port):
        """Configure monitor port"""
        if port:
            self.args.extend(["-monitor", f"tcp:127.0.0.1:{port},server,nowait"])
        return self

    def build(self):
        """Build and return the complete command"""
        return [self.executable, *self.args]
